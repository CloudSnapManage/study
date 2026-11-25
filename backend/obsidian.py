"""Non-destructive Obsidian synchronization."""
from __future__ import annotations

from .config import Settings
from .database import connect_db
from .security import safe_resolve

START_MARKER = "<!-- COGNITO:SYNC-START -->"
END_MARKER = "<!-- COGNITO:SYNC-END -->"


def replace_sync_block(existing: str, generated: str) -> str:
    block = f"{START_MARKER}\n{generated.rstrip()}\n{END_MARKER}"
    start = existing.find(START_MARKER)
    end = existing.find(END_MARKER)
    if start >= 0 and end >= start:
        return existing[:start] + block + existing[end + len(END_MARKER):]
    separator = "" if not existing or existing.endswith("\n") else "\n"
    return f"{existing}{separator}\n{block}\n"


def _radar_markdown(rows: list) -> str:
    lines = ["# Exam Radar", "", "| Done | Topic | Subject | Notes | Past papers | Probability |", "|---|---|---|---:|---:|---:|"]
    for row in rows:
        done = "x" if row["mastered"] else " "
        lines.append(f"| [{done}] | {row['topic_name']} | {row['subject']} | {row['note_mentions']} | {row['past_paper_mentions']} | {row['probability_score']:.0f}% |")
    return "\n".join(lines)


def sync_radar_moc(settings: Settings) -> dict:
    with connect_db(settings) as db:
        rows = db.execute("SELECT * FROM topics ORDER BY probability_score DESC,topic_name").fetchall()
    if settings.obsidian_vault_path is None:
        return {"status": "unset", "path": None, "topics": len(rows)}
    vault = settings.obsidian_vault_path
    vault.mkdir(parents=True, exist_ok=True)
    target = safe_resolve(vault, "Cognito/00_Exam_Radar_MOC.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = target.read_text(encoding="utf-8") if target.exists() else ""
    target.write_text(replace_sync_block(existing, _radar_markdown(rows)), encoding="utf-8")
    return {"status": "synced", "path": str(target), "topics": len(rows)}


def save_cognito_note(settings: Settings, relative_path: str, generated: str) -> dict:
    if settings.obsidian_vault_path is None:
        return {"status": "unset", "path": None}
    target = safe_resolve(settings.obsidian_vault_path, relative_path)
    if target.suffix.lower() != ".md":
        raise ValueError("Obsidian notes must use .md")
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = target.read_text(encoding="utf-8") if target.exists() else ""
    target.write_text(replace_sync_block(existing, generated), encoding="utf-8")
    return {"status": "synced", "path": str(target)}
