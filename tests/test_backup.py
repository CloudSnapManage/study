import sqlite3
from pathlib import Path

from backend.backup import backup_database, restore_database


def test_backup_and_restore_round_trip(tmp_path: Path):
    source = tmp_path / "cognito.db"
    backup = tmp_path / "backups" / "cognito-backup.db"
    restored = tmp_path / "restored.db"

    with sqlite3.connect(source) as db:
        db.execute("CREATE TABLE sample(value TEXT NOT NULL)")
        db.execute("INSERT INTO sample(value) VALUES(?)", ("verified",))

    backup_database(source, backup)
    restore_database(backup, restored)

    with sqlite3.connect(restored) as db:
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert db.execute("SELECT value FROM sample").fetchone()[0] == "verified"
