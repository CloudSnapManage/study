"""Cognito FastAPI application and JSON/SSE routes."""
from __future__ import annotations

import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .config import Settings
from .database import connect_db, init_db
from .ingestion import render_pdf_page, scan_materials
from .license import LicenseManager
from .llm import stream_chat
from .obsidian import save_cognito_note, sync_radar_moc
from .search import search_all, vault_items
from .security import PathSandboxError, validate_provider_url
from .srs import schedule_review
from .study import audit_derivation, generate_mock_exam, grade_mock_exam


class ReviewBody(BaseModel):
    rating: int = Field(ge=1, le=4)


class MasteryBody(BaseModel):
    mastered: bool


class MockBody(BaseModel):
    subject: str
    count: int = Field(default=5, ge=1, le=20)
    source_bias: str = "past_papers_weighted"


class CheckerBody(BaseModel):
    problem: str = Field(default="", max_length=20_000)
    derivation: str = Field(min_length=1, max_length=50_000)


class ChatBody(BaseModel):
    message: str = Field(min_length=1, max_length=50_000)
    mode: str = Field(default="agent", pattern="^(agent|strict|tutor)$")


class SettingsBody(BaseModel):
    active_model: str | None = None
    model: str | None = None
    ollama_base_url: str | None = None
    base_url: str | None = None
    obsidian_vault_path: str | None = None
    materials_dir: str | None = None
    provider: str | None = None
    api_key: str | None = None
    theme: str | None = None


class MockGradeBody(BaseModel):
    questions: list[dict] = []
    answers: dict = {}


class QuestionsBody(BaseModel):
    questions: list[dict] = []


class CheckerFlashcardBody(BaseModel):
    step: int = 0
    audit: dict = {}


class ProfileTestBody(BaseModel):
    base_url: str = "http://127.0.0.1:11434/v1"
    api_key: str | None = None


class ThreadBody(BaseModel):
    messages: list[dict] = []


class LicenseBody(BaseModel):
    token: str = Field(min_length=32, max_length=16_384)


