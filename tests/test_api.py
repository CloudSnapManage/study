from pathlib import Path

import fitz
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.main import create_app


def build_client(tmp_path: Path) -> TestClient:
    frontend = tmp_path / "frontend"
    frontend.mkdir()
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
        mock = client.post("/api/mock/generate", json={"subject": "Physics", "count": 5}).json()
        assert mock["fallback"] is True
        audit = client.post("/api/checker/verify", json={"problem": "potential", "derivation": "E = -grad V\nE = +grad V"}).json()
        assert audit["first_error_step"] == 2
        assert client.post("/api/obsidian/sync").json()["status"] == "unset"


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


def test_api_errors_use_error_and_code(tmp_path: Path):
    with build_client(tmp_path) as client:
        response = client.get("/api/pdf/999/page/1")
        assert response.status_code == 404
        assert response.json() == {"error": "Document not found", "code": "not_found"}
        response = client.post("/api/sprint/999/review", json={"rating": 9})
        assert response.status_code == 422
        assert set(response.json()) == {"error", "code"}
