import numpy as np
import service.rank as rank
from dtos import SearchItem


class FakeTensor:
    def __init__(self, values):
        self._values = np.array(values, dtype=float)

    def numpy(self):
        return self._values

    def squeeze(self):
        return FakeTensor(np.squeeze(self._values))

def test_ranks_matching_items(monkeypatch):
    # given
    def fake_process_and_normalise(image_payload):
        if image_payload == b"anchor":
            return FakeTensor([[1.0, 0.0]])
        if image_payload == b"match":
            return FakeTensor([[1.0, 0.0]])
        return FakeTensor([[0.0, 1.0]])
    
    def fake_get_embedding_by_upload_id(upload_id):
        return FakeTensor([[1.0, 0.0]])

    monkeypatch.setattr(rank, "process_and_normalise", fake_process_and_normalise)
    monkeypatch.setattr(
        rank,
        "fetch_image_bytes_from_url",
        lambda item: {"good": b"match", "bad": b"mismatch"}.get(item.title),
    )
    monkeypatch.setattr(rank, "get_embedding_by_upload_id", fake_get_embedding_by_upload_id)

    # when
    ranked = rank.process_and_rank_pool(
        {SearchItem(title="bad", url="u2"), SearchItem(title="good", url="u1")},
        b"anchor_id",
    )

    assert [item.title for item in ranked] == ["good", "bad"]
    assert ranked[0].similarity_score == 1.0
    assert ranked[0].embedding == [1.0, 0.0]

def test_fallback_when_embedding_not_in_db(monkeypatch):
    # Trackers to verify side effects
    db_insert_called_with = {}
    get_bytes_called = False

    # given
    def fake_get_embedding_fail(upload_id):
        raise Exception("DB Miss!")

    def fake_get_upload_bytes_by_id(upload_id):
        nonlocal get_bytes_called
        get_bytes_called = True
        return b"raw_anchor_bytes"

    def fake_process_and_normalise(image_bytes):
        # Anchor gets processed manually
        if image_bytes == b"raw_anchor_bytes":
            return FakeTensor([[1.0, 0.0]])
        # Scraped item gets processed
        return FakeTensor([[1.0, 0.0]])

    def fake_insert_embedding(upload_id, embedding_list):
        nonlocal db_insert_called_with
        db_insert_called_with = {"id": upload_id, "embedding": embedding_list}

    monkeypatch.setattr(rank, "get_embedding_by_upload_id", fake_get_embedding_fail)
    monkeypatch.setattr(rank, "get_upload_bytes_by_id", fake_get_upload_bytes_by_id)
    monkeypatch.setattr(rank, "process_and_normalise", fake_process_and_normalise)
    monkeypatch.setattr(rank, "insert_embedding_for_upload", fake_insert_embedding)
    monkeypatch.setattr(rank, "fetch_image_bytes_from_url", lambda item: b"some_bytes")

    # when
    ranked = rank.process_and_rank_pool(
        {SearchItem(title="item1", url="u1")},
        upload_id=42,
    )

    # then
    assert get_bytes_called is True
    assert db_insert_called_with == {"id": 42, "embedding": [1.0, 0.0]}
    assert len(ranked) == 1

def test_skips_item_when_image_fetch_fails(monkeypatch):
    # given
    monkeypatch.setattr(rank, "get_embedding_by_upload_id", lambda id: FakeTensor([[1.0, 0.0]]))
    
    # Simulating a failed download (returns None) for 'broken', but successful for 'working'
    monkeypatch.setattr(
        rank, 
        "fetch_image_bytes_from_url", 
        lambda item: b"valid_image" if item.title == "working" else None
    )
    monkeypatch.setattr(rank, "process_and_normalise", lambda bytes: FakeTensor([[1.0, 0.0]]))

    # when
    ranked = rank.process_and_rank_pool(
        {SearchItem(title="broken", url="u1"), SearchItem(title="working", url="u2")},
        upload_id=1,
    )

    # then
    assert len(ranked) == 1
    assert ranked[0].title == "working"

def test_skips_corrupted_image_processing(monkeypatch):
    # given
    monkeypatch.setattr(rank, "get_embedding_by_upload_id", lambda id: FakeTensor([[1.0, 0.0]]))
    monkeypatch.setattr(rank, "fetch_image_bytes_from_url", lambda item: item.title.encode())

    # Throw an error only when trying to process the corrupt image
    def fake_process_and_normalise(image_bytes):
        if image_bytes == b"corrupt":
            raise ValueError("Invalid image file format!")
        return FakeTensor([[0.9, 0.1]])

    monkeypatch.setattr(rank, "process_and_normalise", fake_process_and_normalise)

    # when
    ranked = rank.process_and_rank_pool(
        {SearchItem(title="corrupt", url="u1"), SearchItem(title="healthy", url="u2")},
        upload_id=1,
    )

    # then
    assert len(ranked) == 1
    assert ranked[0].title == "healthy"

def test_handles_empty_scraped_items_pool(monkeypatch):
    # given
    monkeypatch.setattr(rank, "get_embedding_by_upload_id", lambda id: FakeTensor([[1.0, 0.0]]))

    # when
    ranked = rank.process_and_rank_pool(set(), upload_id=1)

    # then
    assert ranked == []