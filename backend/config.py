"""Runtime paths and environment-backed settings."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Settings:
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[1])
    materials_dir: Path | None = None
    data_dir: Path | None = None
    database_path: Path | None = None
    frontend_dir: Path | None = None
    obsidian_vault_path: Path | None = None
    ollama_base_url: str = "http://127.0.0.1:11434/v1"
    active_model: str = "qwen2.5-coder:7b"

    def __post_init__(self) -> None:
        self.project_root = Path(self.project_root).resolve()
        self.materials_dir = Path(self.materials_dir or os.getenv("MATERIALS_DIR", self.project_root / "materials")).resolve()
        self.data_dir = Path(self.data_dir or self.project_root / "data").resolve()
        self.database_path = Path(self.database_path or self.data_dir / "cognito.db").resolve()
        self.frontend_dir = Path(self.frontend_dir or self.project_root / "frontend").resolve()
        vault = self.obsidian_vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
        self.obsidian_vault_path = Path(vault).expanduser().resolve() if vault else None
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", self.ollama_base_url).rstrip("/")
        self.active_model = os.getenv("COGNITO_MODEL", self.active_model)

    def ensure_directories(self) -> None:
        self.materials_dir.mkdir(parents=True, exist_ok=True)
        (self.materials_dir / "notes").mkdir(parents=True, exist_ok=True)
        (self.materials_dir / "past_papers").mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "figures").mkdir(parents=True, exist_ok=True)
