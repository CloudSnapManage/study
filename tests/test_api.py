from pathlib import Path

import fitz
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.main import create_app


def build_client(tmp_path: Path) -> TestClient:
    frontend = tmp_path / "frontend"
    frontend.mkdir(exist_ok=True)
    (frontend / "index.html").write_text("<!doctype html><title>Cognito</title>")
    settings = Settings(project_root=tmp_path, frontend_dir=frontend)
    return TestClient(create_app(settings))


def test_health_and_empty_routes_are_structured(tmp_path: Path):
    with build_client(tmp_path) as client:
        health = client.get("/api/health").json()
        assert health["status"] == "ok"
        assert health["sqlite"]["chunks"] == 0
        assert client.get("/api/search", params={"q": "flux"}).json() == {"results": []}
        assert client.get("/api/sprint/today").json() == {"cards": [], "due": 0}
        assert client.get("/api/radar").json() == {"topics": []}
        assert client.get("/api/vault").json() == {"items": []}
        assert client.get("/").status_code == 200


def test_scan_search_pdf_and_all_study_routes(tmp_path: Path):
    with build_client(tmp_path) as client:
        settings = client.app.state.settings
        pdf = settings.materials_dir / "notes" / "Physics" / "lecture.pdf"
        pdf.parent.mkdir(parents=True)
        document = fitz.open()
        page = document.new_page()
        page.insert_text((72, 72), "Gauss Law\nE = Q / epsilon\nElectric flux")
        document.save(pdf)
        document.close()
        assert client.post("/api/ingest/scan").json()["indexed"] == 1
        result = client.get("/api/search", params={"q": "Electric"}).json()["results"][0]
        assert result["filename"] == "lecture.pdf"
        assert client.get(f"/api/pdf/{result['document_id']}/page/1").headers["content-type"] == "image/png"
        assert "topics" in client.get("/api/radar").json()
        assert "items" in client.get("/api/vault").json()
        mock = client.post("/api/mock/generate", json={"subject": "Physics", "count": 5})
        assert mock.status_code == 402 and mock.json()["code"] == "pro_required"
        audit = client.post("/api/checker/verify", json={"problem": "potential", "derivation": "E = -grad V\nE = +grad V"})
        assert audit.status_code == 402 and audit.json()["code"] == "pro_required"
        obsidian = client.post("/api/obsidian/sync")
        assert obsidian.status_code == 402 and obsidian.json()["code"] == "pro_required"


def test_sprint_review_mastery_settings_and_chat_sse(tmp_path: Path):
    with build_client(tmp_path) as client:
        settings = client.app.state.settings
        from backend.database import connect_db
        with connect_db(settings) as db:
            card = db.execute("INSERT INTO flashcards(subject,topic,question,answer) VALUES('Physics','Flux','Define flux','Surface integral')").lastrowid
            topic = db.execute("INSERT INTO topics(subject,topic_name) VALUES('Physics','Flux')").lastrowid
        assert client.get("/api/sprint/today").json()["due"] == 1
        review = client.post(f"/api/sprint/{card}/review", json={"rating": 3}).json()
        assert review["interval_days"] == 1
        assert client.patch(f"/api/radar/{topic}", json={"mastered": True}).json()["mastered"] is True
        assert client.get("/api/settings").json()["active_model"]
        assert client.post("/api/settings", json={"active_model": "local-model"}).json()["active_model"] == "local-model"
        response = client.post("/api/chat/stream", json={"message": "What is flux?", "mode": "strict"})
        assert response.headers["content-type"].startswith("text/event-stream")
        assert "event: tool_start" in response.text
        assert "event: done" in response.text


def test_frontend_action_routes_and_static_assets(tmp_path: Path):
    with build_client(tmp_path) as client:
        settings = client.app.state.settings
        (settings.frontend_dir / "styles.css").write_text("body{}")
        (settings.frontend_dir / "app.js").write_text("const ready=true")
        from backend.database import connect_db
        with connect_db(settings) as db:
            formula = db.execute(
                "INSERT INTO documents(filename,filepath,file_hash,subject,doc_type,page_count) "
                "VALUES('n.pdf',?, 'hash','Physics','note',1)",
                (str(settings.materials_dir / 'notes' / 'n.pdf'),),
            ).lastrowid
            formula_id = db.execute(
                "INSERT INTO formulas(document_id,page_number,subject,name,latex) VALUES(?,?,?,?,?)",
                (formula, 1, 'Physics', 'Flux', 'Phi=EA'),
            ).lastrowid
        assert client.get('/static/styles.css').status_code == 200
        assert client.get('/static/app.js').status_code == 200
        assert client.post(f'/api/vault/{formula_id}/flashcard').status_code == 402
        assert client.post('/api/mock/generate', json={'subject': '', 'count': 5}).status_code == 402
        assert client.post('/api/mock/grade', json={'questions': [], 'answers': {}}).status_code == 402
        assert client.post('/api/mock/missed-to-sprint', json={'questions': []}).status_code == 402
        assert client.post('/api/checker/flashcard', json={'step': 0, 'audit': {'steps': [{'note': 'Sign error'}]}}).status_code == 402
        assert client.post('/api/profiles/test', json={'base_url': 'http://127.0.0.1:1'}).status_code == 200
        assert client.post('/api/obsidian/thread', json={'messages': [{'role': 'user', 'content': 'Flux'}]}).status_code == 402


def test_pdf_metadata_diagram_serving_and_settings_persistence(tmp_path: Path):
    with build_client(tmp_path) as client:
        settings = client.app.state.settings
        pdf = settings.materials_dir / 'notes' / 'Physics' / 'source.pdf'
        pdf.parent.mkdir(parents=True)
        document = fitz.open()
        document.new_page()
        document.new_page()
        document.save(pdf)
        document.close()
        figure = settings.data_dir / 'figures' / 'figure.png'
        figure.write_bytes(b'\x89PNG\r\n\x1a\nfigure')
        from backend.database import connect_db
        with connect_db(settings) as db:
            document_id = db.execute(
                "INSERT INTO documents(filename,filepath,file_hash,subject,doc_type,page_count) VALUES(?,?,?,?,?,?)",
                ('source.pdf', str(pdf), 'hash', 'Physics', 'note', 2),
            ).lastrowid
            diagram_id = db.execute(
                "INSERT INTO diagrams(document_id,page_number,subject,image_path,caption,width,height) VALUES(?,?,?,?,?,?,?)",
                (document_id, 1, 'Physics', str(figure), 'Figure', 140, 140),
            ).lastrowid
        meta = client.get(f'/api/pdf/{document_id}/meta').json()
        assert meta == {'id': document_id, 'filename': 'source.pdf', 'page_count': 2}
        assert client.get(f'/api/diagram/{diagram_id}').content.startswith(b'\x89PNG')
        saved = client.post('/api/settings', json={'model': 'saved-model', 'theme': 'light'}).json()
        assert saved['active_model'] == 'saved-model'
        assert saved['theme'] == 'light'
    with build_client(tmp_path) as second:
        loaded = second.get('/api/settings').json()
        assert loaded['active_model'] == 'saved-model'
        assert loaded['theme'] == 'light'


def test_api_errors_use_error_and_code(tmp_path: Path):
    with build_client(tmp_path) as client:
        response = client.get("/api/pdf/999/page/1")
        assert response.status_code == 404
        assert response.json() == {"error": "Document not found", "code": "not_found"}
        response = client.post("/api/sprint/999/review", json={"rating": 9})
        assert response.status_code == 422
        assert set(response.json()) == {"error", "code"}
