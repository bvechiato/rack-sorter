import model.repository.feedback as mod
from model.repository.feedback import RerankFeedback, get_feedback_for_upload


def test_rerankfeedback_from_row():
    row = ('http://a', 'MORE')
    rf = RerankFeedback.from_row(row)
    assert rf.item_url == 'http://a'


def test_rerankfeedback_from_row_with_aesthetic():
    row = ('http://a', 'MORE', None, 'formal')
    rf = RerankFeedback.from_row(row)
    assert rf.item_url == 'http://a'
    assert rf.feedback_type == 'MORE'
    assert rf.aesthetic == 'formal'


def test_get_feedback_for_upload_monkeypatch(monkeypatch):
    class FakeConn:
        def __enter__(self):
            return self
        def __exit__(self, *exc):
            return False
        def cursor(self):
            return self

        def execute(self, sql, params):
            pass

        def fetchall(self):
            return [('u1', 'MORE'), ('u2', 'LESS')]

        def close(self):
            pass

    monkeypatch.setattr(mod, 'db_connection', lambda: FakeConn())
    res = get_feedback_for_upload(1)
    assert len(res) == 2
    assert res[0].feedback_type in ('MORE', 'LESS')


def test_delete_last_feedback_deletes_max_id_row(monkeypatch):
    executed = []

    class FakeConn:
        def __enter__(self):
            return self
        def __exit__(self, *exc):
            return False
        def cursor(self):
            return self
        def execute(self, sql, params):
            executed.append((sql, params))
        def fetchone(self):
            return (42,)
        def close(self):
            pass

    monkeypatch.setattr(mod, 'db_connection', lambda: FakeConn())
    assert mod.delete_last_feedback_for_upload(1) is True
    delete_sql, delete_params = executed[-1]
    assert "DELETE FROM rerank_feedback WHERE id" in delete_sql
    assert delete_params == (42,)


def test_delete_last_feedback_noop_when_empty(monkeypatch):
    class FakeConn:
        def __enter__(self):
            return self
        def __exit__(self, *exc):
            return False
        def cursor(self):
            return self
        def execute(self, sql, params):
            pass
        def fetchone(self):
            return None
        def close(self):
            pass

    monkeypatch.setattr(mod, 'db_connection', lambda: FakeConn())
    assert mod.delete_last_feedback_for_upload(1) is False


def test_get_last_feedback_for_upload_returns_most_recent(monkeypatch):
    class FakeConn:
        def __enter__(self):
            return self
        def __exit__(self, *exc):
            return False
        def cursor(self):
            return self
        def execute(self, sql, params):
            pass
        def fetchone(self):
            return ('u2', 'LESS', 'sleeves', None)
        def close(self):
            pass

    monkeypatch.setattr(mod, 'db_connection', lambda: FakeConn())
    fb = mod.get_last_feedback_for_upload(1)
    assert fb.item_url == 'u2'
    assert fb.feedback_type == 'LESS'
    assert fb.concept == 'sleeves'


def test_get_last_feedback_for_upload_none_when_empty(monkeypatch):
    class FakeConn:
        def __enter__(self):
            return self
        def __exit__(self, *exc):
            return False
        def cursor(self):
            return self
        def execute(self, sql, params):
            pass
        def fetchone(self):
            return None
        def close(self):
            pass

    monkeypatch.setattr(mod, 'db_connection', lambda: FakeConn())
    assert mod.get_last_feedback_for_upload(1) is None
