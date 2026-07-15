import json
import repository.search_items as mod
from repository.search_items import SearchItem


def test_searchitem_serialization():
    s = SearchItem(title="t", url="u", image_url="i", data={"k": "v"})
    j = s.to_json()
    s2 = SearchItem.from_json(j)
    assert s2.title == "t"
    assert s2.url == "u"
    assert s2.image_url == "i"
    assert s2.data["k"] == "v"


def test_get_items_by_query_id(monkeypatch):
    rows = [("t", "u", "i", json.dumps({"title": "t", "url": "u", "image_url": "i", "foo": "bar"}))]

    class FakeConn:
        def __init__(self, rows):
            self._rows = rows

        def cursor(self):
            return self

        def execute(self, *args, **kwargs):
            pass

        def fetchall(self):
            return self._rows

        def close(self):
            pass

    monkeypatch.setattr(mod, "sqlite3", type("S", (), {"connect": lambda db: FakeConn(rows)}))
    res = mod.get_items_by_query_id(1)
    assert len(res) == 1
    assert isinstance(res[0], SearchItem)
    assert res[0].data.get("foo") == "bar"


def test_insert_search_items_records(monkeypatch):
    recorded = {}

    class FakeConn:
        def __init__(self):
            self._data = None

        def cursor(self):
            return self

        def executemany(self, sql, data):
            recorded['sql'] = sql
            recorded['data'] = data

        def commit(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(mod, "sqlite3", type("S", (), {"connect": lambda db: FakeConn()}))
    items = [SearchItem(title="t", url="u", image_url=None, data={"a": 1}), {"title": "t2", "url": "u2", "image_url": None}]
    mod.insert_search_items(5, items)
    assert 'data' in recorded
    assert len(recorded['data']) == 2
