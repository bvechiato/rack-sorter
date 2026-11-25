"""Tests for feedback_flow orchestration, including the cadence-neutral undo path."""

from unittest.mock import MagicMock

import pytest

import service.feedback_flow as mod
from dtos import SearchItem


def _item(url: str) -> SearchItem:
    return SearchItem(title=url, url=url, image_url=f"{url}.jpg")


def _item_response(items) -> list[dict]:
    """Stand-in for to_ItemResponse that returns Pydantic-valid dicts."""
    return [
        {
            "title": i.title,
            "url": i.url,
            "image_url": i.image_url,
            "similarity_score": getattr(i, "similarity_score", 0.0) or 0.0,
        }
        for i in items
    ]


def test_undo_deletes_last_event_and_reranks_without_fetch_more(monkeypatch):
    deleted = MagicMock(return_value=True)
    monkeypatch.setattr(mod, "delete_last_feedback_for_upload", deleted)
    monkeypatch.setattr(mod, "get_results_by_upload_id", lambda uid: {_item("a")})
    monkeypatch.setattr(mod, "get_feedback_for_upload", lambda uid: [])
    reranked = MagicMock(return_value=[_item("a")])
    monkeypatch.setattr(mod, "rerank", reranked)
    monkeypatch.setattr(mod, "to_ItemResponse", _item_response)
    # If undo ever pulled a page, this would record the call and fail the assertion.
    fetch_more = MagicMock()
    monkeypatch.setattr(mod, "fetch_more_for_upload", fetch_more)

    result = mod.undo_feedback_and_rerank(6)

    deleted.assert_called_once_with(6)
    reranked.assert_called_once()
    fetch_more.assert_not_called()
    assert len(result.pool) == 1


def test_undo_raises_when_no_feedback_to_delete(monkeypatch):
    monkeypatch.setattr(mod, "delete_last_feedback_for_upload", lambda uid: False)

    with pytest.raises(ValueError, match="no feedback to undo"):
        mod.undo_feedback_and_rerank(6)


def test_apply_feedback_returns_ranked_pool(monkeypatch):
    from api.models import FeedbackEvent

    inserted = MagicMock()
    monkeypatch.setattr(mod, "insert_rerank_feedback", inserted)
    monkeypatch.setattr(mod, "fetch_more_for_upload", MagicMock())
    monkeypatch.setattr(mod, "get_results_by_upload_id", lambda uid: {_item("a")})
    monkeypatch.setattr(mod, "get_feedback_for_upload", lambda uid: [])
    monkeypatch.setattr(mod, "rerank", lambda items, fb, upload_id: items)
    monkeypatch.setattr(mod, "to_ItemResponse", _item_response)

    result = mod.apply_feedback_and_rerank(
        6,
        [FeedbackEvent(item_url="a", feedback_type="MORE", concept="sleeves")],
        fetch_more=False,
    )

    inserted.assert_called_once()
    assert len(result.pool) == 1
