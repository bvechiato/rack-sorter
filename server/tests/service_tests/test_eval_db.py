import os
from service import eval_db


def test_save_image_writes_file(tmp_path, monkeypatch):
    # Point UPLOADS_PATH to temp dir
    monkeypatch.setattr(eval_db, 'UPLOADS_PATH', str(tmp_path))

    data = b'zzz'
    filename = eval_db.save_image(data)
    path = tmp_path / filename
    assert path.exists()
    assert path.read_bytes() == data


def test_save_clip_analysis_executes(cursor=None):
    # Use a fake cursor capture executed statements
    class FakeCursor:
        def __init__(self):
            self.executed = []

        def execute(self, sql, params):
            self.executed.append((sql.strip(), params))

    fake = FakeCursor()
    tags = {
        "classified_tags": ["t1", "t2"],
        "colour_classified_tags": ["c1"],
        "category_archetype": "arch"
    }
    eval_db.save_clip_analysis(fake, 5, tags)
    # Expect at least three inserts (two classified tags, one colour, one archetype)
    assert len(fake.executed) >= 3
