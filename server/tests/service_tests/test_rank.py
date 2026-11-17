from types import SimpleNamespace

import torch

from dtos import SearchItem
from service import rank


class _FakeImage:
    def convert(self, _mode):
        return self


class _FakeDinoProcessor:
    def __call__(self, *, images, return_tensors="pt"):
        return {"images": images}


class _FakeDinoModel:
    def __call__(self, **inputs):
        n = len(inputs["images"])
        return SimpleNamespace(pooler_output=torch.tensor([[1.0, 0.0]] * n, dtype=torch.float32))


class _FakeClipProcessor:
    def __call__(self, *, images, return_tensors="pt", padding=True):
        return {"images": images}


class _FakeClipModel:
    def get_image_features(self, **inputs):
        n = len(inputs["images"])
        return torch.tensor([[0.0, 1.0]] * n, dtype=torch.float32)


def test_pool_ranking_accepts_a_stored_list_anchor(monkeypatch):
    monkeypatch.setattr(rank, "get_embedding_by_upload_id", lambda upload_id: [1.0, 0.0])
    monkeypatch.setattr(rank, "fetch_image_bytes_from_item", lambda item: b"image")
    monkeypatch.setattr(rank, "Image", SimpleNamespace(open=lambda *a, **k: _FakeImage()))
    monkeypatch.setattr(rank, "get_dino_processor", lambda: _FakeDinoProcessor())
    monkeypatch.setattr(rank, "get_dino_model", lambda: _FakeDinoModel())
    monkeypatch.setattr(rank, "get_clip_processor", lambda: _FakeClipProcessor())
    monkeypatch.setattr(rank, "get_clip_model", lambda: _FakeClipModel())

    item = SearchItem(title="long sleeve top", url="a", image_url="a.jpg")
    result = rank.process_and_rank_pool({item}, upload_id=7)

    assert len(result) == 1
    assert result[0].similarity_score == 1.0
    assert result[0].embedding == [1.0, 0.0]
    assert result[0].clip_embedding == [0.0, 1.0]
