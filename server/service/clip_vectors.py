"""FashionCLIP vector lifecycle: anchor cache and lazy candidate backfill."""

import logging
import threading

import numpy as np

from dtos import SearchItem

logger = logging.getLogger(__name__)

CLIP_DIM = 512

_anchor_cache: dict[int, np.ndarray] = {}
_locks: dict[int, threading.Lock] = {}
_locks_guard = threading.Lock()


def _lock_for(key: int) -> threading.Lock:
    with _locks_guard:
        return _locks.setdefault(key, threading.Lock())


def get_anchor_clip_embedding(upload_id: int):
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
        logger.warning("Could not compute anchor CLIP embedding for upload %d: %s", upload_id, e)
        return None


def ensure_clip_embeddings(items, upload_id: int):
    """Lazily encode `clip_embedding` for candidates that predate the column.

    Returns `(encoded, failed)`. Guarded by a per-upload lock.
    """
    if all(getattr(item, "clip_embedding", None) is not None for item in items):
        return 0, 0

    encoded = 0
    failed = 0
    with _lock_for(upload_id):
        for item in items:
            if getattr(item, "clip_embedding", None) is not None:
                continue
            try:
                vector = _encode_candidate(item)
                item.clip_embedding = vector.tolist()
                from model.repository.search_items import update_item_clip_embedding

                update_item_clip_embedding(item.url, item.clip_embedding)
                encoded += 1
            except Exception as e:
                failed += 1
                logger.warning("CLIP backfill failed for %s: %s", item.url, e)

    if encoded or failed:
        logger.info("Lazy CLIP backfill for upload %d: %d encoded, %d failed", upload_id, encoded, failed)
    return encoded, failed


def _encode_candidate(item: SearchItem) -> np.ndarray:
    from service.identifier import get_single_clip_embedding
    from service.rank import fetch_image_bytes_from_url

    if not getattr(item, "image_url", None):
        raise ValueError("missing image_url")
    image_bytes = fetch_image_bytes_from_url(item.image_url)
    if image_bytes is None:
        raise ValueError("image download failed")

    vector = get_single_clip_embedding(image_bytes)
    if vector.shape != (CLIP_DIM,):
        raise ValueError(f"expected {CLIP_DIM}-d CLIP vector, got {vector.shape}")
    return vector
