import numpy as np
import pytest

from dtos import SearchItem
from service import profile


def _axes():
    # Six 2-d axes; only the first two are asserted on.
    return {
        key: np.array([1.0, 0.0]) if i == 0 else np.array([0.0, 1.0]) for i, key in enumerate(profile.traits.TRAIT_KEYS)
    }


def _items():
    return [
        SearchItem(title="right", url="right", clip_embedding=[1.0, 0.0], embedding=[0.0, 1.0]),
        SearchItem(title="up", url="up", clip_embedding=[0.0, 1.0], embedding=[0.0, 1.0]),
        SearchItem(title="left", url="left", clip_embedding=[-1.0, 0.0], embedding=[0.0, 1.0]),
    ]


def test_profile_reports_pool_spread_anchor_and_item(monkeypatch):
    monkeypatch.setattr(profile.traits, "get_trait_axes", _axes)
    monkeypatch.setattr(profile, "get_anchor_clip_embedding", lambda uid: np.array([0.0, 1.0]))
    monkeypatch.setattr(profile, "get_results_by_upload_id", lambda uid: _items())

    result = profile.build_trait_profile(7, item_url="right")

    assert result["count"] == 3
    assert result["mean"]["sleeves"] == pytest.approx(0.0)
    assert result["std"]["sleeves"] == pytest.approx(np.sqrt(2 / 3))
    # Anchor points along the second axis, so it is neutral on the first.
    assert result["anchor"]["sleeves"] == pytest.approx(0.0)
    assert result["item"]["sleeves"] == pytest.approx(1.0)


def test_profile_only_returns_item_scores_when_the_url_is_in_the_pool(monkeypatch):
    monkeypatch.setattr(profile.traits, "get_trait_axes", _axes)
    monkeypatch.setattr(profile, "get_anchor_clip_embedding", lambda uid: np.array([0.0, 1.0]))
    monkeypatch.setattr(profile, "get_results_by_upload_id", lambda uid: _items())

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

    with pytest.raises(ValueError, match="no candidates with CLIP vectors"):
        profile.build_trait_profile(7)
