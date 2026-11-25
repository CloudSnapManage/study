from pathlib import Path

from backend.config import Settings
from backend.database import connect_db, init_db
from backend.study import audit_derivation, generate_mock_exam


def test_mock_exam_is_deterministic_and_uses_indexed_material(tmp_path: Path):
    settings = Settings(project_root=tmp_path)
    init_db(settings)
    with connect_db(settings) as db:
        document_id = db.execute("INSERT INTO documents(filename,filepath,file_hash,subject,doc_type,page_count) VALUES('notes.pdf',?,'x','Physics','note',1)", (str(settings.materials_dir / 'notes.pdf'),)).lastrowid
        db.execute("INSERT INTO chunks(document_id,page_number,chunk_index,heading,content,subject,filename) VALUES(?,1,0,'Gauss Law','Explain electric flux through a closed surface.','Physics','notes.pdf')", (document_id,))
    first = generate_mock_exam(settings, "Physics", 2)
    second = generate_mock_exam(settings, "Physics", 2)
    assert first["questions"] == second["questions"]
    assert first["questions"][0]["source_ref"] == "notes.pdf, p. 1"


def test_audit_derivation_reports_sign_change():
    result = audit_derivation("Electric potential", "E = -grad V\nE = +grad V")
    assert result["status"] == "error"
    assert result["first_error_step"] == 2
    assert result["steps"][1]["valid"] is False
