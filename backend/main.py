"""Cognito FastAPI application and JSON/SSE routes."""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import Settings
from .database import connect_db, init_db
from .ingestion import render_pdf_page, scan_materials
from .llm import stream_chat
from .obsidian import sync_radar_moc
from .search import search_all, vault_items
from .security import PathSandboxError
from .srs import schedule_review
from .study import audit_derivation, generate_mock_exam


class ReviewBody(BaseModel):
    rating: int = Field(ge=1, le=4)


class MasteryBody(BaseModel):
    mastered: bool


class MockBody(BaseModel):
    subject: str
    count: int = Field(default=5, ge=1, le=20)
    source_bias: str = "past_papers_weighted"


class CheckerBody(BaseModel):
    problem: str = ""
    derivation: str


class ChatBody(BaseModel):
    message: str
    mode: str = "agent"


class SettingsBody(BaseModel):
    active_model: str | None = None
    ollama_base_url: str | None = None
    obsidian_vault_path: str | None = None


def error(message: str, code: str, status: int) -> JSONResponse:
    return JSONResponse({"error": message, "code": code}, status_code=status)


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        config.ensure_directories()
        init_db(config)
        application.state.settings = config
        yield

    app = FastAPI(title="Cognito", lifespan=lifespan)
    app.state.settings = config

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError):
        return error(exc.errors()[0].get("msg", "Invalid request"), "validation_error", 422)

    @app.exception_handler(PathSandboxError)
    async def sandbox_handler(_request: Request, exc: PathSandboxError):
        return error(str(exc), "path_outside_root", 403)

    @app.exception_handler(FileNotFoundError)
    async def missing_handler(_request: Request, exc: FileNotFoundError):
        return error(str(exc), "not_found", 404)

    @app.exception_handler(ValueError)
    async def value_handler(_request: Request, exc: ValueError):
        return error(str(exc), "invalid_request", 422)

    @app.get("/api/health")
    def health():
        with connect_db(config) as db:
            chunks = db.execute("SELECT count(*) FROM chunks").fetchone()[0]
            documents = db.execute("SELECT count(*) FROM documents").fetchone()[0]
            tokens = db.execute("SELECT coalesce(sum(prompt_tokens+completion_tokens),0) FROM token_usage").fetchone()[0]
        return {"status": "ok", "sqlite": {"chunks": chunks, "documents": documents}, "obsidian": "connected" if config.obsidian_vault_path else "unset", "llm": {"provider": "Ollama", "model": config.active_model}, "tokens": tokens}

    @app.post("/api/ingest/scan")
    def scan():
        return scan_materials(config)

    @app.get("/api/search")
    def search(q: str = "", subject: str | None = None, limit: int = Query(20, ge=1, le=100)):
        return {"results": search_all(config, q, subject, limit)}

    @app.get("/api/pdf/{document_id}/page/{page_number}")
    def pdf_page(document_id: int, page_number: int, term: str | None = None, zoom: float = Query(2.0, ge=0.5, le=4)):
        return Response(render_pdf_page(config, document_id, page_number, term, zoom), media_type="image/png")

    @app.get("/api/sprint/today")
    def sprint_today():
        with connect_db(config) as db:
            rows = db.execute("SELECT * FROM flashcards WHERE datetime(next_review_at)<=datetime('now') ORDER BY next_review_at,id LIMIT 20").fetchall()
        cards = [dict(row) for row in rows]
        return {"cards": cards, "due": len(cards)}

    @app.post("/api/sprint/{card_id}/review")
    def sprint_review(card_id: int, body: ReviewBody):
        with connect_db(config) as db:
            row = db.execute("SELECT * FROM flashcards WHERE id=?", (card_id,)).fetchone()
            if not row:
                raise FileNotFoundError("Flashcard not found")
            update = schedule_review(row["ease_factor"], row["interval_days"], row["repetitions"], body.rating)
            db.execute("UPDATE flashcards SET ease_factor=?,interval_days=?,repetitions=?,next_review_at=? WHERE id=?", (update["ease_factor"], update["interval_days"], update["repetitions"], update["next_review_at"], card_id))
        return {"id": card_id, **update}

    @app.get("/api/radar")
    def radar():
        with connect_db(config) as db:
            rows = db.execute("SELECT * FROM topics ORDER BY probability_score DESC,topic_name").fetchall()
        return {"topics": [dict(row) for row in rows]}

    @app.patch("/api/radar/{topic_id}")
    def set_mastery(topic_id: int, body: MasteryBody):
        with connect_db(config) as db:
            cursor = db.execute("UPDATE topics SET mastered=? WHERE id=?", (int(body.mastered), topic_id))
            if not cursor.rowcount:
                raise FileNotFoundError("Topic not found")
        return {"id": topic_id, "mastered": body.mastered}

    @app.get("/api/vault")
    def vault(item_type: str | None = None, q: str = ""):
        return {"items": vault_items(config, item_type, q)}

    @app.post("/api/mock/generate")
    def mock_generate(body: MockBody):
        return generate_mock_exam(config, body.subject, body.count, body.source_bias)

    @app.post("/api/checker/verify")
    def checker(body: CheckerBody):
        return audit_derivation(body.problem, body.derivation)

    @app.post("/api/obsidian/sync")
    def obsidian_sync():
        return sync_radar_moc(config)

    @app.get("/api/profiles")
    def profiles():
        with connect_db(config) as db:
            rows = db.execute("SELECT id,name,provider_type,base_url,model_id,tool_mode,role,is_fallback FROM llm_profiles ORDER BY id").fetchall()
        return {"profiles": [dict(row) for row in rows]}

    @app.get("/api/settings")
    def get_settings():
        return {"materials_dir": str(config.materials_dir), "obsidian_vault_path": str(config.obsidian_vault_path) if config.obsidian_vault_path else None, "ollama_base_url": config.ollama_base_url, "active_model": config.active_model}

    @app.post("/api/settings")
    def update_settings(body: SettingsBody):
        if body.active_model is not None:
            config.active_model = body.active_model
        if body.ollama_base_url is not None:
            config.ollama_base_url = body.ollama_base_url.rstrip("/")
        if body.obsidian_vault_path is not None:
            config.obsidian_vault_path = Path(body.obsidian_vault_path).expanduser().resolve() if body.obsidian_vault_path else None
        return get_settings()

    @app.post("/api/chat/stream")
    async def chat(body: ChatBody):
        return StreamingResponse(stream_chat(config, body.message, body.mode), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    if config.frontend_dir.exists():
        vendor = config.frontend_dir / "vendor"
        if vendor.exists():
            app.mount("/vendor", StaticFiles(directory=vendor), name="vendor")
        app.mount("/static", StaticFiles(directory=config.frontend_dir), name="static")

        @app.get("/")
        def index():
            index_path = config.frontend_dir / "index.html"
            if not index_path.exists():
                return error("Frontend is not installed", "frontend_missing", 503)
            return FileResponse(index_path)

    return app


app = create_app()
