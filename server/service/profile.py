"""Read-only trait profile used by the debug radar.

Everything here reads stored CLIP vectors; no downloads and no writes. The profile is
expressed in *raw* axis projections plus the pool mean/spread so the client can draw
the same standardised scale the scorer uses (`z = (s - mean) / std`).
"""

from typing import Dict, Optional

import numpy as np

from model.repository.feedback import get_feedback_for_upload
from service import traits
from service.rerank import _assert_same_space, _unit, get_anchor_clip_embedding, rerank
from service.repository import get_results_by_upload_id

# Size of the "current results" polygon: the mean trait profile of the visible top.
TOP_N = 10


# Size of the "current results" polygon: the mean trait profile of the visible top.
TOP_N = 10


def build_trait_profile(upload_id: int, item_url: Optional[str] = None) -> dict:
    axes = traits.get_trait_axes()
    anchor = get_anchor_clip_embedding(upload_id)
    if anchor is None:
        raise ValueError(f"anchor CLIP embedding unavailable for upload {upload_id}")
    anchor_unit = _unit(anchor)

    # Replays the same ranking the grid is showing, so the top polygon moves when the
    # user gives feedback. Cheap once the vectors are warm (no network).
    items = get_results_by_upload_id(upload_id)
    ranked = rerank(list(items), get_feedback_for_upload(upload_id), upload_id)

    vectors: Dict[str, np.ndarray] = {}
    for item in ranked:
        vector = _unit(item.clip_embedding)
        if vector is not None:
            vectors[item.url] = vector

    if not vectors:
        raise ValueError("no candidates with CLIP vectors; run a trait rerank first")

    for url, vector in vectors.items():
        _assert_same_space(vector, axes[traits.TRAIT_KEYS[0]], url)

    scores: Dict[str, Dict[str, float]] = {}
    for key, axis in axes.items():
        scores[key] = {url: float(np.dot(vector, axis)) for url, vector in vectors.items()}

    mean = {key: float(np.mean(list(values.values()))) for key, values in scores.items()}
    std = {key: float(np.std(list(values.values()))) for key, values in scores.items()}
    anchor_scores = {key: float(np.dot(anchor_unit, axis)) for key, axis in axes.items()}

    item_scores: Optional[Dict[str, float]] = None
    if item_url and item_url in scores[traits.TRAIT_KEYS[0]]:
        item_scores = {key: scores[key][item_url] for key in axes}

    return {
        "count": len(vectors),
        "mean": mean,
        "std": std,
        "anchor": anchor_scores,
        "item": item_scores,
    }
