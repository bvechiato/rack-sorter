"""Trait-axis scoring: fold signed CLIP feedback onto candidate projections."""

import logging
from typing import Dict, Optional, Sequence, Tuple

import numpy as np

from dtos import SearchItem, RerankFeedback
from service import traits

logger = logging.getLogger(__name__)


def apply_trait_modifiers(
    items: Sequence[SearchItem],
    trait_feedback: Sequence[RerankFeedback],
    anchor_clip,
    axes: Dict[str, np.ndarray],
):
    """Fold trait feedback onto the CLIP projection of every candidate."""

    stats = {
        "events": len(trait_feedback),
        "superseded": 0,
        "applied": 0,
        "skipped_degenerate": 0,
        "skipped_missing_vector": 0,
        "missing_vectors": 0,
        "clamped": 0,
    }
    if not trait_feedback:
        return stats

    # Last-write-wins per (item_url, concept).
    latest: Dict[Tuple[str, str], RerankFeedback] = {}
    for fb in trait_feedback:
        key = (fb.item_url, (fb.concept or "").strip().lower())
        latest.pop(key, None)
        latest[key] = fb
    events = list(latest.values())
    stats["superseded"] = len(trait_feedback) - len(events)
    stats["events"] = len(events)

    anchor_unit = _unit(anchor_clip)
    if anchor_unit is None:
        logger.warning("Trait feedback ignored: anchor CLIP embedding unavailable")
        stats["skipped_missing_vector"] = len(trait_feedback)
        return stats

    adjustments: Dict[str, float] = {item.url: 0.0 for item in items}
    z_cache: Dict[str, Optional[Dict[str, float]]] = {}

    for fb in events:
        key = (fb.concept or "").strip().lower()
        axis = axes.get(key)
        if axis is None:
            logger.warning("Unknown trait concept '%s' ignored; expected one of %s", fb.concept, list(axes))
            continue
        if fb.feedback_type not in ("MORE", "LESS"):
            logger.warning("Unknown feedback type '%s' ignored", fb.feedback_type)
            continue

        clicked = _find_item(items, fb.item_url)
        clicked_clip = _unit(clicked.clip_embedding) if clicked is not None else None
        if clicked_clip is None:
            logger.warning("Cross-sell trait event skipped: no CLIP vector for clicked item %s", fb.item_url)
            stats["skipped_missing_vector"] += 1
            continue
        _assert_same_space(clicked_clip, axis, fb.item_url)

        projection_delta = float(np.dot(clicked_clip - anchor_unit, axis))

        if key in z_cache:
            z_scores = z_cache[key]
        else:
            z_scores, missing, flat = _axis_z_scores(items, axis)
            z_cache[key] = z_scores
            stats["missing_vectors"] += missing
            if flat:
                logger.warning("Trait event skipped: axis '%s' has no spread across this pool (std < %s)", key, traits.MIN_TRAIT_SPREAD)
        if z_scores is None:
            stats["skipped_degenerate"] += 1
            continue

        direction = 1.0 if projection_delta >= 0 else -1.0
        weight = traits.W_MORE if fb.feedback_type == "MORE" else -traits.W_LESS

        for item in items:
            adjustments[item.url] += weight * direction * z_scores.get(item.url, 0.0)

        stats["applied"] += 1

    for item in items:
        adjustment = adjustments.get(item.url, 0.0)
        clamped = max(-traits.MAX_TRAIT_ADJUSTMENT, min(traits.MAX_TRAIT_ADJUSTMENT, adjustment))
        if clamped != adjustment:
            stats["clamped"] += 1
        item.rerank_score = (item.rerank_score or 0.0) + clamped

    logger.info(
        "Trait feedback applied: %d/%d events, superseded=%d, degenerate=%d, missing_clicked=%d, items_without_vector=%d, clamped=%d",
        stats["applied"], stats["events"], stats["superseded"], stats["skipped_degenerate"],
        stats["skipped_missing_vector"], stats["missing_vectors"], stats["clamped"],
    )
    return stats


def _axis_z_scores(items, axis):
    raw: Dict[str, float] = {}
    for item in items:
        vector = _unit(item.clip_embedding)
        if vector is None:
            continue
        _assert_same_space(vector, axis, item.url)
        raw[item.url] = float(np.dot(vector, axis))

    missing = len(items) - len(raw)
    if not raw:
        return None, missing, True

    values = np.fromiter(raw.values(), dtype=float, count=len(raw))
    std = float(values.std())
    if std < traits.MIN_TRAIT_SPREAD:
        return None, missing, True

    mean = float(values.mean())
    z_scores = {
        url: float(np.clip((score - mean) / std, -traits.TRAIT_Z_LIMIT, traits.TRAIT_Z_LIMIT))
        for url, score in raw.items()
    }
    return z_scores, missing, False


def _assert_same_space(vector, axis, label):
    if vector.shape != axis.shape:
        raise ValueError(
            f"Trait vector dimension mismatch for {label}: candidate={vector.shape}, "
            f"axis={axis.shape}. Candidates must store a 512-d FashionCLIP vector; "
            f"a 768-d value means the DINO embedding was passed by mistake."
        )


def _find_item(items, url):
    for item in items:
        if item.url == url:
            return item
    return None


def _unit(vector):
    if vector is None:
        return None
    array = np.asarray(vector, dtype=float).reshape(-1)
    norm = np.linalg.norm(array)
    if norm == 0:
        return None
    return array / norm
