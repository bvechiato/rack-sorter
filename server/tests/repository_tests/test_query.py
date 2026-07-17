from model.repository.query import QueryDTO, insert_query, get_query_by_upload_id
import model.repository.query as mod


def test_querydto_from_row():
    row = (7, 'kw', '{"p":1}')
    dto = QueryDTO.from_row(row)
    assert dto.id == 7
    assert dto.search_keyword == 'kw'


def test_get_query_by_upload_id_monkeypatch(monkeypatch):
    class FakeConn:
        def cursor(self):
            return self

        def execute(self, sql, params):
            pass

        def fetchone(self):
            return (3, 'k', '{}')

        def close(self):
            pass

    monkeypatch.setattr(mod, 'sqlite3', type('S', (), {'connect': lambda db: FakeConn()}))
    dto = get_query_by_upload_id(1)
    assert dto.id == 3
