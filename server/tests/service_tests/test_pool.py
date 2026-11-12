import pytest

from dtos import QueryDTO, SearchItem
from service import pool


def _item(url: str) -> SearchItem:
    return SearchItem(title=url, url=url, image_url=f"{url}.jpg")


@pytest.fixture(autouse=True)
def clean_cursor():
    pool._page_cursor.clear()
    yield
    pool._page_cursor.clear()


def _stub_query(monkeypatch, params="search_text=blouse"):
    monkeypatch.setattr(
        pool,
        "get_query_by_upload_id",
        lambda upload_id: QueryDTO(id=7, search_keyword="blouse", query_params=params),
    )


def test_fetch_more_merges_only_unseen_items(monkeypatch):
    _stub_query(monkeypatch)
    monkeypatch.setattr(pool, "get_item_urls_for_query", lambda query_id: {"a", "b"})
    scraped = {_item("b"), _item("c"), _item("d")}  # SearchItems hash by identity
    monkeypatch.setattr(pool, "scrape_vinted_pool", lambda params: scraped)
    monkeypatch.setattr(pool, "process_and_rank_pool", lambda items, uid: list(items))

    written = {}

    def fake_insert(query_id, items):
        written["query_id"] = query_id
        written["urls"] = {item.url for item in items}

    monkeypatch.setattr(pool, "insert_search_items", fake_insert)

    count = pool.fetch_more_for_upload(42)

    assert count == 2
    assert written["query_id"] == 7
    assert written["urls"] == {"c", "d"}


def test_fetch_more_advances_the_page(monkeypatch):
    _stub_query(monkeypatch)
    monkeypatch.setattr(pool, "get_item_urls_for_query", lambda query_id: set())
    monkeypatch.setattr(pool, "process_and_rank_pool", lambda items, uid: list(items))
    monkeypatch.setattr(pool, "insert_search_items", lambda query_id, items: None)

    seen = []
    monkeypatch.setattr(
        pool,
        "scrape_vinted_pool",
        lambda params: seen.append(params) or {_item(f"x{len(seen)}")},
    )

    pool.fetch_more_for_upload(42)
    pool.fetch_more_for_upload(42)

    assert seen[0].endswith("&page=2")
    assert seen[1].endswith("&page=3")


def test_fetch_more_stops_at_the_page_cap(monkeypatch):
    _stub_query(monkeypatch)
    monkeypatch.setattr(
        pool, "scrape_vinted_pool", lambda params: pytest.fail("scraper must not be called past the cap")
    )
    pool._page_cursor[42] = pool.MAX_PAGE

    assert pool.fetch_more_for_upload(42) == 0


def test_fetch_more_without_query_params_is_a_logged_noop(monkeypatch):
    _stub_query(monkeypatch, params=None)
    monkeypatch.setattr(
        pool, "scrape_vinted_pool", lambda params: pytest.fail("nothing to scrape without params")
    )

    assert pool.fetch_more_for_upload(42) == 0


def test_fetch_more_duplicate_page_adds_nothing(monkeypatch):
    _stub_query(monkeypatch)
    monkeypatch.setattr(pool, "get_item_urls_for_query", lambda query_id: {"a"})
    monkeypatch.setattr(pool, "scrape_vinted_pool", lambda params: {_item("a")})
    monkeypatch.setattr(
        pool, "insert_search_items", lambda query_id, items: pytest.fail("no new rows to insert")
    )

    assert pool.fetch_more_for_upload(42) == 0
    # The cursor still moves so the next feedback asks for a different page.
    assert pool._page_cursor[42] == 2
