"""Rerank orchestration: blends DINO visual feedback with trait-axis steering."""

import logging
from typing import List, Set

import numpy as np

from dtos import RerankFeedback, SearchItem
from model.repository.search_items import get_item_by_url  # noqa: F401
from model.repository.user_uploads import get_embedding_by_upload_id  # noqa: F401
from service import traits
from service.aesthetic_scoring import apply_aesthetic_modifiers
from service.clip_vectors import CLIP_DIM, ensure_clip_embeddings, get_anchor_clip_embedding
from service.scoring import build_intent_vector, compute_base_visual_scores
from service.trait_scoring import (  # noqa: F401
    _assert_same_space,
    _axis_z_scores,
    _find_item,
    _unit,
    apply_trait_modifiers,
)

logger = logging.getLogger(__name__)

CLIP_DIM = CLIP_DIM


def rerank(previous_results: Set[SearchItem], feedback_history: List[RerankFeedback], upload_id: int) -> List[SearchItem]:
    logger.debug("Running dual-engine rerank pipeline on %d items.", len(previous_results))

    # Aesthetic events are absolute (they carry a phrase, not a clicked item), so they must
    # not leak into the visual lane.
    image_fb = [fb for fb in feedback_history if not fb.concept and not fb.aesthetic]
    trait_fb = [fb for fb in feedback_history if fb.concept]
    aesthetic_fb = [fb for fb in feedback_history if fb.aesthetic and not fb.concept]

    anchor_embedding = np.asarray(get_embedding_by_upload_id(upload_id), dtype=float).reshape(1, -1)
    intent_vector = build_intent_vector(anchor_embedding, image_fb)
    logger.debug("Intent vector created")
    items_with_base_scores = compute_base_visual_scores(list(previous_results), intent_vector)
    logger.debug("Generic image feedback computed")

    if trait_fb or aesthetic_fb:
        ensure_clip_embeddings(items_with_base_scores, upload_id)

    if trait_fb:
        anchor_clip = get_anchor_clip_embedding(upload_id)
        if anchor_clip is None:
            logger.warning("Trait feedback ignored: anchor CLIP embedding unavailable")
        else:
            axes = traits.get_trait_axes()
            apply_trait_modifiers(items_with_base_scores, trait_fb, anchor_clip, axes)

    if aesthetic_fb:
        apply_aesthetic_modifiers(items_with_base_scores, aesthetic_fb)

    items_with_base_scores.sort(key=lambda x: x.rerank_score, reverse=True)
    return items_with_base_scores
