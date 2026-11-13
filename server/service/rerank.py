"""Rerank orchestration: blends DINO visual feedback with trait-axis steering."""

import logging
from typing import List, Optional, Set

import numpy as np

from dtos import SearchItem, RerankFeedback
from model.repository.search_items import get_item_by_url
from model.repository.user_uploads import get_embedding_by_upload_id
from service import traits
from service.clip_vectors import CLIP_DIM, ensure_clip_embeddings, get_anchor_clip_embedding
from service.scoring import DINO_DIM, build_intent_vector, compute_base_visual_scores
from service.trait_scoring import (
    _assert_same_space,
    _axis_z_scores,
    _find_item,
    _unit,
    apply_trait_modifiers,
)

logger = logging.getLogger(__name__)

CLIP_DIM = CLIP_DIM


def rerank(previous_results: Set[SearchItem], feedback_history: List[RerankFeedback], upload_id: int) -> List[SearchItem]:
    logger.info("Running dual-engine rerank pipeline on %d items.", len(previous_results))

    image_fb = [fb for fb in feedback_history if not fb.concept]
    trait_fb = [fb for fb in feedback_history if fb.concept]

    anchor_embedding = np.asarray(get_embedding_by_upload_id(upload_id), dtype=float).reshape(1, -1)
    intent_vector = build_intent_vector(anchor_embedding, image_fb)
    logger.info("Intent vector created")
    items_with_base_scores = compute_base_visual_scores(list(previous_results), intent_vector)
    logger.info("Generic image feedback computed")

    if trait_fb:
        anchor_clip = get_anchor_clip_embedding(upload_id)
        if anchor_clip is None:
            logger.warning("Trait feedback ignored: anchor CLIP embedding unavailable")
        else:
            ensure_clip_embeddings(items_with_base_scores, upload_id)
            axes = traits.get_trait_axes()
            stats = apply_trait_modifiers(items_with_base_scores, trait_fb, anchor_clip, axes)
            logger.info(
                "Trait feedback applied: %d/%d events, superseded=%d, degenerate=%d, "
                "missing_clicked=%d, items_without_vector=%d, clamped=%d",
                stats["applied"], stats["events"], stats["superseded"], stats["skipped_degenerate"],
                stats["skipped_missing_vector"], stats["missing_vectors"], stats["clamped"],
            )

    items_with_base_scores.sort(key=lambda x: x.rerank_score, reverse=True)
    return items_with_base_scores
