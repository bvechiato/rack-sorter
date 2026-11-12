import threading
import logging
from typing import Dict, List, Optional, Sequence, Set, Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from model.repository.search_items import get_item_by_url, update_item_clip_embedding
from model.repository.user_uploads import get_embedding_by_upload_id
from dtos import SearchItem, RerankFeedback
from service import traits
logger = logging.getLogger(__name__)

CLIP_DIM = 512
DINO_DIM = 768

# Stats for one rerank call; logged so a no-op is never silent.
TraitScoringStats = Dict[str, int]


def compute_base_visual_scores(items: List[SearchItem], intent_vector: np.ndarray) -> List[SearchItem]:
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
            logger.warning(f"Failed visual score computation for item: {item.url}. Error: {e}")
            item.rerank_score = 0.0
        scored_items.append(item)
    return scored_items


def apply_trait_modifiers(
    items: Sequence[SearchItem],
    trait_feedback: Sequence[RerankFeedback],
    anchor_clip: np.ndarray,
    axes: Dict[str, np.ndarray],
) -> TraitScoringStats:
    """Fold trait feedback onto the CLIP projection of every candidate.

    Pure with respect to I/O: it only reads `item.clip_embedding` and writes
    `item.rerank_score`, which keeps it directly testable with synthetic vectors.
    """
    stats: TraitScoringStats = {
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

    # The history is append-only, so switching a trait from + to − would otherwise
    # partially cancel out. Keep only the last choice per (clicked item, trait) so
    # the ranking reflects what the user currently means.
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
    # Standardised projections are per axis, so several taps on the same trait reuse one
    # pass over the pool. `None` caches a degenerate (flat) axis so it is not recomputed.
    z_cache: Dict[str, Optional[Dict[str, float]]] = {}

    for fb in events:
        key = (fb.concept or "").strip().lower()
        axis = axes.get(key)
        if axis is None:
            logger.warning(f"Unknown trait concept '{fb.concept}' ignored; expected one of {list(axes)}")
            continue
        if fb.feedback_type not in ("MORE", "LESS"):
            logger.warning(f"Unknown feedback type '{fb.feedback_type}' ignored")
            continue

        clicked = _find_item(items, fb.item_url)
        clicked_clip = _unit(clicked.clip_embedding) if clicked is not None else None
        if clicked_clip is None:
            logger.warning(f"Cross-sell trait event skipped: no CLIP vector for clicked item {fb.item_url}")
            stats["skipped_missing_vector"] += 1
            continue
        _assert_same_space(clicked_clip, axis, fb.item_url)

        # Direction of the *clicked* item on this trait, relative to the anchor. A
        # neutral click (delta == 0) still counts: it is treated as the positive
        # direction rather than dropped, so every tap has an effect.
        projection_delta = float(np.dot(clicked_clip - anchor_unit, axis))

        if key in z_cache:
            z_scores = z_cache[key]
        else:
            z_scores, missing, flat = _axis_z_scores(items, axis)
            z_cache[key] = z_scores
            stats["missing_vectors"] += missing
            if flat:
                logger.warning(
                    f"Trait event skipped: axis '{key}' has no spread across this pool "
                    f"(std < {traits.MIN_TRAIT_SPREAD}); cannot standardise the projection"
                )
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

    return stats


def rerank(previous_results: Set[SearchItem], feedback_history: List[RerankFeedback], upload_id: int) -> List[SearchItem]:
    logger.info(f"Running dual-engine rerank pipeline on {len(previous_results)} items.")

    # 1. Split the data history streams early
    image_fb = [fb for fb in feedback_history if not fb.concept]
    trait_fb = [fb for fb in feedback_history if fb.concept]

    # 2. Build the visual intent vector using visual-only interactions
    anchor_embedding = np.asarray(get_embedding_by_upload_id(upload_id), dtype=float).reshape(1, -1)
    intent_vector = build_intent_vector(anchor_embedding, image_fb)
    logger.info(f"Intent vector created")

    # 3. Execute Engine 1: Establish our DINO baseline image similarity rankings
    items_with_base_scores = compute_base_visual_scores(list(previous_results), intent_vector)
    logger.info(f"Generic image feedback computed")

    # 4. Execute Engine 2: Layer trait-axis adjustments over the visual baseline
    if trait_fb:
        anchor_clip = get_anchor_clip_embedding(upload_id)
        if anchor_clip is None:
            logger.warning("Trait feedback ignored: anchor CLIP embedding unavailable")
        else:
            ensure_clip_embeddings(items_with_base_scores, upload_id)
            axes = traits.get_trait_axes()
            stats = apply_trait_modifiers(items_with_base_scores, trait_fb, anchor_clip, axes)
            logger.info(
                f"Trait feedback applied: {stats['applied']}/{stats['events']} events, "
                f"superseded={stats['superseded']}, "
                f"degenerate={stats['skipped_degenerate']}, "
                f"missing_clicked={stats['skipped_missing_vector']}, "
                f"items_without_vector={stats['missing_vectors']}, clamped={stats['clamped']}"
            )

    # 5. Coordinate sorting positions for final delivery
    items_with_base_scores.sort(key=lambda x: x.rerank_score, reverse=True)
    return items_with_base_scores


def build_intent_vector(anchor_embedding: np.ndarray, image_feedback: List[RerankFeedback]) -> np.ndarray:
    """Computes the visual center of mass over raw DINO space."""
    if not image_feedback:
        return anchor_embedding.reshape(1, -1)

    positive_embeddings = []
    negative_embeddings = []

    for feedback in image_feedback:
        try:
            item = get_item_by_url(feedback.item_url)
            embedding = np.array(item.embedding, dtype=float)
            if embedding.shape != (DINO_DIM,):
                raise ValueError(f"expected {DINO_DIM}-d DINO vector, got {embedding.shape}")
            if feedback.feedback_type == "MORE":
                positive_embeddings.append(embedding)
            else:
                negative_embeddings.append(embedding)
        except Exception as e:
            logger.warning(f"Error fetching embedding for vector update: {e}")

    if positive_embeddings:
        intent = np.mean(positive_embeddings, axis=0)
        if negative_embeddings:
            intent -= (0.3 * np.mean(negative_embeddings, axis=0))
    else:
        intent = anchor_embedding.copy()
        if negative_embeddings:
            intent -= (0.3 * np.mean(negative_embeddings, axis=0))

    norm = np.linalg.norm(intent)
    if norm > 0:
        intent = intent / norm

    return intent.reshape(1, -1)


# ---------------------------------------------------------------------------
# CLIP vector lifecycle
# ---------------------------------------------------------------------------

_anchor_cache: Dict[int, np.ndarray] = {}
_locks: Dict[int, threading.Lock] = {}
_locks_guard = threading.Lock()


def _lock_for(key: int) -> threading.Lock:
    with _locks_guard:
        return _locks.setdefault(key, threading.Lock())


def get_anchor_clip_embedding(upload_id: int) -> Optional[np.ndarray]:
    """512-d CLIP embedding of the uploaded anchor image, cached per upload."""
    if upload_id in _anchor_cache:
        return _anchor_cache[upload_id]

    try:
        from service.identifier import get_single_clip_embedding
        from service.repository import get_upload_bytes_by_id

        vector = get_single_clip_embedding(get_upload_bytes_by_id(upload_id))
        if vector.shape != (CLIP_DIM,):
            raise ValueError(f"expected {CLIP_DIM}-d CLIP vector, got {vector.shape}")
        _anchor_cache[upload_id] = vector
        return vector
    except Exception as e:
        logger.warning(f"Could not compute anchor CLIP embedding for upload {upload_id}: {e}")
        return None


def ensure_clip_embeddings(items: Sequence[SearchItem], upload_id: int) -> Tuple[int, int]:
    """Lazily encode `clip_embedding` for candidates that predate the column.

    Returns `(encoded, failed)`. Guarded by a per-upload lock so concurrent reranks
    cannot encode the same pool twice.
    """
    if all(item.clip_embedding is not None for item in items):
        return 0, 0

    encoded = 0
    failed = 0
    with _lock_for(upload_id):
        for item in items:
            if item.clip_embedding is not None:
                continue
            try:
                vector = _encode_candidate(item)
                item.clip_embedding = vector.tolist()
                update_item_clip_embedding(item.url, item.clip_embedding)
                encoded += 1
            except Exception as e:
                failed += 1
                logger.warning(f"CLIP backfill failed for {item.url}: {e}")

    if encoded or failed:
        logger.info(f"Lazy CLIP backfill for upload {upload_id}: {encoded} encoded, {failed} failed")
    return encoded, failed


def _encode_candidate(item: SearchItem) -> np.ndarray:
    from service.identifier import get_single_clip_embedding
    from service.rank import fetch_image_bytes_from_url

    if not item.image_url:
        raise ValueError("missing image_url")
    image_bytes = fetch_image_bytes_from_url(item.image_url)
    if image_bytes is None:
        raise ValueError("image download failed")

    vector = get_single_clip_embedding(image_bytes)
    if vector.shape != (CLIP_DIM,):
        raise ValueError(f"expected {CLIP_DIM}-d CLIP vector, got {vector.shape}")
    return vector


def _axis_z_scores(items: Sequence[SearchItem], axis: np.ndarray) -> Tuple[Optional[Dict[str, float]], int, bool]:
    """Standardised projection of every candidate onto one trait axis.

    Returns `(z_by_url, missing_vectors, flat)`. `flat` means the pool has no meaningful
    spread on this axis, in which case `z_by_url` is `None`: applying a direction there
    would sort on noise. Items without a CLIP vector are omitted (and counted) so they
    contribute 0 instead of crashing the request.
    """
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


def _assert_same_space(vector: np.ndarray, axis: np.ndarray, label: str) -> None:
    """Fail loudly on a DINO/CLIP mix-up instead of letting dot() raise somewhere opaque."""
    if vector.shape != axis.shape:
        raise ValueError(
            f"Trait vector dimension mismatch for {label}: candidate={vector.shape}, "
            f"axis={axis.shape}. Candidates must store a {CLIP_DIM}-d FashionCLIP vector; "
            f"a {DINO_DIM}-d value means the DINO embedding was passed by mistake."
        )


def _find_item(items: Sequence[SearchItem], url: str) -> Optional[SearchItem]:
    for item in items:
        if item.url == url:
            return item
    return None


def _unit(vector: Optional[Sequence[float]]) -> Optional[np.ndarray]:
    if vector is None:
        return None
    array = np.asarray(vector, dtype=float).reshape(-1)
    norm = np.linalg.norm(array)
    if norm == 0:
        return None
    return array / norm
