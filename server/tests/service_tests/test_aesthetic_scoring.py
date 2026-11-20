import numpy as np
import pytest

from api.models import FeedbackEvent
from dtos import RerankFeedback, SearchItem
from service import aesthetic_scoring, traits
from service import rerank as rerank_module

# Unit-axis fixture: the injected phrase "formal" embeds along +AXIS; the two pool items
# project +0.8 / -0.8 on it, so the pool std is 0.8 and z = ±1.
AXIS = np.array([1.0, 0.0])


@pytest.fixture(autouse=True)
def _clean_aesthetic_axis_cache():
    aesthetic_scoring._axis_cache.clear()
    yield
    aesthetic_scoring._axis_cache.clear()


def _inject_text_embeddings(monkeypatch, phrase_vectors=None):
    """Make every phrase resolve through the injected text encoder (no real model)."""
    import service.identifier as identifier

    phrase_vectors = phrase_vectors or {}

    def fake_get_text_embeddings(texts):
        return np.vstack([phrase_vectors.get(text, AXIS) for text in texts])

    monkeypatch.setattr(identifier, "get_text_embeddings", fake_get_text_embeddings)


def _pool():
    return [
        SearchItem(title="a", url="formal", image_url="a.jpg", clip_embedding=[0.8, 0.6], similarity_score=0.5),
        SearchItem(title="b", url="casual", image_url="b.jpg", clip_embedding=[-0.8, 0.6], similarity_score=0.9),
    ]


def test_aesthetic_axis_is_unit_normalised_and_cached(monkeypatch):
    _inject_text_embeddings(monkeypatch, {"formal": np.array([2.0, 0.0])})
    axis = aesthetic_scoring.get_aesthetic_axis("formal")
    assert np.allclose(axis, [1.0, 0.0])
    # Key is the stripped, lower-cased phrase; the same intent shares one axis.
    assert aesthetic_scoring.get_aesthetic_axis("Formal ") is axis


def test_aesthetic_axis_zero_vector_raises(monkeypatch):
    _inject_text_embeddings(monkeypatch, {"formal": np.array([0.0, 0.0])})
    with pytest.raises(ValueError, match="zero vector"):
        aesthetic_scoring.get_aesthetic_axis("formal")


def test_aesthetic_steering_is_absolute_toward_the_phrase(monkeypatch):
    _inject_text_embeddings(monkeypatch)
    items = _pool()
    aesthetic_scoring.apply_aesthetic_modifiers(items, [RerankFeedback(item_url="formal", feedback_type="MORE", aesthetic="formal")])
    by_url = {item.url: item for item in items}
    assert by_url["formal"].rerank_score > by_url["casual"].rerank_score


def test_aesthetic_steering_does_not_depend_on_the_event_item_url(monkeypatch):
    _inject_text_embeddings(monkeypatch)
    run_a = _pool()
    aesthetic_scoring.apply_aesthetic_modifiers(run_a, [RerankFeedback(item_url="casual", feedback_type="MORE", aesthetic="formal")])
    run_b = _pool()
    aesthetic_scoring.apply_aesthetic_modifiers(run_b, [RerankFeedback(item_url="formal", feedback_type="MORE", aesthetic="formal")])
    assert {item.url: item.rerank_score for item in run_a} == pytest.approx(
        {item.url: item.rerank_score for item in run_b}
    )


def test_multiple_phrases_accumulate(monkeypatch):
    _inject_text_embeddings(monkeypatch)
    # Shrink the weight so the combined adjustment stays under the cap and the
    # accumulation itself is observable.
    monkeypatch.setattr(traits, "W_AESTHETIC", 0.1)
    items = _pool()
    stats = aesthetic_scoring.apply_aesthetic_modifiers(
        items,
        [
            RerankFeedback(item_url="x", feedback_type="MORE", aesthetic="formal"),
            RerankFeedback(item_url="x", feedback_type="MORE", aesthetic="minimal"),
        ],
    )
    assert stats["applied"] == 2
    by_url = {item.url: item for item in items}
    assert by_url["formal"].rerank_score == pytest.approx(2 * 0.1)
    assert by_url["casual"].rerank_score == pytest.approx(-2 * 0.1)


