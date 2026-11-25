# Cognito Design

## Intent
Build a local-first desktop study workstation for STEM students who need one keyboard-driven place to index PDFs, prioritize exam topics, verify cited source pages, review spaced-repetition cards, run mock exams, and audit derivations. Success means every core workflow remains usable without a network connection, while local or OpenAI-compatible language models enhance rather than gate the product.

## Goals
- One FastAPI process, one SQLite database in WAL mode, and a zero-build vanilla frontend.
- Recursive incremental indexing of `materials/notes` and `materials/past_papers` with exact PDF/page provenance.
- Six complete, data-backed workspaces matching `RULES.md` and `UI_UX.md`.
- Safe filesystem operations and non-destructive Obsidian marker updates.
- Graceful deterministic fallbacks whenever Ollama, a cloud-compatible endpoint, or Obsidian is unavailable.
- Automated backend, API, frontend-policy, and startup verification.

## Non-goals
- Electron packaging, cloud accounts, multi-user synchronization, Docker, a vector database, or a Node build pipeline.
- Fabricated metrics or seed data in production views.
- Writing outside configured materials, runtime data, or Obsidian roots.

## Anti-goals
- Marketing-page layouts, gradients, shadows, glass effects, decorative animation, emojis, or CDN dependencies.
- LLM-dependent navigation or core study features.
- Raw HTML insertion from PDF, user, Markdown, or model content.

## Constraints
`RULES.md` and `UI_UX.md` are binding. The frontend uses exact graphite/amber tokens, 100dvh shell geometry, delegated events, one `AppState`, local vendor assets, DOMPurify sanitation, and KaTeX-safe SSE buffering. Every relevant file operation uses resolved-path containment. Obsidian writes preserve text outside exact uppercase COGNITO markers.

## Approaches considered
1. **Single-process layered FastAPI application (selected).** Small focused backend modules share a connection factory; FastAPI owns APIs, SSE, and static files. It minimizes deployment and meets offline/idle constraints.
2. **Single large backend module.** Faster initial typing but difficult to test, audit, and safely evolve across ingestion, scheduling, model routing, and sync. Rejected.
3. **Separate frontend/backend services with a JS toolchain.** Familiar SPA structure but violates the zero-build, single-process requirement. Rejected.

## Architecture
- `backend/config.py`: resolved project paths and environment-backed settings.
- `backend/security.py`: reusable `safe_resolve` containment primitive.
- `backend/database.py`: schema, WAL pragmas, transaction helpers, FTS5 where available.
- `backend/ingestion.py`: incremental PyMuPDF scanning, text chunking, equations, and on-demand rendering metadata.
- `backend/srs.py`, `backend/obsidian.py`, `backend/llm.py`, and `backend/services.py`: isolated domain logic.
- `backend/main.py`: thin API/SSE/static composition layer with structured errors.
- `frontend/index.html`, `styles.css`, `app.js`: a single semantic shell; each view is a render function driven by `AppState`; delegated actions route through one event layer.
- `frontend/vendor/`: pinned local KaTeX, marked, and DOMPurify distributions.

## Data model
SQLite stores documents/chunks, extracted formulas and diagrams, topics, flashcards and SM-2 state, mock attempts/questions, chat sessions/messages, tool traces, profiles/settings, and token usage. Documents retain canonical paths and SHA-256 hashes. Search uses FTS5/BM25 when available and a LIKE fallback when the SQLite build lacks FTS5.

## API behavior
JSON routes expose health/status, scan/search, sprint/review, radar/mastery, vault, mock exams, solution checks, profiles/settings, Obsidian sync, and exact-page PNG rendering. Chat uses SSE events (`tool_start`, `tool_result`, `token`, `citation`, `done`, `error`). Deterministic retrieval answers and checker audits keep the route useful when no model responds.

## UI design
The visual system is a scientific instrument: exact graphite surfaces, amber active state, steel-blue citations, dense rows, one-pixel structural rules, native sans and monospace metric text. The memorable interaction is evidence verification: clicking a citation opens the exact rendered PDF page alongside the chat. The application never scrolls as a page; only panes scroll.

## Safety and degradation
All dynamic paths pass `safe_resolve`. API exceptions become `{error, code}` JSON. Missing optional integrations produce explicit status plus local fallback output. Obsidian marker replacement is idempotent and never modifies surrounding content.

## Verification
Pytest covers schema/WAL, indexing, traversal rejection, markers, SM-2 math, and routes. A standalone frontend audit detects forbidden visual/runtime tokens and inline handlers. A startup probe launches Uvicorn and fetches `/api/health` and `/`.
