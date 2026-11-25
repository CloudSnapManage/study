from pathlib import Path

from backend.config import Settings
from backend.database import connect_db, init_db
from backend.obsidian import END_MARKER, START_MARKER, replace_sync_block, sync_radar_moc


def test_replace_sync_block_preserves_surrounding_text_and_is_idempotent():
    original = f"Personal preface\n\n{START_MARKER}\nold\n{END_MARKER}\n\nPersonal ending\n"
    updated = replace_sync_block(original, "new\ncontent")
    assert updated.startswith("Personal preface")
    assert updated.endswith("Personal ending\n")
    assert replace_sync_block(updated, "new\ncontent") == updated


def test_sync_radar_returns_clean_fallback_when_vault_unset(tmp_path: Path):
    settings = Settings(project_root=tmp_path)
    init_db(settings)
    assert sync_radar_moc(settings) == {"status": "unset", "path": None, "topics": 0}


def test_sync_radar_preserves_existing_user_text(tmp_path: Path):
    vault = tmp_path / "vault"
    settings = Settings(project_root=tmp_path, obsidian_vault_path=vault)
    init_db(settings)
    with connect_db(settings) as db:
        db.execute("INSERT INTO topics(subject,topic_name,probability_score) VALUES('Physics','Flux',80)")
    target = vault / "Cognito" / "00_Exam_Radar_MOC.md"
    target.parent.mkdir(parents=True)
    target.write_text("My notes before\n\nMy notes after\n")
    result = sync_radar_moc(settings)
    content = target.read_text()
    assert result["status"] == "synced"
    assert "My notes before" in content and "My notes after" in content
    assert START_MARKER in content and "Flux" in content
