"""Consistent SQLite backup and restore helpers."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path


def _checked_database(path: Path) -> None:
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as db:
        result = db.execute("PRAGMA integrity_check").fetchone()
    if not result or result[0] != "ok":
        raise ValueError("SQLite integrity check failed")


def backup_database(source: Path | str, destination: Path | str) -> Path:
    source_path = Path(source).expanduser().resolve()
    destination_path = Path(destination).expanduser().resolve()
    if not source_path.is_file():
        raise FileNotFoundError("Source database not found")
    destination_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with sqlite3.connect(source_path) as source_db, sqlite3.connect(destination_path) as destination_db:
        source_db.backup(destination_db)
    os.chmod(destination_path, 0o600)
    _checked_database(destination_path)
    return destination_path


def restore_database(backup: Path | str, destination: Path | str) -> Path:
    backup_path = Path(backup).expanduser().resolve()
    destination_path = Path(destination).expanduser().resolve()
    if not backup_path.is_file():
        raise FileNotFoundError("Backup database not found")
    _checked_database(backup_path)
    destination_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with sqlite3.connect(backup_path) as backup_db, sqlite3.connect(destination_path) as destination_db:
        backup_db.backup(destination_db)
    os.chmod(destination_path, 0o600)
    _checked_database(destination_path)
    return destination_path
