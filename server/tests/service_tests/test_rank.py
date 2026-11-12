import numpy as np

from dtos import SearchItem
from service import rank


class _FakeTensor:
    """Stands in for the DINO tensor without loading torch in the assertion."""

    def __init__(self, array):
        self.array = array

    def numpy(self):
        return self.array

    def squeeze(self):
        return _FakeTensor(np.squeeze(self.array))


def test_pool_ranking_accepts_a_stored_list_anchor(monkeypatch):
    # `get_embedding_by_upload_id` returns a plain list on every call after the
    # first ingest. Fetch-more used to call `.numpy()` on it and drop every new
    # item, so this path must be exercised with a list, not a tensor.
    monkeypatch.setattr(rank, "get_embedding_by_upload_id", lambda upload_id: [1.0, 0.0])
    monkeypatch.setattr(rank, "fetch_image_bytes_from_item", lambda item: b"image")
    monkeypatch.setattr(
        rank, "process_and_normalise", lambda data: _FakeTensor(np.array([[1.0, 0.0]]))
    )
    monkeypatch.setattr(rank, "get_single_clip_embedding", lambda image: np.array([0.0, 1.0]))

    item = SearchItem(title="long sleeve top", url="a", image_url="a.jpg")
    result = rank.process_and_rank_pool({item}, upload_id=7)

    assert len(result) == 1
    assert result[0].similarity_score == 1.0
    assert result[0].embedding == [1.0, 0.0]
    assert result[0].clip_embedding == [0.0, 1.0]
