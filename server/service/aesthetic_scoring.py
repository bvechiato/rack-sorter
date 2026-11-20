"""Absolute, text-driven aesthetic steering.

Aesthetic feedback carries a user phrase (e.g. ``"formal"``) instead of a clicked-vs-anchor
direction: the axis is the normalised FashionCLIP text embedding of the phrase, and each
candidate is scored by ``w * dot(unit(clip_i), axis)`` — positive pushes the pool toward the
phrase, with no dependency on the clicked item or the anchor. Standardisation and the
flat-pool skip reuse ``trait_scoring._axis_z_scores``; the adjustment shares
``MAX_TRAIT_ADJUSTMENT`` with the physical lanes.

``feedback_type`` is the on/off switch for the phrase, not a direction: ``MORE`` steers
toward it and ``LESS`` removes it (the client sends ``LESS`` when a style chip is switched
off). The history is append-only, so last-write-wins per phrase is what makes removal work.
"""

import logging
from typing import Dict, Sequence

import numpy as np

from dtos import RerankFeedback, SearchItem
from service import traits
from service.trait_scoring import _axis_z_scores

logger = logging.getLogger(__name__)

# phrase (stripped, lower-cased) -> unit axis. Same intent typed twice shares one axis.
_axis_cache: Dict[str, np.ndarray] = {}


def get_aesthetic_axis(phrase: str) -> np.ndarray:
    """Unit-normalised 512-d FashionCLIP text embedding of the user's phrase."""
    key = phrase.strip().lower()
    axis = _axis_cache.get(key)
    if axis is None:
        from service.identifier import get_text_embeddings

        vector = np.asarray(get_text_embeddings([phrase]), dtype=float).reshape(-1)
        norm = np.linalg.norm(vector)
        if norm == 0:
            raise ValueError(f"Degenerate aesthetic phrase {phrase!r}: embeds to the zero vector")
        axis = vector / norm
        _axis_cache[key] = axis
    return axis


def apply_aesthetic_modifiers(
    items: Sequence[SearchItem],
    aesthetic_feedback: Sequence[RerankFeedback],
) -> Dict:
    """Fold aesthetic feedback onto the pool: additive, absolute, per-phrase last-write-wins."""
    stats: Dict[str, int] = {
        "events": len(aesthetic_feedback),
        "superseded": 0,
        "removed": 0,
        "applied": 0,
        "skipped_degenerate": 0,
        "skipped_empty_phrase": 0,
        "missing_vectors": 0,
        "clamped": 0,
    }
    if not aesthetic_feedback:
        return stats

    # Last-write-wins per phrase (mirrors the physical lanes' per-concept dedupe): the
    # history is append-only, so the last event for a phrase carries the user's intent —
    # including a trailing LESS, which switches the phrase off.
    latest: Dict[str, RerankFeedback] = {}
    for fb in aesthetic_feedback:
        phrase = (fb.aesthetic or "").strip()
        if not phrase:
            stats["skipped_empty_phrase"] += 1
            continue
        key = phrase.lower()
        latest.pop(key, None)
        latest[key] = fb
    events = list(latest.values())
    stats["superseded"] = len(aesthetic_feedback) - len(events)
    stats["events"] = len(events)

    # A phrase whose latest event is LESS is off: it contributes nothing to the pool.
    active = [fb for fb in events if fb.feedback_type != "LESS"]
    stats["removed"] = len(events) - len(active)

    # When the last phrase is removed, nothing stays on: the lane must not touch the pool,
    # because the base scores stand on their own. (Blank-only events are different — the
    # lane ran, nothing was ever switched off, so the scores are zeroed below.)
    if not active and stats["removed"]:
        return stats

    adjustments: Dict[str, float] = {item.url: 0.0 for item in items}
    for fb in active:
        phrase = (fb.aesthetic or "").strip()
        axis = get_aesthetic_axis(phrase)
        z_scores, missing, flat = _axis_z_scores(items, axis)
        stats["missing_vectors"] += missing
        if flat:
            logger.warning(
                "Aesthetic event skipped: phrase %r has no spread across this pool (std < %s)",
                phrase,
                traits.MIN_TRAIT_SPREAD,
            )
            stats["skipped_degenerate"] += 1
            continue
        for item in items:
            adjustments[item.url] += traits.W_AESTHETIC * z_scores.get(item.url, 0.0)
        stats["applied"] += 1

    for item in items:
        adjustment = adjustments.get(item.url, 0.0)
        clamped = max(-traits.MAX_TRAIT_ADJUSTMENT, min(traits.MAX_TRAIT_ADJUSTMENT, adjustment))
        if clamped != adjustment:
            stats["clamped"] += 1
        item.rerank_score = (item.rerank_score or 0.0) + clamped

    logger.debug(
        "Aesthetic feedback applied: %d/%d phrases, superseded=%d, removed=%d, degenerate=%d, missing_vectors=%d, clamped=%d",
        stats["applied"],
        stats["events"],
        stats["superseded"],
        stats["removed"],
        stats["skipped_degenerate"],
        stats["missing_vectors"],
        stats["clamped"],
    )
    return stats
