"""Append the next catalogue page to an existing search pool.

Feedback is more useful when it can promote items the user has not seen yet: every
`/rerank` pulls one more Vinted page and merges it into the upload's pool before
scoring. The scrape is deliberately fail-soft at the call site — losing the feedback
would be worse than skipping a page.
"""

import threading
from typing import Dict

from model.repository.query import get_query_by_upload_id
from model.repository.search_items import get_item_urls_for_query, insert_search_items
from service.rank import process_and_rank_pool
from service.scraper import scrape_vinted_pool

# Page 1 arrives with `/fetch_initial`; feedback walks 2, 3, … until the cap.
MAX_PAGE = 8

# In-process cursor per upload. A restart replays a page, which the URL merge makes
# harmless (it simply yields zero new rows), so no extra schema is needed.
_page_cursor: Dict[int, int] = {}
_locks: Dict[int, threading.Lock] = {}
_locks_guard = threading.Lock()


def _lock_for(upload_id: int) -> threading.Lock:
    with _locks_guard:
        return _locks.setdefault(upload_id, threading.Lock())


def reset_page_cursor(upload_id: int) -> None:
    """Restart paging at page 2 for a fresh search on the same upload."""
    _page_cursor.pop(upload_id, None)


def fetch_more_for_upload(upload_id: int) -> int:
    """Fetch and persist one more catalogue page. Returns the number of new items."""
    with _lock_for(upload_id):
        query = get_query_by_upload_id(upload_id)
        if not query.query_params:
            print(f"[WARN] Fetch-more skipped for upload {upload_id}: no stored query params")
            return 0

        page = _page_cursor.get(upload_id, 1) + 1
        if page > MAX_PAGE:
            print(f"[INFO] Fetch-more exhausted for upload {upload_id} at page cap {MAX_PAGE}")
            return 0

        params = f"{query.query_params}&page={page}"
        scraped = scrape_vinted_pool(params)
        known = get_item_urls_for_query(query.id)
        fresh = {item for item in scraped if item.url not in known}
        print(
            f"[INFO] Fetch-more page {page} for upload {upload_id}: "
            f"{len(scraped)} scraped, {len(fresh)} unseen"
        )

        if not fresh:
            _page_cursor[upload_id] = page
            return 0

        processed = process_and_rank_pool(fresh, upload_id)
        insert_search_items(query.id, processed)
        _page_cursor[upload_id] = page
        print(f"[SUCCESS] Fetch-more appended {len(processed)} items to query {query.id}")
        return len(processed)
