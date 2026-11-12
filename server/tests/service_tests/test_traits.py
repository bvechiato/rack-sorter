import numpy as np
import pytest

from dtos import RerankFeedback, SearchItem
from service import rerank as rerank_module
from service import traits

AXES = {"sleeves": np.array([1.0, 0.0])}
# Anchor sits at the neutral point between the two poles.
ANCHOR = np.array([0.0, 1.0])


def _pool():
    return [
        SearchItem(
            title="long sleeve knit",
            url="sleeved",
            image_url="sleeved.jpg",
            embedding=[0.0, 1.0],
            clip_embedding=[1.0, 0.0],
            similarity_score=0.5,
        ),
        SearchItem(
            title="sleeveless top",
            url="sleeveless",
            image_url="sleeveless.jpg",
            embedding=[1.0, 0.0],
            clip_embedding=[-1.0, 0.0],
            similarity_score=0.9,
        ),
    ]


def _apply(items, feedback):
    return rerank_module.apply_trait_modifiers(items, feedback, ANCHOR, AXES)


def test_trait_axes_cover_the_vocabulary():
    # Build from injected embeddings so the real CLIP model is never loaded.
    import service.identifier as identifier

    fake = []
    for key in traits.TRAIT_KEYS:
        positive, negative = traits.TRAIT_PROMPTS[key]
        fake.extend([np.array([1.0, 0.0]), np.array([-1.0, 0.0])])

    original = identifier.get_text_embeddings
    identifier.get_text_embeddings = lambda texts: np.vstack(fake)
    traits._axes.clear()
    try:
        axes = traits.get_trait_axes()
        assert set(axes) == set(traits.TRAIT_KEYS)
        for axis in axes.values():
            assert axis.shape == (2,)
            assert np.isclose(np.linalg.norm(axis), 1.0)
    finally:
        identifier.get_text_embeddings = original
        traits._axes.clear()


def test_axis_prompt_polarity_points_at_the_positive_pole():
    # positive prompt is [1,0], negative is [-1,0] -> axis must be [1,0]
    import service.identifier as identifier

    fake = []
    for _ in traits.TRAIT_KEYS:
        fake.extend([np.array([1.0, 0.0]), np.array([-1.0, 0.0])])

    original = identifier.get_text_embeddings
    identifier.get_text_embeddings = lambda texts: np.vstack(fake)
    traits._axes.clear()
    try:
        axes = traits.get_trait_axes()
        for key, axis in axes.items():
            assert np.allclose(axis, [1.0, 0.0]), f"{key} axis has the wrong polarity"
    finally:
        identifier.get_text_embeddings = original
        traits._axes.clear()


def test_more_moves_the_pool_toward_the_clicked_item():
    items = _pool()
    # Clicked item is the sleeveless one, so d = -1.
    _apply(items, [RerankFeedback(item_url="sleeveless", feedback_type="MORE", concept="sleeves")])

    by_url = {item.url: item for item in items}
    assert by_url["sleeveless"].rerank_score > by_url["sleeved"].rerank_score


def test_less_inverts_the_order():
    items = _pool()
    _apply(items, [RerankFeedback(item_url="sleeveless", feedback_type="LESS", concept="sleeves")])

    by_url = {item.url: item for item in items}
    assert by_url["sleeved"].rerank_score > by_url["sleeveless"].rerank_score


def test_clicked_item_equal_to_anchor_is_a_deadband_no_op():
    items = _pool()
    # Anchor and clicked item both sit at s = 0.
    anchor = np.array([0.0, 1.0])
    clicked = [item for item in items if item.url == "sleeved"][0]
    clicked.clip_embedding = [0.0, 1.0]

    stats = rerank_module.apply_trait_modifiers(
        items,
        [RerankFeedback(item_url="sleeved", feedback_type="MORE", concept="sleeves")],
        anchor,
        AXES,
    )

    assert stats["skipped_deadband"] == 1
    assert stats["applied"] == 0
    assert all(item.rerank_score == 0.0 for item in items)


def test_no_feedback_leaves_scores_untouched():
    items = _pool()
    stats = _apply(items, [])
    assert stats["events"] == 0
    assert [item.rerank_score for item in items] == [None, None]


