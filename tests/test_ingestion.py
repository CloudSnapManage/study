from pathlib import Path

import fitz
import pytest

from backend.config import Settings
from backend.database import connect_db, init_db
from backend.ingestion import render_pdf_page, scan_materials
from backend.search import search_all
from backend.security import PathSandboxError


def make_pdf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def test_scan_indexes_pdf_and_skips_unchanged(tmp_path: Path):
    settings = Settings(project_root=tmp_path)
    init_db(settings)
    pdf = settings.materials_dir / "notes" / "Physics_II" / "Lecture_02.pdf"
    make_pdf(pdf, "Gauss Law\nE = Q / epsilon\nElectric flux definition")
    first = scan_materials(settings)
    second = scan_materials(settings)
    assert first == {"indexed": 1, "skipped": 0, "errors": []}
    assert second == {"indexed": 0, "skipped": 1, "errors": []}
    with connect_db(settings) as db:
        assert db.execute("SELECT count(*) FROM documents").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM chunks").fetchone()[0] >= 1
        assert db.execute("SELECT count(*) FROM formulas").fetchone()[0] >= 1


def test_search_returns_exact_provenance(tmp_path: Path):
    settings = Settings(project_root=tmp_path)
    init_db(settings)
    pdf = settings.materials_dir / "past_papers" / "Physics_II" / "Past_2024.pdf"
    make_pdf(pdf, "Calculate electric flux using Gauss Law")
    scan_materials(settings)
    result = search_all(settings, "electric flux")
    assert result[0]["filename"] == "Past_2024.pdf"
    assert result[0]["page_number"] == 1
    assert result[0]["doc_type"] == "past_paper"


def test_scan_extracts_embedded_diagram_to_sandboxed_asset(tmp_path: Path):
    settings = Settings(project_root=tmp_path)
    init_db(settings)
    pdf = settings.materials_dir / "notes" / "Physics" / "diagram.pdf"
    pdf.parent.mkdir(parents=True)
    image = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 140, 140), 0)
    image.clear_with(200)
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Circuit diagram")
    page.insert_image(fitz.Rect(72, 100, 212, 240), pixmap=image)
    document.save(pdf)
    document.close()
    scan_materials(settings)
    with connect_db(settings) as db:
        diagram = db.execute("SELECT image_path,width,height FROM diagrams").fetchone()
    assert diagram is not None
    assert Path(diagram["image_path"]).is_relative_to(settings.data_dir / "figures")
    assert Path(diagram["image_path"]).exists()
    assert diagram["width"] >= 120 and diagram["height"] >= 120


def test_render_pdf_page_produces_png_and_rejects_escape(tmp_path: Path):
    settings = Settings(project_root=tmp_path)
    init_db(settings)
    pdf = settings.materials_dir / "notes" / "Physics" / "source.pdf"
    make_pdf(pdf, "Exact cited page")
    scan_materials(settings)
    with connect_db(settings) as db:
        doc_id = db.execute("SELECT id FROM documents").fetchone()[0]
    image = render_pdf_page(settings, doc_id, 1, "cited")
    assert image.startswith(b"\x89PNG")
    with connect_db(settings) as db:
        db.execute("UPDATE documents SET filepath=? WHERE id=?", (str(tmp_path / "outside.pdf"), doc_id))
    with pytest.raises(PathSandboxError):
        render_pdf_page(settings, doc_id, 1)
