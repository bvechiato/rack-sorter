# Defect: rerank replays the oldest search for an upload

- **Status:** Fixed (minimal) — `ORDER BY id DESC`, resolved-query logging, and tests landed; follow-ups 1–3 remain open as design decisions.
- **Severity:** High — wrong data, no error surfaced
- **Reported:** 2026-11-11
- **Component:** `server/model/repository/query.py`, consumed by `server/service/repository.py`
- **Related:** [`docs/design/trait-aspect-feedback.md`](../design/trait-aspect-feedback.md) §11

---

## Summary

`get_query_by_upload_id` selects a query with `fetchone()` and **no `ORDER BY`**. Because
`insert_query` appends a new row on every `/fetch_initial`, any upload that is searched more than once
has multiple `queries` rows, and SQLite returns the *first* one (lowest `rowid`). `/rerank` therefore
replays the pool of the **oldest** search, not the one the user is looking at.

## Evidence from the tracked database

The committed `server/search_eval.db` already contains multi-query uploads — 39 `queries` rows across
31 uploads, i.e. **7 uploads are affected**:

```
upload_id | queries | first | last
4         | 3       | 4     | 9
26        | 2       | 32    | 33
24        | 2       | 29    | 30
13, 3, 2, 1 | 2    | ...   | ...
```

For upload `4`:

```
id | search_keyword
4  | ruched+waist
5  | ruched+waist
9  | ruched
```

The current query is:

```sql
SELECT id, search_keyword, query_params FROM queries WHERE upload_id = ?;
-- returns id=4 ("ruched+waist"), the oldest
```

All three queries have 96 items, so the rerank operates on a full pool from the wrong keyword. With
different filter sets the pools diverge further (and can differ in size), so the user sees results
reranked against listings they may no longer be able to see.

## Reproduction

1. `POST /analyze` → `upload_id`.
2. `POST /fetch_initial` with keyword `A` → `queries.id = 10`.
3. `POST /fetch_initial` with keyword `B` → `queries.id = 11`.
4. `POST /rerank` with `upload_id`, any item and `feedback_type = "MORE"`.
5. Observe `[INFO] Running dual-engine rerank pipeline on N items` where `N` and the returned URLs
   correspond to query 10, not 11.

SQL check without touching the API:

```bash
sqlite3 server/search_eval.db \
  "SELECT id, search_keyword FROM queries WHERE upload_id = 4;"
# first row is always the one the code uses
```

## Root cause

- `insert_query` (`query.py:5-13`) always `INSERT`s; there is no unique constraint and no "current"
  pointer.
- `get_query_by_upload_id` (`query.py:15-26`) uses `fetchone()` without `ORDER BY`. SQLite makes no
  ordering guarantee here; in practice it walks the table in `rowid` order and returns the oldest row.
- `service/repository.py::get_results_by_upload_id` and `main.py:101` consume that row directly.

There is no log line identifying which `query_id` was used, so the bug is invisible in normal operation.

## Impact

- `/rerank` reorders the wrong pool; the client then replaces `products` with that stale pool, so the
  grid silently changes search.
- Feedback is stored against `upload_id`, not `query_id`, so trait/generic feedback given while looking
  at query 11 is replayed against query 10 — and against every future search of the same upload.
- Any evaluation built on `search_eval.db` compares feedback against the wrong query.
- Trait-aspect work (design doc) cannot be evaluated until this is fixed, since the "base pool" is
  ambiguous.

## Fix (applied)

### Recommended (minimal, no API change)

```python
cursor.execute(
    """
    SELECT id, search_keyword, query_params
    FROM queries
    WHERE upload_id = ?
    ORDER BY id DESC
    LIMIT 1
    """,
    (upload_id,),
)
```

Order by `id`, not `timestamp`: `CURRENT_TIMESTAMP` has one-second resolution, so two searches within
the same second tie and would fall back to unspecified order. `id` is monotonic per insert.

Add an assertion/log in `get_results_by_upload_id`:

```python
print(f"[INFO] Resolving upload {upload_id} -> query {query_dto.id}")
```

### Follow-ups (not required for the fix)

1. **Explicit current-query pointer.** Add `current_query_id` to `user_uploads`, updated in the same
   transaction as `insert_query`. Makes the choice explicit and race-free, and is the right model if
   sessions ever resume.
2. **Scope feedback to a query.** `rerank_feedback.upload_id` should become (`upload_id`, `query_id`) or
   be cleared when a new search starts. Today a "less sleeves" click from an old search keeps applying
   forever; this is a design decision, not just a bug.
3. **Client-side query id.** Return `query_id` from `/fetch_initial` and send it on `/rerank`, removing
   server-side guessing entirely. Breaking change; needs `api.d.ts` regeneration.

## Tests

- Repository: insert two queries for one upload, assert `get_query_by_upload_id` returns the newest.
- Service: rerank after two searches resolves the second pool (assert returned URLs belong to query 2).
- Regression guard: temporarily remove `ORDER BY` and confirm the test fails (documents the contract).

## Checklist

- [x] Add `ORDER BY id DESC LIMIT 1`
- [x] Log resolved `query_id` (in `get_results_by_upload_id`, called by `/rerank` and fetch-more)
- [x] Add repository + service tests (`test_get_query_by_upload_id_returns_the_newest_query`, `test_get_results_by_upload_id_resolves_the_newest_query`)
- [ ] Decide on follow-up 2 (feedback scoping) before trait evaluation
- [ ] (Optional) Re-run `/rerank` for uploads 1, 2, 3, 4, 13, 24, 26 and confirm the pool matches the last search
