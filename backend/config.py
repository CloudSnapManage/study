"""Runtime paths and environment-backed settings."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Settings:
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[1])
    materials_dir: Path = field(default=None)  # type: ignore[assignment]
    data_dir: Path = field(default=None)  # type: ignore[assignment]
    database_path: Path = field(default=None)  # type: ignore[assignment]
    frontend_dir: Path = field(default=None)  # type: ignore[assignment]
    obsidian_vault_path: Path | None = None
    ollama_base_url: str = "http://127.0.0.1:11434/v1"
    active_model: str = "qwen2.5-coder:7b"
    license_public_key: str | None = None
    checkout_url: str | None = None
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    api_token: str | None = None
    launch_nonce: str | None = None

    def __post_init__(self) -> None:
        self.project_root = Path(os.getenv("COGNITO_PROJECT_ROOT", self.project_root)).resolve()
        self.materials_dir = Path(self.materials_dir or os.getenv("MATERIALS_DIR", self.project_root / "materials")).resolve()
        self.data_dir = Path(self.data_dir or os.getenv("COGNITO_DATA_DIR", self.project_root / "data")).resolve()
        self.database_path = Path(self.database_path or os.getenv("COGNITO_DB_PATH", self.data_dir / "cognito.db")).resolve()
        self.frontend_dir = Path(self.frontend_dir or os.getenv("COGNITO_FRONTEND_DIR", self.project_root / "frontend")).resolve()
        vault = self.obsidian_vault_path or os.getenv("OBSIDIAN_VAULT_PATH")
        self.obsidian_vault_path = Path(vault).expanduser().resolve() if vault else None
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", self.ollama_base_url).rstrip("/")
        self.active_model = os.getenv("COGNITO_MODEL", self.active_model)
        self.license_public_key = os.getenv("COGNITO_LICENSE_PUBLIC_KEY", self.license_public_key or "") or None
        self.checkout_url = os.getenv("COGNITO_CHECKOUT_URL", self.checkout_url or "") or None
        self.rate_limit_requests = int(os.getenv("COGNITO_RATE_LIMIT", self.rate_limit_requests))
        self.rate_limit_window_seconds = int(os.getenv("COGNITO_RATE_WINDOW", self.rate_limit_window_seconds))
        self.api_token = os.getenv("COGNITO_API_TOKEN", self.api_token or "") or None
        self.launch_nonce = os.getenv("COGNITO_LAUNCH_NONCE", self.launch_nonce or "") or None
        if self.rate_limit_requests < 1 or self.rate_limit_window_seconds < 1:
            raise ValueError("Rate limit settings must be positive")

    def ensure_directories(self) -> None:
        self.materials_dir.mkdir(parents=True, exist_ok=True)
        (self.materials_dir / "notes").mkdir(parents=True, exist_ok=True)
        (self.materials_dir / "past_papers").mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.data_dir.chmod(0o700)
        figures = self.data_dir / "figures"
        figures.mkdir(parents=True, exist_ok=True, mode=0o700)
        figures.chmod(0o700)
