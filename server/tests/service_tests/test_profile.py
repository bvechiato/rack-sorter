import numpy as np
import pytest

from dtos import RerankFeedback, SearchItem
from service import profile


def _axes():
    # Six 2-d axes; only the first two are asserted on.
    return {key: np.array([1.0, 0.0]) if i == 0 else np.array([0.0, 1.0]) for i, key in enumerate(profile.traits.TRAIT_KEYS)}


def _items():
    return [
        SearchItem(title="right", url="right", clip_embedding=[1.0, 0.0], embedding=[0.0, 1.0]),
        SearchItem(title="up", url="up", clip_embedding=[0.0, 1.0], embedding=[0.0, 1.0]),
        SearchItem(title="left", url="left", clip_embedding=[-1.0, 0.0], embedding=[0.0, 1.0]),
    ]


def test_profile_reports_pool_spread_anchor_and_top(monkeypatch):
    captured = {}

    monkeypatch.setattr(profile.traits, "get_trait_axes", _axes)
    monkeypatch.setattr(profile, "get_anchor_clip_embedding", lambda uid: np.array([0.0, 1.0]))
    monkeypatch.setattr(profile, "get_results_by_upload_id", lambda uid: _items())
    monkeypatch.setattr(profile, "get_feedback_for_upload", lambda uid: [])

    def fake_rerank(items, history, upload_id):
        captured["history"] = history
        return list(items)

    monkeypatch.setattr(profile, "rerank", fake_rerank)

    result = profile.build_trait_profile(7, item_url="right")

    assert result["count"] == 3
    assert result["top_n"] == 3
    assert result["mean"]["sleeves"] == pytest.approx(0.0)
    assert result["std"]["sleeves"] == pytest.approx(np.sqrt(2 / 3))
    # Anchor points along the second axis, so it is neutral on the first.
    assert result["anchor"]["sleeves"] == pytest.approx(0.0)
    assert result["top"]["sleeves"] == pytest.approx(0.0)
    assert result["item"]["sleeves"] == pytest.approx(1.0)
    assert captured["history"] == []


def test_profile_only_returns_item_scores_when_the_url_is_in_the_pool(monkeypatch):
    monkeypatch.setattr(profile.traits, "get_trait_axes", _axes)
    monkeypatch.setattr(profile, "get_anchor_clip_embedding", lambda uid: np.array([0.0, 1.0]))
    monkeypatch.setattr(profile, "get_results_by_upload_id", lambda uid: _items())
    monkeypatch.setattr(profile, "get_feedback_for_upload", lambda uid: [])
    monkeypatch.setattr(profile, "rerank", lambda items, history, upload_id: list(items))

    assert profile.build_trait_profile(7, item_url="missing")["item"] is None
    assert profile.build_trait_profile(7)["item"] is None


def test_profile_fails_loudly_without_vectors(monkeypatch):
    monkeypatch.setattr(profile.traits, "get_trait_axes", _axes)
    monkeypatch.setattr(profile, "get_anchor_clip_embedding", lambda uid: np.array([0.0, 1.0]))
    monkeypatch.setattr(
        profile,
        "get_results_by_upload_id",
        lambda uid: [SearchItem(title="x", url="x", clip_embedding=None)],
    )
    monkeypatch.setattr(profile, "get_feedback_for_upload", lambda uid: [])
    monkeypatch.setattr(profile, "rerank", lambda items, history, upload_id: list(items))

    with pytest.raises(ValueError, match="no candidates with CLIP vectors"):
        profile.build_trait_profile(7)


def test_profile_uses_the_feedback_history(monkeypatch):
    seen = {}
    monkeypatch.setattr(profile.traits, "get_trait_axes", _axes)
    monkeypatch.setattr(profile, "get_anchor_clip_embedding", lambda uid: np.array([0.0, 1.0]))
    monkeypatch.setattr(profile, "get_results_by_upload_id", lambda uid: _items())
    monkeypatch.setattr(
        profile,
        "get_feedback_for_upload",
        lambda uid: [RerankFeedback(item_url="right", feedback_type="MORE", concept="sleeves")],
    )
    monkeypatch.setattr(
        profile, "rerank", lambda items, history, upload_id: seen.update(history=history) or list(items)
    )

    profile.build_trait_profile(7)
    assert seen["history"][0].concept == "sleeves"
