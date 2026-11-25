"""Filesystem containment helpers."""
from pathlib import Path


class PathSandboxError(ValueError):
    """Raised when a requested path escapes its configured root."""


def safe_resolve(root: Path | str, target: Path | str) -> Path:
    allowed_root = Path(root).expanduser().resolve()
    candidate = Path(target).expanduser()
    if not candidate.is_absolute():
        candidate = allowed_root / candidate
    resolved = candidate.resolve()
    if not resolved.is_relative_to(allowed_root):
        raise PathSandboxError("Path is outside the allowed root")
    return resolved
