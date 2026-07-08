import numpy as np
import service.rank as rank


class FakeTensor:
    def __init__(self, values):
        self._values = np.array(values, dtype=float)

    def numpy(self):
        return self._values

    def squeeze(self):
        return FakeTensor(np.squeeze(self._values))


def test_process_and_rank_pool_ranks_matching_items(monkeypatch):
    def fake_process_and_normalise(image_payload):
        if image_payload == b"anchor":
            return FakeTensor([[1.0, 0.0]])
        if image_payload == b"match":
            return FakeTensor([[1.0, 0.0]])
        return FakeTensor([[0.0, 1.0]])

    monkeypatch.setattr(rank, "process_and_normalise", fake_process_and_normalise)
    monkeypatch.setattr(
        rank,
        "fetch_image_bytes_from_url",
        lambda item: {"good": b"match", "bad": b"mismatch"}.get(item["title"]),
    )

    ranked = rank.process_and_rank_pool(
        [{"title": "bad", "url": "u2"}, {"title": "good", "url": "u1"}],
        b"anchor",
    )

    assert [item["title"] for item in ranked] == ["good", "bad"]
    assert ranked[0]["similarity_score"] == 1.0
    assert ranked[0]["embedding"] == [1.0, 0.0]


