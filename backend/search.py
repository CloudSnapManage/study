"""Local full-text retrieval with provenance."""
from __future__ import annotations

import sqlite3

from .config import Settings
from .database import connect_db


def search_all(settings: Settings, query: str, subject: str | None = None, limit: int = 20) -> list[dict]:
    query = query.strip()
    if not query:
        return []
    params: list[object] = []
    subject_sql = ""
    if subject:
        subject_sql = " AND d.subject=?"
        params.append(subject)
    with connect_db(settings) as db:
        try:
            terms = " OR ".join(f'"{word.replace(chr(34), "")}"' for word in query.split())
            rows = db.execute(f"""SELECT c.id,c.document_id,c.page_number,c.heading,c.content,c.subject,c.filename,d.doc_type,
              bm25(chunks_fts) AS rank FROM chunks_fts JOIN chunks c ON c.id=chunks_fts.rowid
              JOIN documents d ON d.id=c.document_id WHERE chunks_fts MATCH ?{subject_sql}
              ORDER BY rank LIMIT ?""", [terms, *params, limit]).fetchall()
        except sqlite3.OperationalError:
            like = f"%{query}%"
            rows = db.execute(f"""SELECT c.id,c.document_id,c.page_number,c.heading,c.content,c.subject,c.filename,d.doc_type,0 AS rank
              FROM chunks c JOIN documents d ON d.id=c.document_id WHERE (c.content LIKE ? OR c.heading LIKE ?){subject_sql}
              ORDER BY c.id DESC LIMIT ?""", [like, like, *params, limit]).fetchall()
    return [dict(row) for row in rows]


def vault_items(settings: Settings, item_type: str | None = None, query: str = "") -> list[dict]:
    clauses: list[str] = []
    params: list[object] = []
    if query:
        clauses.append("(name LIKE ? OR latex LIKE ? OR context LIKE ?)")
        pattern = f"%{query}%"
        params.extend([pattern, pattern, pattern])
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with connect_db(settings) as db:
        formulas = db.execute(f"""SELECT f.id,'formula' AS type,f.name,f.latex,f.context,f.subject,f.page_number,d.filename,d.id AS document_id
          FROM formulas f JOIN documents d ON d.id=f.document_id{where} ORDER BY f.id DESC""", params).fetchall()
        diagrams = []
        if not item_type or item_type in {"all", "diagram"}:
            diagrams = db.execute("""SELECT g.id,'diagram' AS type,g.caption AS name,'' AS latex,g.caption AS context,g.subject,g.page_number,d.filename,d.id AS document_id,g.image_path
              FROM diagrams g JOIN documents d ON d.id=g.document_id ORDER BY g.id DESC""").fetchall()
    result = [dict(row) for row in formulas] + [dict(row) for row in diagrams]
    if item_type and item_type != "all":
        result = [item for item in result if item["type"] == item_type]
    return result
