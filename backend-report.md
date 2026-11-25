# Backend Tasks 1–4 Report

## Status
Complete.

## Files created
- Runtime: `requirements.txt`, `.env.example`, `run.sh`, `pytest.ini`
- Foundation: `backend/__init__.py`, `backend/config.py`, `backend/security.py`, `backend/database.py`
- Index/search: `backend/ingestion.py`, `backend/search.py`
- Study domains: `backend/srs.py`, `backend/obsidian.py`, `backend/study.py`
- LLM/tools/API: `backend/llm.py`, `backend/tools.py`, `backend/main.py`
- Tests: `tests/test_database.py`, `tests/test_security.py`, `tests/test_ingestion.py`, `tests/test_srs.py`, `tests/test_obsidian.py`, `tests/test_study.py`, `tests/test_api.py`

## TDD evidence
- Foundation RED: collection failed because `backend` modules did not exist. GREEN: 5 passed.
- Ingestion RED: collection failed because `backend.ingestion` did not exist. GREEN with foundation: 8 passed.
- Study domains RED: collection failed because `backend.srs`, `backend.obsidian`, and `backend.study` did not exist. GREEN: 10 passed.
- API RED: collection failed because `backend.main` did not exist. GREEN: 4 passed.

## Full verification
Command: `.venv/bin/pytest -q`
Result: `25 passed, 2 warnings in 0.38s`.

Warnings are dependency deprecations only: the legacy `fitz` alias imported by the test fixture and Starlette's TestClient notice for its current httpx integration.

## Behavior delivered
- SQLite WAL, foreign keys, full schema, optional FTS5 triggers, named rows.
- Resolved-path containment rejecting parent and symlink traversal.
- Recursive incremental PDF ingestion with SHA-256 deduplication, page chunks, equation/topic extraction, exact provenance, local search, highlighted high-DPI PNG rendering.
- SM-2 ratings 1–4, deterministic mock generation and derivation audit.
- Idempotent uppercase COGNITO marker replacement preserving user text and unset-vault fallback.
- Health, scan, search, PDF, sprint, radar, vault, mock, checker, profiles/settings, Obsidian, and SSE chat routes with structured errors.
- OpenAI-compatible/Ollama streaming attempt followed by deterministic local retrieval fallback.

## Limitations
- Formula extraction is intentionally heuristic and diagram rows are schema-ready but embedded-image extraction is not yet implemented.
- Deterministic derivation checking catches explicit sign/undefined-operation errors; full symbolic equivalence depends on a configured LLM.
- Provider profile CRUD currently exposes list plus runtime settings; persistence of arbitrary new profiles is not exposed by the frontend contract yet.
