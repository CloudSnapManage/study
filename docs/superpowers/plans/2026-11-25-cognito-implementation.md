# Cognito Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify the complete Cognito local-first desktop study workstation.

**Architecture:** A layered FastAPI application owns SQLite, filesystem integration, JSON/SSE APIs, and static serving. A zero-build vanilla frontend renders six workspaces from one AppState object and uses only local vendor dependencies.

**Tech Stack:** Python 3, FastAPI, Uvicorn, sqlite3/FTS5, PyMuPDF, httpx, pytest, HTML5, CSS3, ES6+, KaTeX, marked, DOMPurify.

**Spec:** `docs/superpowers/specs/2026-11-25-cognito-design.md`, with `RULES.md` and `UI_UX.md` as binding source specifications.

## Global Constraints
- One local FastAPI process and one SQLite database in WAL mode; no Node, Docker, Redis, or external vector database.
- Pure vanilla HTML/CSS/JS; zero inline handlers and zero runtime CDNs.
- Exact color tokens and 100dvh/44px/26px shell geometry from `UI_UX.md`.
- No gradients, shadows, backdrop filters, decorative emojis, or radii beyond specified maxima.
- Every dynamic filesystem operation validates `target.resolve().is_relative_to(root.resolve())`.
- Obsidian writes preserve content outside `<!-- COGNITO:SYNC-START -->` and `<!-- COGNITO:SYNC-END -->`.
- Core workflows return useful JSON without Ollama, API keys, or Obsidian.

## Review Focus
- Symlink and `..` traversal must be rejected by path utilities and PDF/Obsidian routes.
- Empty databases must produce actionable empty states, never fabricated rows or metrics.
- Malformed model streams must terminate with structured SSE errors without breaking subsequent requests.
- Re-scanning unchanged PDFs must not duplicate documents, chunks, formulas, or topics.
- Keyboard actions must not fire while a user is typing in an input or textarea.

---

### Task 1: Runtime foundation, schema, and safety
**Files:** Create `requirements.txt`, `.env.example`, `run.sh`, `backend/__init__.py`, `backend/config.py`, `backend/security.py`, `backend/database.py`; test `tests/test_database.py`, `tests/test_security.py`.
**Interfaces:** Produce `Settings`, `safe_resolve(root, target)`, `connect_db()`, and `init_db()`.
- [ ] Write failing WAL/schema and path-containment tests.
- [ ] Run focused tests and confirm missing-module failures.
- [ ] Implement settings, safe path resolution, connection pragmas, and full schema.
- [ ] Run focused tests and confirm pass.

### Task 2: Indexing, retrieval, and page rendering
**Files:** Create `backend/ingestion.py`, `backend/search.py`; test `tests/test_ingestion.py`.
**Interfaces:** Consume database/security; produce `scan_materials()`, `search_all()`, and `render_pdf_page()`.
- [ ] Write failing tests for incremental PDF indexing, equation extraction, search provenance, and traversal.
- [ ] Confirm RED.
- [ ] Implement recursive scan, SHA-256 replacement, chunk/formula/topic extraction, and PNG rendering.
- [ ] Confirm focused and database tests GREEN.

### Task 3: Study domains and Obsidian bridge
**Files:** Create `backend/srs.py`, `backend/obsidian.py`, `backend/study.py`; test `tests/test_srs.py`, `tests/test_obsidian.py`, `tests/test_study.py`.
**Interfaces:** Produce `schedule_review()`, `replace_sync_block()`, `sync_radar_moc()`, mock generation, and derivation audit fallbacks.
- [ ] Write failing tests for ratings 1–4, idempotent marker replacement, surrounding-text preservation, unset-vault fallback, and deterministic study output.
- [ ] Confirm RED.
- [ ] Implement domain functions.
- [ ] Confirm focused tests GREEN.

### Task 4: LLM routing, tools, and API composition
**Files:** Create `backend/llm.py`, `backend/tools.py`, `backend/main.py`; test `tests/test_api.py`.
**Interfaces:** Consume all prior services; expose the `/api/*` JSON and SSE contract and static frontend.
- [ ] Write failing route tests for health, scan, search, sprint, radar, vault, mock, checker, settings, Obsidian, PDF pages, and chat fallback SSE.
- [ ] Confirm RED.
- [ ] Implement thin routes, structured errors, local retrieval tools, OpenAI-compatible/Ollama routing, and static mounts.
- [ ] Confirm all backend tests GREEN.

### Task 5: Offline vendor assets and application shell
**Files:** Create `frontend/vendor/**`, `frontend/index.html`, `frontend/styles.css`, `frontend/app.js`.
**Interfaces:** Consume API/SSE contract; produce one keyboard-first AppState-driven SPA.
- [ ] Vendor pinned KaTeX, marked, and DOMPurify distributions locally.
- [ ] Implement exact shell, nav, telemetry, command palette, settings drawer, and reusable render/sanitization/math helpers.
- [ ] Implement Daily Sprint, Exam Radar, Chat/PDF verifier, Vault, Mock Exam, and Solution Checker views.
- [ ] Implement SSE delimiter buffering, citations, delegated events, and all specified shortcuts.

### Task 6: Policy audit, startup verification, and delivery
**Files:** Create `scripts/audit_frontend.py`, `tests/test_frontend_policy.py`, `README.md`, `TASK_PLAN.md`; update planning logs.
**Interfaces:** Verify the assembled application.
- [ ] Write and run frontend policy checks for banned styles, colors, emojis, external URLs, inline handlers, AppState, and local vendor links.
- [ ] Run the complete pytest suite.
- [ ] Start Uvicorn briefly and fetch health/static resources.
- [ ] Record exact results and launch instructions in README and TASK_PLAN.md.
