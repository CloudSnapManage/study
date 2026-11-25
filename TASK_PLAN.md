# Cognito Delivery Status

**Date:** 2026-11-25  
**Status:** Complete; canonical web and experimental Electron versions are running for review.

## Requirements and design

- [x] Read and apply `RULES.md` and `UI_UX.md`
- [x] Maintain persistent design, implementation, findings, and progress documents
- [x] Preserve the FastAPI/browser application as the canonical product
- [x] Keep the Electron experiment isolated under `build/electron-experimental/`

## Canonical application

- [x] FastAPI + SQLite WAL backend
- [x] Recursive incremental PDF indexing with SHA-256 deduplication
- [x] Search, formulas, diagrams, flashcards, SM-2, radar, RAG chat, PDF verification, and Obsidian flows
- [x] OpenAI-compatible/Ollama routing with deterministic offline fallbacks
- [x] Six-view vanilla frontend with one `AppState`, delegated events, local dependencies, keyboard support, and sanitized rendering
- [x] Canonical server running at `http://127.0.0.1:8765`

## Monetization

- [x] Cognito Free and Cognito Pro entitlements
- [x] Offline Ed25519 license verification with seven-day expiry grace
- [x] Backend Pro enforcement and upgrade/activation surfaces
- [x] Provider-neutral external checkout configuration

## Security and operations

- [x] Strict filesystem containment and owner-only runtime permissions
- [x] Trusted hosts, restrictive security headers, cross-site mutation checks, request bounds, and rate limiting
- [x] Optional API capability token and Electron per-launch token/nonce
- [x] Provider URL validation against credential embedding and private-network SSRF
- [x] Parameterized database access and sanitized browser rendering
- [x] SQLite online backup/restore with integrity checks
- [x] `.env`, databases, dependencies, and generated build outputs ignored
- [x] Python and npm dependency audits report zero known vulnerabilities

## Experimental Electron wrapper

- [x] Sandboxed BrowserWindow with context isolation and Node integration disabled
- [x] Random loopback port, API token, and authenticated health nonce
- [x] Isolated per-user materials and database paths
- [x] PyInstaller server bundled as an explicit extra resource
- [x] ASAR allowlist includes `main.cjs`, `preload.cjs`, `wrapper-lib.cjs`, and `package.json`
- [x] AppImage and Debian artifacts produced
- [x] Packaged application launched, six workspace entry points exercised, local assets verified, and screenshot inspected
- [x] Experimental application left running for review

## Final verification evidence

- [x] `pytest -q`: 40 passed, 2 third-party deprecation warnings
- [x] Ruff: clean
- [x] mypy: clean across 14 source files
- [x] Frontend policy audit: clean
- [x] JavaScript syntax and Python compilation: clean
- [x] `pip-audit`: no known vulnerabilities
- [x] Electron tests: 3 passed
- [x] `npm audit`: zero vulnerabilities
- [x] Canonical health and static-asset probes: HTTP 200
- [x] Packaged Electron process and bundled backend confirmed running

## Remaining non-blocking release work

- Supply production branding/icon and Linux desktop association metadata.
- Code-sign release installers and configure a real update channel before commercial distribution.
- Keep the private license-signing key outside every application build.
- Consider OS-keyring storage for custom provider credentials before accepting production API keys.
