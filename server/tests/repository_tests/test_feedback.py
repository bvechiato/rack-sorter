from model.repository.feedback import get_feedback_for_upload, RerankFeedback
import model.repository.feedback as mod


def test_rerankfeedback_from_row():
    row = ('http://a', 'MORE')
    rf = RerankFeedback.from_row(row)
    assert rf.item_url == 'http://a'


def test_get_feedback_for_upload_monkeypatch(monkeypatch):
    class FakeConn:
        def cursor(self):
            return self

        def execute(self, sql, params):
            pass

        def fetchall(self):
            return [('u1', 'MORE'), ('u2', 'LESS')]

        def close(self):
            pass

    monkeypatch.setattr(mod, 'sqlite3', type('S', (), {'connect': lambda db: FakeConn()}))
    res = get_feedback_for_upload(1)
    assert len(res) == 2
    assert res[0].feedback_type in ('MORE', 'LESS')
