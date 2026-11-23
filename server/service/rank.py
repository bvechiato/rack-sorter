import io
import logging

import cloudscraper
import numpy as np
import torch
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoImageProcessor, AutoModel

from config import DINO_MODEL_ID as MODEL_ID
from config import SAVE_UPLOAD_IMAGES
from dtos import SearchItem
from model.repository.user_uploads import get_embedding_by_upload_id, insert_embedding_for_upload

from .repository import get_upload_bytes_by_id

logger = logging.getLogger(__name__)

# Lazily loaded (on first use) so importing this module never downloads a model.
processor = None
model = None

BATCH_SIZE = 16


def get_dino_processor():
    global processor
    if processor is None:
        processor = AutoImageProcessor.from_pretrained(MODEL_ID)
    return processor


def get_dino_model():
    global model
    if model is None:
        model = AutoModel.from_pretrained(MODEL_ID)
        model.eval()
        logger.debug("Initialised local DINOv2 for vector extraction")
    return model


def get_clip_processor():
    from service.identifier import get_clip_processor as _get
    return _get()


def get_clip_model():
    from service.identifier import get_clip_model as _get
    return _get()


def _anchor_array(upload_id: int) -> np.ndarray:
    """Load (or compute) the anchor DINO embedding and return it as a 2-D array."""
    try:
        anchor_features = get_embedding_by_upload_id(upload_id)
        if anchor_features is None:
            raise ValueError("missing anchor embedding")
    except Exception:
        if not SAVE_UPLOAD_IMAGES:
            raise  # no image file in prod; the stored vector is the only source
        # Legacy dev rows created before vectors were stored at upload time.
        anchor_bytes = get_upload_bytes_by_id(upload_id)
        anchor_features = process_and_normalise(anchor_bytes)
        insert_embedding_for_upload(upload_id, anchor_features.squeeze().numpy().tolist())
    arr = anchor_features.numpy() if hasattr(anchor_features, "numpy") else np.asarray(anchor_features, dtype=float)
    return arr.reshape(1, -1)


def _download_images(scraped_items):
    """Fetch image bytes for every item; skip items whose download fails."""
    downloaded = []
    for item in scraped_items:
        image = fetch_image_bytes_from_item(item)
        if image is None:
            logger.warning("Skipping item, image not found")
            continue
        downloaded.append((item, image))
    return downloaded


def _run_dino(downloaded, anchor_array):
    """Batched DINO inference: sets similarity_score and embedding on each item.

    Returns the list of items that were successfully scored.
    """
    proc = get_dino_processor()
    mdl = get_dino_model()
    successful = []
    for start in range(0, len(downloaded), BATCH_SIZE):
        batch = downloaded[start:start + BATCH_SIZE]
        try:
            images = [Image.open(io.BytesIO(blob)).convert("L").convert("RGB") for (_, blob) in batch]
            inputs = proc(images=images, return_tensors="pt")
            with torch.inference_mode():
                outputs = mdl(**inputs)
                features = outputs.pooler_output
                features = features / features.norm(dim=-1, keepdim=True)
            for i, (item, _blob) in enumerate(batch):
                feat = features[i]
                item.similarity_score = float(cosine_similarity(anchor_array, feat.reshape(1, -1))[0][0])
                item.embedding = feat.squeeze().numpy().tolist()
                successful.append(item)
        except Exception as e:
            logger.warning("DINO batch failed: %s", e)
    return successful


def _run_clip(successful, downloaded):
    """Batched FashionCLIP inference: sets clip_embedding on each item."""
    by_item = {item: blob for item, blob in downloaded}
    proc = get_clip_processor()
    model = get_clip_model()
    items = successful
    for start in range(0, len(items), BATCH_SIZE):
        batch_items = items[start:start + BATCH_SIZE]
        batch = [(it, by_item[it]) for it in batch_items]
        images = [Image.open(io.BytesIO(blob)).convert("RGB") for (_, blob) in batch]
        inputs = proc(images=images, return_tensors="pt")
        with torch.inference_mode():
            features = model.get_image_features(**inputs)
            features = features / features.norm(dim=-1, keepdim=True)
        for i, (item, _blob) in enumerate(batch):
            item.clip_embedding = features[i].squeeze().numpy().tolist()


def process_and_rank_pool(scraped_items: set[SearchItem], upload_id: int) -> list[SearchItem]:
    anchor_array = _anchor_array(upload_id)

    downloaded = _download_images(scraped_items)
    if not downloaded:
        return []

    ranked_pool = _run_dino(downloaded, anchor_array)
    _run_clip(ranked_pool, downloaded)

    ranked_pool.sort(key=lambda x: x.similarity_score, reverse=True)
    return ranked_pool


def process_and_normalise(image_bytes):
    """Extracts DINOv2 visual features from a single image (used for the anchor)."""
    image_payload = image_bytes.getvalue() if hasattr(image_bytes, "getvalue") else image_bytes
    image = Image.open(io.BytesIO(image_payload)).convert("L").convert("RGB")
    proc = get_dino_processor()
    mdl = get_dino_model()
    inputs = proc(images=image, return_tensors="pt")
    with torch.inference_mode():
        outputs = mdl(**inputs)
        features = outputs.pooler_output
        features = features / features.norm(dim=-1, keepdim=True)
    return features


def fetch_image_bytes_from_item(item: SearchItem) -> bytes:
    """Fetches image bytes from a given item using cloudscraper."""
    scraper = cloudscraper.create_scraper()
    image_url = item.image_url
    if not image_url:
        logger.warning("No image URL found for item: %s", item.title)
        return None

    response = scraper.get(image_url, timeout=3)
    if response.status_code != 200:
        logger.warning("Failed to fetch image from %s, status code: %s", image_url, response.status_code)
        return None
    return response.content


def fetch_image_bytes_from_url(url: str) -> bytes:
    """Fetches image bytes from a given item using cloudscraper."""
    scraper = cloudscraper.create_scraper()

    response = scraper.get(url, timeout=3)
    if response.status_code != 200:
        logger.warning("Failed to fetch image from %s, status code: %s", url, response.status_code)
        return None
    return response.content