def test_repeated_phrase_is_applied_once(monkeypatch):
    _inject_text_embeddings(monkeypatch)
    items = _pool()
    stats = aesthetic_scoring.apply_aesthetic_modifiers(
        items,
        [
            RerankFeedback(item_url="a", feedback_type="MORE", aesthetic="formal"),
            RerankFeedback(item_url="b", feedback_type="MORE", aesthetic="FORMAL"),
        ],
    )
    assert stats["superseded"] == 1
    assert stats["applied"] == 1
    by_url = {item.url: item for item in items}
    assert by_url["formal"].rerank_score == pytest.approx(traits.W_AESTHETIC)


def test_less_event_removes_the_phrase(monkeypatch):
    _inject_text_embeddings(monkeypatch)
    items = _pool()
    stats = aesthetic_scoring.apply_aesthetic_modifiers(
        items,
        [
            RerankFeedback(item_url="a", feedback_type="MORE", aesthetic="formal"),
            RerankFeedback(item_url="a", feedback_type="LESS", aesthetic="formal"),
        ],
    )
    assert stats["removed"] == 1
    assert stats["applied"] == 0
    assert [item.rerank_score for item in items] == [None, None]


def test_phrase_can_be_switched_back_on(monkeypatch):
    _inject_text_embeddings(monkeypatch)
    items = _pool()
    stats = aesthetic_scoring.apply_aesthetic_modifiers(
        items,
        [
            RerankFeedback(item_url="a", feedback_type="MORE", aesthetic="formal"),
            RerankFeedback(item_url="a", feedback_type="LESS", aesthetic="formal"),
            RerankFeedback(item_url="a", feedback_type="MORE", aesthetic="formal"),
        ],
    )
    assert stats["removed"] == 0
    assert stats["applied"] == 1
    by_url = {item.url: item for item in items}
    assert by_url["formal"].rerank_score == pytest.approx(traits.W_AESTHETIC)


def test_removing_one_phrase_keeps_the_others(monkeypatch):
    _inject_text_embeddings(monkeypatch)
    monkeypatch.setattr(traits, "W_AESTHETIC", 0.1)
    items = _pool()
    stats = aesthetic_scoring.apply_aesthetic_modifiers(
        items,
        [
            RerankFeedback(item_url="a", feedback_type="MORE", aesthetic="formal"),
            RerankFeedback(item_url="a", feedback_type="MORE", aesthetic="minimal"),
            RerankFeedback(item_url="a", feedback_type="LESS", aesthetic="minimal"),
        ],
    )
    assert stats["removed"] == 1
    assert stats["applied"] == 1
    by_url = {item.url: item for item in items}
    assert by_url["formal"].rerank_score == pytest.approx(0.1)


def test_blank_phrases_are_skipped(monkeypatch):
    _inject_text_embeddings(monkeypatch)
    items = _pool()
    stats = aesthetic_scoring.apply_aesthetic_modifiers(
        items, [RerankFeedback(item_url="a", feedback_type="MORE", aesthetic="   ")]
    )
    assert stats["skipped_empty_phrase"] == 1
    assert stats["applied"] == 0
    assert all(item.rerank_score == 0.0 for item in items)


def test_empty_aesthetic_feedback_leaves_scores_untouched(monkeypatch):
    _inject_text_embeddings(monkeypatch)
    items = _pool()
    stats = aesthetic_scoring.apply_aesthetic_modifiers(items, [])
    assert stats["events"] == 0
    assert [item.rerank_score for item in items] == [None, None]


def test_flat_axis_is_skipped_and_reported(monkeypatch):
    _inject_text_embeddings(monkeypatch)
    items = [
        SearchItem(title="a", url="u1", image_url="a.jpg", clip_embedding=[1.0, 0.0]),
        SearchItem(title="b", url="u2", image_url="b.jpg", clip_embedding=[1.0, 0.0]),
    ]
    stats = aesthetic_scoring.apply_aesthetic_modifiers(
        items, [RerankFeedback(item_url="u1", feedback_type="MORE", aesthetic="formal")]
    )
    assert stats["skipped_degenerate"] == 1
    assert stats["applied"] == 0
    assert all(item.rerank_score in (None, 0.0) for item in items)


