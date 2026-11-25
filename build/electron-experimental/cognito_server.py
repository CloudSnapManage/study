"""PyInstaller entry point for the experimental Electron wrapper."""
import os
import sys
from pathlib import Path


def bundled_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))


root = bundled_root()
os.environ.setdefault("COGNITO_PROJECT_ROOT", str(root))

import uvicorn

from backend.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("PORT", "18765")), log_level="warning")
