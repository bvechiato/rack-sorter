import io
import logging

import cloudscraper
import numpy as np
import torch
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoImageProcessor, AutoModel

from config import DINO_MODEL_ID as MODEL_ID
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


def process_and_rank_pool(scraped_items: set[SearchItem], upload_id: int) -> list[SearchItem]:
    try:
        anchor_features = get_embedding_by_upload_id(upload_id)
        if anchor_features is None:
            raise ValueError("missing anchor embedding")
    except Exception:
        anchor_bytes = get_upload_bytes_by_id(upload_id)
        anchor_features = process_and_normalise(anchor_bytes)
        insert_embedding_for_upload(upload_id, anchor_features.squeeze().numpy().tolist())

    anchor_array = (
        anchor_features.numpy() if hasattr(anchor_features, "numpy") else np.asarray(anchor_features, dtype=float)
    ).reshape(1, -1)

    # Phase 1: download all images (sequential, to be polite to Vinted).
    downloaded: list[tuple[SearchItem, bytes]] = []
    for item in scraped_items:
        image = fetch_image_bytes_from_item(item)
        if image is None:
            logger.warning("Skipping item, image not found")
            continue
        downloaded.append((item, image))

    if not downloaded:
        return []

    ranked_pool: list[SearchItem] = []

    # Phase 2: batched DINO inference.
    proc = get_dino_processor()
    mdl = get_dino_model()
    for start in range(0, len(downloaded), BATCH_SIZE):
        batch = downloaded[start:start + BATCH_SIZE]
        images = [Image.open(io.BytesIO(blob)).convert("L").convert("RGB") for (_, blob) in batch]
        inputs = proc(images=images, return_tensors="pt")
        with torch.inference_mode():
            outputs = mdl(**inputs)
            features = outputs.pooler_output
            features = features / features.norm(dim=-1, keepdim=True)
        for i, (item, _blob) in enumerate(batch):
            feat = features[i]
            similarity = cosine_similarity(anchor_array, feat.reshape(1, -1))[0][0]
            item.similarity_score = float(similarity)
            item.embedding = feat.squeeze().numpy().tolist()
            ranked_pool.append(item)

    # Phase 3: batched CLIP inference (FashionCLIP vectors for trait steering).
    clip_proc = get_clip_processor()
    clip_model = get_clip_model()
    for start in range(0, len(downloaded), BATCH_SIZE):
        batch = downloaded[start:start + BATCH_SIZE]
        images = [Image.open(io.BytesIO(blob)).convert("RGB") for (_, blob) in batch]
        inputs = clip_proc(images=images, return_tensors="pt")
        with torch.inference_mode():
            features = clip_model.get_image_features(**inputs)
            features = features / features.norm(dim=-1, keepdim=True)
        for i, (item, _blob) in enumerate(batch):
            item.clip_embedding = features[i].squeeze().numpy().tolist()

    ranked_pool.sort(key=lambda x: x.similarity_score, reverse=True)
    return ranked_pool


def process_and_normalise(image_bytes) -> "torch.Tensor":
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