def test_missing_vectors_are_counted_and_zero(monkeypatch):
    _inject_text_embeddings(monkeypatch)
    items = [
        SearchItem(title="a", url="with", image_url="a.jpg", clip_embedding=[0.8, 0.6]),
        SearchItem(title="b", url="without", image_url="b.jpg"),
        SearchItem(title="c", url="with2", image_url="c.jpg", clip_embedding=[-0.8, 0.6]),
    ]
    stats = aesthetic_scoring.apply_aesthetic_modifiers(
        items, [RerankFeedback(item_url="with", feedback_type="MORE", aesthetic="formal")]
    )
    assert stats["missing_vectors"] == 1
    assert stats["applied"] == 1
    by_url = {item.url: item for item in items}
    assert by_url["without"].rerank_score == 0.0


def test_shared_cap_clamps(monkeypatch):
    _inject_text_embeddings(monkeypatch)
    # One outlier projecting +1, nine projecting -1: z(outlier) = 3 (std 0.6), so the
    # aesthetic adjustment is 0.45 * 3 = 1.35, clamped to MAX_TRAIT_ADJUSTMENT.
    items = [
        SearchItem(title="out", url="u_out", image_url="o.jpg", clip_embedding=[1.0, 0.0], similarity_score=0.5)
    ] + [
        SearchItem(title=f"i{i}", url=f"u{i}", image_url=f"i{i}.jpg", clip_embedding=[-1.0, 0.0], similarity_score=0.5)
        for i in range(9)
    ]
    stats = aesthetic_scoring.apply_aesthetic_modifiers(
        items, [RerankFeedback(item_url="u_out", feedback_type="MORE", aesthetic="formal")]
    )
    assert stats["applied"] == 1
    assert stats["clamped"] > 0
    by_url = {item.url: item for item in items}
    assert by_url["u_out"].rerank_score == pytest.approx(traits.MAX_TRAIT_ADJUSTMENT)
    assert all(item.rerank_score is not None and abs(item.rerank_score) <= traits.MAX_TRAIT_ADJUSTMENT + 1e-9 for item in items)


def test_dino_vector_in_clip_slot_fails_loudly(monkeypatch):
    _inject_text_embeddings(monkeypatch)
    items = _pool()
    items[0].clip_embedding = [1.0] + [0.0] * 767
    with pytest.raises(ValueError, match="dimension mismatch"):
        aesthetic_scoring.apply_aesthetic_modifiers(
            items, [RerankFeedback(item_url="formal", feedback_type="MORE", aesthetic="formal")]
        )


def test_rerank_integration_aesthetic_only(monkeypatch):
    _inject_text_embeddings(monkeypatch)
    items = [
        SearchItem(title="a", url="formal", image_url="a.jpg", embedding=[0.0, 1.0], clip_embedding=[0.8, 0.6], similarity_score=0.5),
        SearchItem(title="b", url="casual", image_url="b.jpg", embedding=[0.0, 1.0], clip_embedding=[-0.8, 0.6], similarity_score=0.5),
    ]
    monkeypatch.setattr(rerank_module, "get_embedding_by_upload_id", lambda upload_id: [0.0, 1.0])
    history = [RerankFeedback(item_url="formal", feedback_type="MORE", aesthetic="formal")]
    reranked = rerank_module.rerank(items, history, upload_id=1)
    assert reranked[0].url == "formal"


def test_aesthetic_events_do_not_feed_the_visual_lane(monkeypatch):
    _inject_text_embeddings(monkeypatch)
    captured = {}

    def fake_intent(anchor, image_feedback):
        captured["image_fb"] = image_feedback
        return np.array([[1.0, 0.0]])

    monkeypatch.setattr(rerank_module, "build_intent_vector", fake_intent)
    monkeypatch.setattr(rerank_module, "get_embedding_by_upload_id", lambda upload_id: [1.0, 0.0])
    items = _pool()
    rerank_module.rerank(
        items, [RerankFeedback(item_url="x", feedback_type="MORE", aesthetic="formal")], upload_id=1
    )
    assert captured["image_fb"] == []


def test_feedback_event_parses_aesthetic():
    event = FeedbackEvent(item_url="u", feedback_type="MORE", aesthetic="formal")
    assert event.aesthetic == "formal"
    assert event.concept is None


def test_rerank_feedback_from_row_with_aesthetic():
    rf = RerankFeedback.from_row(("u1", "MORE", None, "formal"))
    assert rf.item_url == "u1"
    assert rf.feedback_type == "MORE"
    assert rf.aesthetic == "formal"
