# Cognito

Cognito is a local-first study workstation for indexed course PDFs, spaced-repetition review, exam-priority analysis, source-grounded chat, formula retrieval, mock exams, and derivation checking.

## Runtime

- One local FastAPI process
- SQLite in WAL mode
- PyMuPDF PDF indexing and page rendering
- Vanilla HTML, CSS, and JavaScript
- Local KaTeX, marked, DOMPurify, and KaTeX font files
- Ollama by default, with configurable OpenAI-compatible endpoints

Core indexing, search, sprint scheduling, exam radar, mock generation, and deterministic solution audits continue to work when no model is available. Obsidian features return structured status when no vault is configured.

## Folder layout

```text
materials/
  notes/<Subject>/*.pdf
  past_papers/<Subject>/*.pdf
frontend/
backend/
tests/
cognito.db
```

Place PDFs under the subject folders, start Cognito, then use **Scan Materials**.

## Install

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

All browser runtime dependencies are already stored under `frontend/vendor/`; Wi-Fi is not required to render Markdown, sanitized HTML, or KaTeX.

## Launch

```bash
./run.sh
```

Open `http://127.0.0.1:8765`.

To launch directly:

```bash
.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8765
```

## Configuration

The Settings drawer configures the materials directory, optional Obsidian vault path, provider, model, endpoint, and theme. Environment variables may also be set before launch:

```bash
export MATERIALS_DIR="$PWD/materials"
export OBSIDIAN_VAULT_PATH="$HOME/Documents/MyVault"
export COGNITO_DB_PATH="$PWD/cognito.db"
```

For local Ollama, the default OpenAI-compatible endpoint is `http://127.0.0.1:11434/v1`. Plain HTTP provider URLs are accepted only on loopback; remote providers must use HTTPS.

## Free and Pro

Cognito Free includes local PDF indexing, search, Daily Sprint, Exam Radar, the Formula & Diagram Vault, local retrieval chat, and exact-page PDF verification. Cognito Pro unlocks mock exams, Solution Checker, Obsidian sync/export, agent tools, formula flashcards, and custom providers.

Pro activation uses an offline Ed25519-signed token. Set `COGNITO_LICENSE_PUBLIC_KEY` to the base64url-encoded raw public key and `COGNITO_CHECKOUT_URL` to your external HTTPS checkout page. Never bundle the private signing key. Licenses receive a seven-day offline grace period after expiry.

## Keyboard controls

| Context | Shortcut | Action |
|---|---|---|
| Global | `Ctrl+K` / `Command+K` | Open command palette |
| Global | `Esc` | Close palette, drawer, or PDF inspector |
| Daily Sprint | `Space` | Reveal answer |
| Daily Sprint | `1`–`4` | Grade recall |
| Chat | `Enter` | Send |
| Chat | `Shift+Enter` | New line |
| Mock Exam | `F` | Flag current question |
| Solution Checker | `Ctrl+Enter` | Audit derivation |
| Vault | `/` | Focus filter |

## Backup and restore

Use the SQLite online-backup helpers while Cognito is stopped or from an administrative Python shell:

```python
from backend.backup import backup_database, restore_database
backup_database("data/cognito.db", "backups/cognito.db")
restore_database("backups/cognito.db", "data/restored.db")
```

Both operations run `PRAGMA integrity_check` and write owner-only database files.

## Experimental Electron wrapper

The optional wrapper is isolated under `build/electron-experimental/` and does not change the canonical browser app. It uses a sandboxed BrowserWindow, a random loopback port, per-launch API capability and health nonce, separate user data, and an explicitly allowlisted package payload.

```bash
npm --prefix build/electron-experimental install --ignore-scripts
npm --prefix build/electron-experimental run build:linux
```

Installer outputs are written to `build/electron-experimental/dist/`. The wrapper is experimental; the FastAPI/browser application remains canonical.

## Verification

```bash
.venv/bin/pytest -q
.venv/bin/python scripts/audit_frontend.py
node --check frontend/app.js
.venv/bin/ruff check backend tests build/electron-experimental/cognito_server.py
.venv/bin/mypy --ignore-missing-imports backend
.venv/bin/pip-audit -r requirements.txt
npm --prefix build/electron-experimental test
npm --prefix build/electron-experimental audit
```

The test suite covers SQLite initialization, indexing, strict path containment, Obsidian marker preservation, SM-2 scheduling, API routes, and frontend policy constraints. The audit rejects banned colors, gradients, shadows, backdrop filters, emoji code points, inline event handlers, and external runtime assets.

## Data safety

- Every dynamic PDF, material, and Obsidian path is resolved and checked against its configured root.
- Obsidian updates only replace text inside exact `COGNITO:SYNC-START` and `COGNITO:SYNC-END` markers.
- API failures use structured JSON with `error` and `code` fields.
- Trusted hosts, strict browser response headers, cross-site mutation rejection, request bounds, and per-client rate limits protect the loopback API.
- Optional `COGNITO_API_TOKEN` capability enforcement is used automatically by the Electron wrapper.
- Runtime data directories are owner-only (`0700`) and SQLite files are owner-only (`0600`).
- Indexed materials and chat history remain in the local SQLite database.
