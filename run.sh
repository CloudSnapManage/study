#!/usr/bin/env sh
set -eu
exec "$(dirname "$0")/.venv/bin/uvicorn" backend.main:app --host 127.0.0.1 --port "${PORT:-8765}"
