import sqlite3
from pathlib import Path

import numpy as np
import pytest
from alembic import command
from alembic.config import Config

import config
from model.repository import constants as repo_constants
from model.repository.user_uploads import insert_user_upload
from service import clip_vectors, eval_db, rank
from service import repository as upload_repository

SERVER_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI = SERVER_DIR / "alembic.ini"
TAGS = {
    "classified_tags": ["t1"],
    "colour_classified_tags": ["red"],
    "category_archetype": "tops",
}
DINO = [1.0, 0.0]
CLIP = [0.0] * 512
CLIP[0] = 1.0


@pytest.fixture(autouse=True)
def clear_anchor_cache():
    clip_vectors._anchor_cache.clear()
    yield
    clip_vectors._anchor_cache.clear()


def _fresh_db(tmp_path, monkeypatch):
    db = tmp_path / "app.db"
    monkeypatch.setattr(config, "DB_PATH", str(db))
    monkeypatch.setattr(repo_constants, "DB", str(db))
    monkeypatch.setattr(eval_db, "DB", str(db))
    command.upgrade(Config(str(ALEMBIC_INI)), "head")
    return db


def test_upload_without_flag_stores_vectors_and_no_file(tmp_path, monkeypatch):
    db = _fresh_db(tmp_path, monkeypatch)
    uploads = tmp_path / "uploads"
    monkeypatch.setattr(eval_db, "UPLOADS_PATH", str(uploads))
    monkeypatch.setattr(eval_db, "SAVE_UPLOAD_IMAGES", False)

    upload_id = eval_db.save_user_upload(b"image-bytes", TAGS, DINO, CLIP)

    assert not uploads.exists() or list(uploads.iterdir()) == []
    with sqlite3.connect(db) as conn:
        row = conn.execute(
            "SELECT image_path, embedding, clip_embedding FROM user_uploads WHERE id = ?",
            (upload_id,),
        ).fetchone()
    assert row[0] is None
    assert np.frombuffer(row[1], dtype=np.float32).tolist() == DINO
    assert np.frombuffer(row[2], dtype=np.float32).tolist() == CLIP


def test_upload_with_flag_writes_debug_file(tmp_path, monkeypatch):
    db = _fresh_db(tmp_path, monkeypatch)
    uploads = tmp_path / "uploads"
    monkeypatch.setattr(eval_db, "UPLOADS_PATH", str(uploads))
    monkeypatch.setattr(eval_db, "SAVE_UPLOAD_IMAGES", True)

    upload_id = eval_db.save_user_upload(b"image-bytes", TAGS, DINO, CLIP)

    with sqlite3.connect(db) as conn:
        path = conn.execute("SELECT image_path FROM user_uploads WHERE id = ?", (upload_id,)).fetchone()[0]
    assert path is not None
    assert (uploads / path).read_bytes() == b"image-bytes"


def test_anchor_clip_embedding_comes_from_db_without_flag(tmp_path, monkeypatch):
    _fresh_db(tmp_path, monkeypatch)
    monkeypatch.setattr(clip_vectors, "SAVE_UPLOAD_IMAGES", False)
    monkeypatch.setattr(
        upload_repository,
        "get_upload_bytes_by_id",
        lambda _: pytest.fail("file fallback must not run when the flag is off"),
    )
    upload_id = insert_user_upload(None, DINO, CLIP)

    vector = clip_vectors.get_anchor_clip_embedding(upload_id)

    assert vector is not None
    assert np.allclose(vector, CLIP)


def test_anchor_dino_array_comes_from_db_without_flag(tmp_path, monkeypatch):
    _fresh_db(tmp_path, monkeypatch)
    monkeypatch.setattr(rank, "SAVE_UPLOAD_IMAGES", False)
    monkeypatch.setattr(
        rank,
        "get_upload_bytes_by_id",
        lambda _: pytest.fail("file fallback must not run when the flag is off"),
    )
    upload_id = insert_user_upload(None, DINO, CLIP)

    array = rank._anchor_array(upload_id)

    assert np.allclose(array, np.asarray(DINO, dtype=float).reshape(1, -1))
