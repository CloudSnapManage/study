#!/usr/bin/env bash
set -euo pipefail
WRAPPER_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_ROOT="$(cd "$WRAPPER_DIR/../.." && pwd)"
PYTHON="$PROJECT_ROOT/.venv/bin/python"
"$PYTHON" -m pip install 'pyinstaller==6.16.0'
rm -rf "$WRAPPER_DIR/server-build" "$WRAPPER_DIR/server-dist"
cd "$PROJECT_ROOT"
"$PYTHON" -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --name cognito-server \
  --distpath "$WRAPPER_DIR/server-dist" \
  --workpath "$WRAPPER_DIR/server-build" \
  --specpath "$WRAPPER_DIR/server-build" \
  --add-data "$PROJECT_ROOT/frontend:frontend" \
  --collect-all pymupdf \
  --hidden-import uvicorn.logging \
  --hidden-import uvicorn.loops.auto \
  --hidden-import uvicorn.protocols.http.auto \
  --hidden-import uvicorn.protocols.websockets.auto \
  --hidden-import uvicorn.lifespan.on \
  "$WRAPPER_DIR/cognito_server.py"
