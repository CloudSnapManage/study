from pathlib import Path

import pytest

from backend.security import PathSandboxError, safe_resolve


def test_safe_resolve_accepts_descendant(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    assert safe_resolve(root, "nested/file.pdf") == (root / "nested/file.pdf").resolve()


def test_safe_resolve_rejects_parent_traversal(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    with pytest.raises(PathSandboxError):
        safe_resolve(root, "../outside.pdf")


def test_safe_resolve_rejects_symlink_escape(tmp_path: Path):
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "escape").symlink_to(outside, target_is_directory=True)
    with pytest.raises(PathSandboxError):
        safe_resolve(root, "escape/file.pdf")
