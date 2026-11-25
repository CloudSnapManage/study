"""SQLite storage with WAL mode and optional FTS5."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from .config import Settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
 id INTEGER PRIMARY KEY, filename TEXT NOT NULL, filepath TEXT UNIQUE NOT NULL,
 file_hash TEXT NOT NULL, subject TEXT NOT NULL, doc_type TEXT NOT NULL,
 page_count INTEGER NOT NULL DEFAULT 0, ingested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS chunks (
 id INTEGER PRIMARY KEY, document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
 page_number INTEGER NOT NULL, chunk_index INTEGER NOT NULL, heading TEXT NOT NULL DEFAULT '',
 content TEXT NOT NULL, subject TEXT NOT NULL, filename TEXT NOT NULL,
 UNIQUE(document_id, page_number, chunk_index)
);
CREATE TABLE IF NOT EXISTS formulas (
 id INTEGER PRIMARY KEY, document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
 page_number INTEGER NOT NULL, subject TEXT NOT NULL, name TEXT NOT NULL,
 latex TEXT NOT NULL, context TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS diagrams (
 id INTEGER PRIMARY KEY, document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
 page_number INTEGER NOT NULL, subject TEXT NOT NULL, image_path TEXT NOT NULL,
 caption TEXT NOT NULL DEFAULT '', width INTEGER NOT NULL DEFAULT 0, height INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS topics (
 id INTEGER PRIMARY KEY, subject TEXT NOT NULL, topic_name TEXT NOT NULL,
 source_ref TEXT NOT NULL DEFAULT '', note_mentions INTEGER NOT NULL DEFAULT 0,
 past_paper_mentions INTEGER NOT NULL DEFAULT 0, probability_score REAL NOT NULL DEFAULT 0,
 estimated_weightage TEXT NOT NULL DEFAULT '', mastered INTEGER NOT NULL DEFAULT 0,
 UNIQUE(subject, topic_name)
);
CREATE TABLE IF NOT EXISTS flashcards (
 id INTEGER PRIMARY KEY, subject TEXT NOT NULL, topic TEXT NOT NULL, question TEXT NOT NULL,
 answer TEXT NOT NULL, latex_hint TEXT NOT NULL DEFAULT '', source_ref TEXT NOT NULL DEFAULT '',
 ease_factor REAL NOT NULL DEFAULT 2.5, interval_days INTEGER NOT NULL DEFAULT 0,
 repetitions INTEGER NOT NULL DEFAULT 0, next_review_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS llm_profiles (
 id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, provider_type TEXT NOT NULL,
 base_url TEXT NOT NULL, api_key TEXT NOT NULL DEFAULT '', model_id TEXT NOT NULL,
 tool_mode TEXT NOT NULL DEFAULT 'native', role TEXT NOT NULL DEFAULT 'chat', is_fallback INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS chat_sessions (id INTEGER PRIMARY KEY, title TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS chat_messages (id INTEGER PRIMARY KEY, session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE, role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS tool_traces (id INTEGER PRIMARY KEY, session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE, tool_name TEXT NOT NULL, arguments_json TEXT NOT NULL, result_json TEXT NOT NULL, duration_ms INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS mock_attempts (id INTEGER PRIMARY KEY, subject TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active', started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, submitted_at TEXT);
CREATE TABLE IF NOT EXISTS mock_questions (id INTEGER PRIMARY KEY, attempt_id INTEGER REFERENCES mock_attempts(id) ON DELETE CASCADE, position INTEGER NOT NULL, prompt TEXT NOT NULL, model_solution TEXT NOT NULL DEFAULT '', marks INTEGER NOT NULL DEFAULT 5, response TEXT NOT NULL DEFAULT '', flagged INTEGER NOT NULL DEFAULT 0, score REAL);
CREATE TABLE IF NOT EXISTS token_usage (id INTEGER PRIMARY KEY, profile_id INTEGER REFERENCES llm_profiles(id), prompt_tokens INTEGER NOT NULL DEFAULT 0, completion_tokens INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
"""


def _configure(db: sqlite3.Connection) -> sqlite3.Connection:
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("PRAGMA foreign_keys=ON")
    return db


@contextmanager
def connect_db(settings: Settings | None = None) -> Iterator[sqlite3.Connection]:
    settings = settings or Settings()
    settings.ensure_directories()
    db = _configure(sqlite3.connect(settings.database_path, timeout=10))
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db(settings: Settings | None = None) -> None:
    with connect_db(settings) as db:
        db.executescript(SCHEMA)
        try:
            db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(content, heading, subject, filename, content='chunks', content_rowid='id', tokenize='porter unicode61')")
            db.executescript("""
            CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
              INSERT INTO chunks_fts(rowid, content, heading, subject, filename) VALUES (new.id,new.content,new.heading,new.subject,new.filename);
            END;
            CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
              INSERT INTO chunks_fts(chunks_fts,rowid,content,heading,subject,filename) VALUES('delete',old.id,old.content,old.heading,old.subject,old.filename);
            END;
            CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
              INSERT INTO chunks_fts(chunks_fts,rowid,content,heading,subject,filename) VALUES('delete',old.id,old.content,old.heading,old.subject,old.filename);
              INSERT INTO chunks_fts(rowid,content,heading,subject,filename) VALUES(new.id,new.content,new.heading,new.subject,new.filename);
            END;
            """)
        except sqlite3.OperationalError:
            pass
        db.execute("INSERT OR IGNORE INTO llm_profiles(name,provider_type,base_url,api_key,model_id,tool_mode,role,is_fallback) VALUES(?,?,?,?,?,?,?,?)", ("Ollama local", "ollama", "http://127.0.0.1:11434/v1", "ollama", "qwen2.5-coder:7b", "native", "chat", 1))
