"""DINO-based visual scoring and intent-vector construction."""

import logging

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

DINO_DIM = 768


def compute_base_visual_scores(items, intent_vector):
    """Calculates pure spatial cosine similarities between the drift vector and DINO embeddings."""
    scored_items = []
    for item in items:
        try:
            if item.embedding is None:
                raise ValueError("missing DINO embedding")
            candidate_embedding = np.asarray(item.embedding, dtype=float).reshape(1, -1)
            base_score = cosine_similarity(intent_vector, candidate_embedding)[0][0]
            item.rerank_score = float(base_score)
        except Exception as e:
            logger.warning("Failed visual score computation for item: %s. Error: %s", item.url, e)
            item.rerank_score = 0.0
        scored_items.append(item)
    return scored_items


def build_intent_vector(anchor_embedding, image_feedback):
    """Computes the visual center of mass over raw DINO space."""
    if not image_feedback:
        return anchor_embedding.reshape(1, -1)

    positive_embeddings = []
    negative_embeddings = []

    for feedback in image_feedback:
        try:
            import service.rerank as _rerank_mod

            item = _rerank_mod.get_item_by_url(feedback.item_url)
            embedding = np.array(item.embedding, dtype=float)
            if embedding.shape != (DINO_DIM,):
                raise ValueError(f"expected {DINO_DIM}-d DINO vector, got {embedding.shape}")
            if feedback.feedback_type == "MORE":
                positive_embeddings.append(embedding)
            else:
                negative_embeddings.append(embedding)
        except Exception as e:
            logger.warning("Error fetching embedding for vector update: %s", e)

    if positive_embeddings:
        intent = np.mean(positive_embeddings, axis=0)
        if negative_embeddings:
            intent -= 0.3 * np.mean(negative_embeddings, axis=0)
    else:
        intent = anchor_embedding.copy()
        if negative_embeddings:
            intent -= 0.3 * np.mean(negative_embeddings, axis=0)

    norm = np.linalg.norm(intent)
    if norm > 0:
        intent = intent / norm

    return intent.reshape(1, -1)
