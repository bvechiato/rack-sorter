from repository.user_uploads import UserUpload, get_upload_by_id
import repository.user_uploads as mod


def test_userupload_from_row():
    row = (9, 'img.jpg')
    u = UserUpload.from_row(row)
    assert u.id == 9
    assert u.image_path == 'img.jpg'


def test_get_upload_by_id_monkeypatch(monkeypatch):
    class FakeConn:
        def cursor(self):
            return self

        def execute(self, sql, params):
            pass

        def fetchone(self):
            return (11, 'i.jpg')

        def close(self):
            pass

    monkeypatch.setattr(mod, 'sqlite3', type('S', (), {'connect': lambda db: FakeConn()}))
    u = get_upload_by_id(1)
    assert u.id == 11
