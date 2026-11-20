import asyncio
import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config

import config

SERVER_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI = SERVER_DIR / "alembic.ini"
TABLES = {
    "user_uploads",
    "queries",
    "search_items",
    "clip_tags",
    "rerank_feedback",
}


def _alembic_config():
    return Config(str(ALEMBIC_INI))


def _db_tables(db_path):
    with sqlite3.connect(db_path) as conn:
        return {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }


def test_upgrade_from_empty_db_creates_baseline(tmp_path, monkeypatch):
    db = tmp_path / "fresh.db"
    monkeypatch.setattr(config, "DB_PATH", str(db))

    command.upgrade(_alembic_config(), "head")

    assert TABLES <= _db_tables(db)
    assert "alembic_version" in _db_tables(db)


def test_stamp_at_base_then_upgrade_to_head(tmp_path, monkeypatch):
    db = tmp_path / "stamped.db"
    monkeypatch.setattr(config, "DB_PATH", str(db))
    cfg = _alembic_config()

    command.stamp(cfg, "base")
    command.upgrade(cfg, "head")

    assert TABLES <= _db_tables(db)


def test_upgrade_is_idempotent(tmp_path, monkeypatch):
    db = tmp_path / "repeat.db"
    monkeypatch.setattr(config, "DB_PATH", str(db))
    cfg = _alembic_config()

    command.upgrade(cfg, "head")
    command.upgrade(cfg, "head")

    with sqlite3.connect(db) as conn:
        version = conn.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    assert version == "0001"


def test_app_startup_applies_migrations(tmp_path, monkeypatch):
    db = tmp_path / "app.db"
    monkeypatch.setattr(config, "DB_PATH", str(db))

    import main

    async def _enter_lifespan():
        async with main.lifespan(app=None):
            pass

    asyncio.run(_enter_lifespan())

    assert TABLES <= _db_tables(db)