class ProRequiredError(PermissionError):
    pass


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
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["127.0.0.1", "localhost", "testserver"],
    )
    request_times: dict[str, deque[float]] = defaultdict(deque)
    licenses = LicenseManager(config)

    @app.middleware("http")
    async def harden_http(request: Request, call_next):
        if request.url.path.startswith("/api/"):
            presented_token = request.headers.get("x-cognito-token") or request.cookies.get("cognito_session")
            if config.api_token and presented_token != config.api_token:
                response = error("API token is required", "api_token_required", 401)
            elif request.method not in {"GET", "HEAD", "OPTIONS"} and (
                request.headers.get("sec-fetch-site") == "cross-site"
                or (
                    request.headers.get("origin")
                    and request.headers["origin"] not in {
                        "http://127.0.0.1:8765",
                        "http://localhost:8765",
                        f"http://127.0.0.1:{request.url.port}",
                        "http://testserver",
                    }
                )
            ):
                response = error("Cross-site requests are not allowed", "cross_site_request", 403)
            else:
                now = time.monotonic()
                client = request.client.host if request.client else "local"
                history = request_times[client]
                cutoff = now - config.rate_limit_window_seconds
                while history and history[0] <= cutoff:
                    history.popleft()
                if len(history) >= config.rate_limit_requests:
                    retry_after = max(1, int(history[0] + config.rate_limit_window_seconds - now) + 1)
                    response = error("Too many requests", "rate_limited", 429)
                    response.headers["Retry-After"] = str(retry_after)
                else:
                    history.append(now)
                    response = await call_next(request)
        else:
            response = await call_next(request)

        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; "
            "object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        return response

    def require_pro():
        status = licenses.status()
        if status["tier"] != "pro":
            raise ProRequiredError("This workflow requires Cognito Pro")
        return status

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

    @app.exception_handler(ProRequiredError)
    async def pro_handler(_request: Request, exc: ProRequiredError):
        return error(str(exc), "pro_required", 402)

    @app.get("/api/health")
    def health():
        with connect_db(config) as db:
            chunks = db.execute("SELECT count(*) FROM chunks").fetchone()[0]
            documents = db.execute("SELECT count(*) FROM documents").fetchone()[0]
            tokens = db.execute("SELECT coalesce(sum(prompt_tokens+completion_tokens),0) FROM token_usage").fetchone()[0]
        return {"status": "ok", "chunks": chunks, "chunk_count": chunks, "sqlite": {"chunks": chunks, "documents": documents}, "obsidian": "Connected" if config.obsidian_vault_path else "Unset", "llm": {"provider": "Ollama", "model": config.active_model, "profile": f"Ollama: {config.active_model}"}, "tokens": tokens, "subjects": [], "launch_nonce": config.launch_nonce}

    @app.get("/api/license/status")
    def license_status():
        return licenses.status()

    @app.post("/api/license/activate")
    def license_activate(body: LicenseBody):
        return licenses.activate(body.token)

    @app.post("/api/license/deactivate")
    def license_deactivate():
        return licenses.deactivate()

    @app.post("/api/ingest/scan")
    def scan():
        return scan_materials(config)

    @app.get("/api/search")
    def search(q: str = Query("", max_length=500), subject: str | None = None, limit: int = Query(20, ge=1, le=100)):
        return {"results": search_all(config, q, subject, limit)}

    @app.get("/api/pdf/{document_id}/meta")
    def pdf_meta(document_id: int):
        with connect_db(config) as db:
            row = db.execute("SELECT id,filename,page_count FROM documents WHERE id=?", (document_id,)).fetchone()
        if not row:
            raise FileNotFoundError("Document not found")
        return dict(row)

    @app.get("/api/pdf/{document_id}/page/{page_number}")
    def pdf_page(document_id: int, page_number: int, term: str | None = None, zoom: float = Query(2.0, ge=0.5, le=4)):
        return Response(render_pdf_page(config, document_id, page_number, term, zoom), media_type="image/png")

    @app.get("/api/diagram/{diagram_id}")
    def diagram(diagram_id: int):
        from .security import safe_resolve
        with connect_db(config) as db:
            row = db.execute("SELECT image_path FROM diagrams WHERE id=?", (diagram_id,)).fetchone()
        if not row:
            raise FileNotFoundError("Diagram not found")
        path = safe_resolve(config.data_dir / "figures", row["image_path"])
        if not path.exists():
            raise FileNotFoundError("Diagram asset not found")
        return FileResponse(path)

    @app.get("/api/sprint/today")
    def sprint_today(subject: str | None = None):
        with connect_db(config) as db:
            if subject:
                rows = db.execute("SELECT * FROM flashcards WHERE datetime(next_review_at)<=datetime('now') AND subject=? ORDER BY next_review_at,id LIMIT 20", (subject,)).fetchall()
            else:
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
    def radar(subject: str | None = None):
        with connect_db(config) as db:
            if subject:
                rows = db.execute("SELECT * FROM topics WHERE subject=? ORDER BY probability_score DESC,topic_name", (subject,)).fetchall()
            else:
                rows = db.execute("SELECT * FROM topics ORDER BY probability_score DESC,topic_name").fetchall()
        return {"topics": [dict(row) for row in rows]}

    @app.patch("/api/radar/{topic_id}")
    @app.post("/api/radar/{topic_id}/mastery")
    def set_mastery(topic_id: int, body: MasteryBody):
        with connect_db(config) as db:
            cursor = db.execute("UPDATE topics SET mastered=? WHERE id=?", (int(body.mastered), topic_id))
            if not cursor.rowcount:
                raise FileNotFoundError("Topic not found")
        return {"id": topic_id, "mastered": body.mastered}

    @app.get("/api/vault")
    def vault(item_type: str | None = None, q: str = "", subject: str | None = None):
        items = vault_items(config, item_type, q)
        if subject:
            items = [item for item in items if item.get("subject") == subject]
        return {"items": items}

    @app.post("/api/vault/{formula_id}/flashcard")
    def vault_flashcard(formula_id: int, _license: dict = Depends(require_pro)):  # noqa: B008 -- FastAPI dependency declaration
        with connect_db(config) as db:
            row = db.execute("SELECT f.*,d.filename FROM formulas f JOIN documents d ON d.id=f.document_id WHERE f.id=?", (formula_id,)).fetchone()
            if not row:
                raise FileNotFoundError("Formula not found")
            card_id = db.execute("INSERT INTO flashcards(subject,topic,question,answer,latex_hint,source_ref) VALUES(?,?,?,?,?,?)", (row["subject"], row["name"], f"State and explain {row['name']}.", row["context"] or row["latex"], row["latex"], f"{row['filename']}, p. {row['page_number']}" )).lastrowid
        return {"status": "created", "id": card_id}

    @app.post("/api/mock/generate")
    def mock_generate(body: MockBody, _license: dict = Depends(require_pro)):  # noqa: B008 -- FastAPI dependency declaration
        return generate_mock_exam(config, body.subject, body.count, body.source_bias)

    @app.post("/api/mock/grade")
    def mock_grade(body: MockGradeBody, _license: dict = Depends(require_pro)):  # noqa: B008 -- FastAPI dependency declaration
        return grade_mock_exam(body.questions, body.answers)

    @app.post("/api/mock/missed-to-sprint")
    def mock_missed_to_sprint(body: QuestionsBody, _license: dict = Depends(require_pro)):  # noqa: B008 -- FastAPI dependency declaration
        created = 0
        with connect_db(config) as db:
            for question in body.questions:
                if float(question.get("score") or 0) >= float(question.get("marks") or 5):
                    continue
                prompt = str(question.get("prompt") or "Review missed concept")
                answer = str(question.get("solution") or question.get("model_solution") or "Review the indexed source.")
                db.execute("INSERT INTO flashcards(subject,topic,question,answer,source_ref) VALUES(?,?,?,?,?)", (str(question.get("subject") or "General"), prompt[:80], prompt, answer, str(question.get("source_ref") or "Mock Exam")))
                created += 1
        return {"status": "created", "cards": created}

    @app.post("/api/checker/verify")
    def checker(body: CheckerBody, _license: dict = Depends(require_pro)):  # noqa: B008 -- FastAPI dependency declaration
        return audit_derivation(body.problem, body.derivation)

    @app.post("/api/checker/flashcard")
    def checker_flashcard(body: CheckerFlashcardBody, _license: dict = Depends(require_pro)):  # noqa: B008 -- FastAPI dependency declaration
        steps = body.audit.get("steps", [])
        step = steps[body.step] if 0 <= body.step < len(steps) else {}
        with connect_db(config) as db:
            card_id = db.execute("INSERT INTO flashcards(subject,topic,question,answer,source_ref) VALUES(?,?,?,?,?)", ("General", "Derivation error", "Correct this derivation error.", str(step.get("note") or "Review the failed derivation step."), "Solution Checker")).lastrowid
        return {"status": "created", "id": card_id}

    @app.post("/api/obsidian/sync")
    def obsidian_sync(_license: dict = Depends(require_pro)):  # noqa: B008 -- FastAPI dependency declaration
        return sync_radar_moc(config)

    @app.post("/api/obsidian/thread")
    def obsidian_thread(body: ThreadBody, _license: dict = Depends(require_pro)):  # noqa: B008 -- FastAPI dependency declaration
        generated = "# Study Thread\n\n" + "\n\n".join(f"**{message.get('role', 'message').title()}**\n\n{message.get('content', '')}" for message in body.messages)
        return save_cognito_note(config, "Cognito/Threads/Latest.cognito.md", generated)

    @app.get("/api/profiles")
    def profiles():
        with connect_db(config) as db:
            rows = db.execute("SELECT id,name,provider_type,base_url,model_id,tool_mode,role,is_fallback FROM llm_profiles ORDER BY id").fetchall()
        return {"profiles": [dict(row) for row in rows]}

    @app.post("/api/profiles/test")
    async def profile_test(body: ProfileTestBody):
        import httpx
        base_url = validate_provider_url(body.base_url)
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                response = await client.get(base_url.removesuffix("/v1") + "/api/tags")
                response.raise_for_status()
            return {"status": "connected", "message": "Connection available"}
        except httpx.HTTPError:
            return {"status": "unavailable", "message": "Endpoint unavailable; local fallback remains active"}

    @app.get("/api/settings")
    def get_settings():
        with connect_db(config) as db:
            saved = {row["key"]: row["value"] for row in db.execute("SELECT key,value FROM settings WHERE key IN ('active_model','ollama_base_url','theme')").fetchall()}
        return {"materials_dir": str(config.materials_dir), "obsidian_vault_path": str(config.obsidian_vault_path) if config.obsidian_vault_path else None, "ollama_base_url": saved.get("ollama_base_url", config.ollama_base_url), "active_model": saved.get("active_model", config.active_model), "theme": saved.get("theme", "dark")}

    @app.post("/api/settings")
    def update_settings(body: SettingsBody):
        model = body.active_model if body.active_model is not None else body.model
        base_url = body.ollama_base_url if body.ollama_base_url is not None else body.base_url
        if model is not None:
            config.active_model = model
        if base_url is not None:
            config.ollama_base_url = validate_provider_url(base_url)
        if body.obsidian_vault_path is not None:
            config.obsidian_vault_path = Path(body.obsidian_vault_path).expanduser().resolve() if body.obsidian_vault_path else None
        with connect_db(config) as db:
            for key, value in (("active_model", config.active_model), ("ollama_base_url", config.ollama_base_url), ("theme", body.theme)):
                if value is not None:
                    db.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
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
            response = FileResponse(index_path)
            if config.api_token:
                response.set_cookie(
                    "cognito_session",
                    config.api_token,
                    httponly=True,
                    samesite="strict",
                    secure=False,
                    path="/",
                )
            return response

    return app


app = create_app()
