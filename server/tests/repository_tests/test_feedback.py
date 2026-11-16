import model.repository.feedback as mod
from model.repository.feedback import RerankFeedback, get_feedback_for_upload


def test_rerankfeedback_from_row():
    row = ('http://a', 'MORE')
    rf = RerankFeedback.from_row(row)
    assert rf.item_url == 'http://a'


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