def test_unknown_concept_is_ignored_not_applied():
    items = _pool()
    stats = _apply(items, [RerankFeedback(item_url="sleeveless", feedback_type="MORE", concept="floral")])
    assert stats["applied"] == 0
    assert all(item.rerank_score == 0.0 for item in items)


def test_total_adjustment_is_clamped_per_item():
    items = _pool()
    # Ten distinct clicks (different items) so the last-wins rule does not collapse them.
    extra = [
        SearchItem(
            title=f"sleeveless {i}",
            url=f"extra-{i}",
            image_url=f"extra-{i}.jpg",
            embedding=[1.0, 0.0],
            clip_embedding=[-1.0, 0.0],
            similarity_score=0.4,
        )
        for i in range(10)
    ]
    items.extend(extra)
    events = [
        RerankFeedback(item_url=item.url, feedback_type="MORE", concept="sleeves")
        for item in extra
    ]
    stats = _apply(items, events)

    by_url = {item.url: item for item in items}
    assert by_url["sleeveless"].rerank_score == pytest.approx(traits.MAX_TRAIT_ADJUSTMENT)
    assert by_url["sleeved"].rerank_score == pytest.approx(-traits.MAX_TRAIT_ADJUSTMENT)
    # 12 of the 12 items exceed the cap: both original items plus the ten extra clicks.
    assert stats["clamped"] == 12


def test_switching_polarity_uses_the_last_choice():
    items = _pool()
    stats = _apply(
        items,
        [
            RerankFeedback(item_url="sleeveless", feedback_type="MORE", concept="sleeves"),
            RerankFeedback(item_url="sleeveless", feedback_type="LESS", concept="sleeves"),
        ],
    )

    by_url = {item.url: item for item in items}
    assert stats["superseded"] == 1
    # LESS sleeves on a sleeveless click means "toward sleeved".
    assert by_url["sleeved"].rerank_score > by_url["sleeveless"].rerank_score


def test_dino_vector_in_clip_slot_fails_loudly():
    items = _pool()
    items[0].clip_embedding = [1.0] + [0.0] * 767

    with pytest.raises(ValueError, match="dimension mismatch"):
        _apply(items, [RerankFeedback(item_url="sleeveless", feedback_type="MORE", concept="sleeves")])


def test_base_scores_do_not_crash_on_missing_embedding():
    items = [SearchItem(title="no vector", url="missing", image_url="missing.jpg")]
    scored = rerank_module.compute_base_visual_scores(items, np.array([[1.0, 0.0]]))

    assert scored[0].rerank_score == 0.0


def _angled_pool(thetas):
    """Unit vectors in the axis plane; projection onto [1,0] is cos(theta)."""
    return [
        SearchItem(
            title=f"item {theta}",
            url=f"u{theta}",
            image_url=f"u{theta}.jpg",
            embedding=[0.0, 1.0],
            clip_embedding=[float(np.cos(np.radians(theta))), float(np.sin(np.radians(theta)))],
        )
        for theta in thetas
    ]


def test_adjustment_is_pool_relative_not_raw_projection():
    # Wide spread (cos = ±0.87) vs narrow spread (cos = ±0.17): both are ±1 std, so
    # feedback must produce the same score delta. Raw projections would differ 5x.
    wide = _angled_pool([30, 150])
    narrow = _angled_pool([80, 100])

    rerank_module.apply_trait_modifiers(
        wide, [RerankFeedback(item_url="u150", feedback_type="MORE", concept="sleeves")], ANCHOR, AXES
    )
    rerank_module.apply_trait_modifiers(
        narrow, [RerankFeedback(item_url="u100", feedback_type="MORE", concept="sleeves")], ANCHOR, AXES
    )

    wide_scores = sorted(item.rerank_score for item in wide)
    narrow_scores = sorted(item.rerank_score for item in narrow)
    assert wide_scores == pytest.approx(narrow_scores)
    assert wide_scores[1] > wide_scores[0]


def test_flat_axis_is_skipped_and_reported():
    # Every candidate projects identically, so there is no direction to sort on.
    items = _angled_pool([30, 30.0001])
    stats = _apply(items, [RerankFeedback(item_url="u30", feedback_type="MORE", concept="sleeves")])

    assert stats["skipped_degenerate"] == 1
    assert stats["applied"] == 0
    assert all(item.rerank_score == 0.0 for item in items)
