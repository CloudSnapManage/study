"""Incremental PDF ingestion and page rendering."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pymupdf

from .config import Settings
from .database import connect_db
from .security import safe_resolve

EQUATION = re.compile(r"(?m)^\s*([^\n]{0,100}(?:=|∫|∑|∂|∇|\\frac|\\int|\\sum)[^\n]{1,160})\s*$")


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _chunks(text: str, size: int = 1400) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs and text.strip():
        paragraphs = [text.strip()]
    result: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 2 > size:
            result.append(current)
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}".strip()
    if current:
        result.append(current)
    return result


def _topic_name(text: str) -> str | None:
    for line in text.splitlines():
        value = line.strip()
        if 3 <= len(value) <= 80 and any(char.isalpha() for char in value):
            return value
    return None


def scan_materials(settings: Settings | None = None) -> dict:
    settings = settings or Settings()
    settings.ensure_directories()
    indexed = skipped = 0
    errors: list[dict] = []
    for doc_type, folder in (("note", "notes"), ("past_paper", "past_papers")):
        root = safe_resolve(settings.materials_dir, folder)
        for source in sorted(root.rglob("*.pdf")):
            try:
                source = safe_resolve(settings.materials_dir, source)
                file_hash = _hash(source)
                relative = source.relative_to(root)
                subject = relative.parts[0] if len(relative.parts) > 1 else "Unsorted"
                with connect_db(settings) as db:
                    existing = db.execute("SELECT id,file_hash FROM documents WHERE filepath=?", (str(source),)).fetchone()
                    if existing and existing["file_hash"] == file_hash:
                        skipped += 1
                        continue
                    if existing:
                        document_id = existing["id"]
                        db.execute("DELETE FROM chunks WHERE document_id=?", (document_id,))
                        db.execute("DELETE FROM formulas WHERE document_id=?", (document_id,))
                        db.execute("DELETE FROM diagrams WHERE document_id=?", (document_id,))
                    document = pymupdf.open(source)
                    if existing:
                        db.execute("UPDATE documents SET filename=?,file_hash=?,subject=?,doc_type=?,page_count=?,ingested_at=CURRENT_TIMESTAMP WHERE id=?", (source.name, file_hash, subject, doc_type, document.page_count, document_id))
                    else:
                        cursor = db.execute("INSERT INTO documents(filename,filepath,file_hash,subject,doc_type,page_count) VALUES(?,?,?,?,?,?)", (source.name, str(source), file_hash, subject, doc_type, document.page_count))
                        document_id = cursor.lastrowid
                    for page_index in range(document.page_count):
                        page = document.load_page(page_index)
                        text = page.get_text("text").strip()
                        for chunk_index, content in enumerate(_chunks(text)):
                            db.execute("INSERT INTO chunks(document_id,page_number,chunk_index,heading,content,subject,filename) VALUES(?,?,?,?,?,?,?)", (document_id, page_index + 1, chunk_index, _topic_name(content) or "", content, subject, source.name))
                        for formula_index, match in enumerate(EQUATION.finditer(text), 1):
                            latex = match.group(1).strip()
                            db.execute("INSERT INTO formulas(document_id,page_number,subject,name,latex,context) VALUES(?,?,?,?,?,?)", (document_id, page_index + 1, subject, f"Equation {formula_index}", latex, text[:500]))
                        for image_index, image in enumerate(page.get_images(full=True)):
                            xref = image[0]
                            pixmap = pymupdf.Pixmap(document, xref)
                            width, height = pixmap.width, pixmap.height
                            aspect = max(width / max(height, 1), height / max(width, 1))
                            if width < 120 or height < 120 or aspect > 6:
                                continue
                            output = safe_resolve(settings.data_dir / "figures", f"{file_hash[:16]}_p{page_index + 1}_{image_index}.png")
                            pixmap.save(output)
                            caption = next((line.strip() for line in text.splitlines() if re.search(r"\b(?:fig(?:ure)?|diagram|circuit)\b", line, re.IGNORECASE)), "")
                            db.execute("INSERT INTO diagrams(document_id,page_number,subject,image_path,caption,width,height) VALUES(?,?,?,?,?,?,?)", (document_id, page_index + 1, subject, str(output), caption, width, height))
                        topic = _topic_name(text)
                        if topic:
                            note_inc, paper_inc = (1, 0) if doc_type == "note" else (0, 1)
                            db.execute("""INSERT INTO topics(subject,topic_name,source_ref,note_mentions,past_paper_mentions,probability_score)
                              VALUES(?,?,?,?,?,?) ON CONFLICT(subject,topic_name) DO UPDATE SET
                              source_ref=excluded.source_ref,
                              note_mentions=topics.note_mentions+excluded.note_mentions,
                              past_paper_mentions=topics.past_paper_mentions+excluded.past_paper_mentions,
                              probability_score=min(100, (topics.note_mentions+excluded.note_mentions)*10 + (topics.past_paper_mentions+excluded.past_paper_mentions)*25)
                            """, (subject, topic, f"{source.name}, p. {page_index + 1}", note_inc, paper_inc, min(100, note_inc * 10 + paper_inc * 25)))
                    document.close()
                indexed += 1
            except Exception as exc:  # noqa: BLE001 -- isolate malformed/unreadable PDFs per file
                errors.append({"file": str(source), "error": str(exc)})
    return {"indexed": indexed, "skipped": skipped, "errors": errors}


def render_pdf_page(settings: Settings, document_id: int, page_number: int, term: str | None = None, zoom: float = 2.0) -> bytes:
    with connect_db(settings) as db:
        row = db.execute("SELECT filepath,page_count FROM documents WHERE id=?", (document_id,)).fetchone()
    if not row:
        raise FileNotFoundError("Document not found")
    source = safe_resolve(settings.materials_dir, row["filepath"])
    if page_number < 1 or page_number > row["page_count"]:
        raise ValueError("Page number is out of range")
    document = pymupdf.open(source)
    try:
        page = document[page_number - 1]
        if term:
            for rectangle in page.search_for(term):
                annotation = page.add_highlight_annot(rectangle)
                annotation.update()
        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
        return pixmap.tobytes("png")
    finally:
        document.close()
