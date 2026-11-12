import io
import logging
import torch
import numpy as np
from PIL import Image
import cloudscraper
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoImageProcessor, AutoModel
from dtos import SearchItem
from .repository import get_upload_bytes_by_id
from model.repository.user_uploads import get_embedding_by_upload_id, insert_embedding_for_upload
from service.identifier import get_single_clip_embedding
logger = logging.getLogger(__name__)
MODEL_ID = "facebook/dinov2-base"

# Lazily loaded (on first use) so importing this module never downloads a model.
processor = None
model = None


def get_dino_processor():
    global processor
    if processor is None:
        processor = AutoImageProcessor.from_pretrained(MODEL_ID)
    return processor


def get_dino_model():
    global model
    if model is None:
        model = AutoModel.from_pretrained(MODEL_ID)
        logger.info("Initialised local DINOv2 for vector extraction")
    return model

def process_and_rank_pool(scraped_items: set[SearchItem], upload_id: int) -> list[SearchItem]:  
    try:
        anchor_features = get_embedding_by_upload_id(upload_id)
        if anchor_features is None:
            raise ValueError("missing anchor embedding")
    except Exception as e:
        anchor_bytes = get_upload_bytes_by_id(upload_id) 
        anchor_features = process_and_normalise(anchor_bytes)
        insert_embedding_for_upload(upload_id, anchor_features.squeeze().numpy().tolist())

    # `get_embedding_by_upload_id` returns a plain list; the freshly-computed path
    # returns a tensor. Normalise once so the second fetch-more page on an upload
    # does not die with "'list' object has no attribute 'numpy'".
    anchor_array = (
        anchor_features.numpy() if hasattr(anchor_features, "numpy") else np.asarray(anchor_features, dtype=float)
    ).reshape(1, -1)

    ranked_pool = set()
    for item in scraped_items:
        try:
            image = fetch_image_bytes_from_item(item)
            if image is None:
                logger.warning(f"Skipping item, image not found")
                continue

            scraped_item_features = process_and_normalise(image)
                
            # Compute pure spatial similarity matrix
            similarity = cosine_similarity(
                anchor_array, 
                scraped_item_features.numpy()
            )[0][0]

            item.similarity_score = float(similarity)
            item.embedding = (
                scraped_item_features
                    .squeeze()
                    .numpy()
                    .tolist()
            )

            # FashionCLIP vector for trait steering: computed here because the image
            # bytes are already in memory, so the feedback path never re-downloads.
            try:
                item.clip_embedding = get_single_clip_embedding(image).tolist()
            except Exception as e:
                logger.warning(f"CLIP embedding failed for {item.url}: {e}")

            ranked_pool.add(item)  
        except Exception as e:
            logger.warning(f"Skipping item due to error: {e}")
            continue

    return sorted(list(ranked_pool), key=lambda x: x.similarity_score, reverse=True)

def process_and_normalise(image_bytes) -> list:
    """Extracts DINOv2 visual features from a single image."""
    image_payload = image_bytes.getvalue() if hasattr(image_bytes, "getvalue") else image_bytes
    image = Image.open(io.BytesIO(image_payload)).convert("L").convert("RGB")
    proc = get_dino_processor()
    mdl = get_dino_model()
    inputs = proc(images=image, return_tensors="pt")
    with torch.no_grad():
        outputs = mdl(**inputs)
        features = outputs.pooler_output
        features /= features.norm(dim=-1, keepdim=True)
    return features

def fetch_image_bytes_from_item(item: SearchItem) -> bytes:
    """Fetches image bytes from a given item using cloudscraper."""
    scraper = cloudscraper.create_scraper()
    image_url = item.image_url
    if not image_url:
        logger.warning(f"No image URL found for item: {item.title}")
        return None
        
    response = scraper.get(image_url, timeout=3)
    if response.status_code != 200:
        logger.warning(f"Failed to fetch image from {image_url}, status code: {response.status_code}")
        return None
    return response.content

def fetch_image_bytes_from_url(url: str) -> bytes:
    """Fetches image bytes from a given item using cloudscraper."""
    scraper = cloudscraper.create_scraper()
        
    response = scraper.get(url, timeout=3)
    if response.status_code != 200:
        logger.warning(f"Failed to fetch image from {url}, status code: {response.status_code}")
        return None
    return response.content