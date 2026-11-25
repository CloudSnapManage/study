import sqlite3
from pathlib import Path

from backend.config import Settings
from backend.database import connect_db, init_db


def test_init_db_enables_wal_and_creates_core_schema(tmp_path: Path):
    settings = Settings(project_root=tmp_path)
    init_db(settings)
    with connect_db(settings) as db:
        assert db.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        names = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
    assert {"documents", "chunks", "formulas", "diagrams", "topics", "flashcards", "chat_sessions", "chat_messages", "tool_traces", "llm_profiles", "settings", "mock_attempts", "mock_questions", "token_usage"} <= names


def test_connect_db_returns_named_rows(tmp_path: Path):
    settings = Settings(project_root=tmp_path)
    init_db(settings)
    with connect_db(settings) as db:
        row = db.execute("SELECT 7 AS value").fetchone()
    assert isinstance(row, sqlite3.Row)
    assert row["value"] == 7
