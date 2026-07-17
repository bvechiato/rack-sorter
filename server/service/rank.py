import io
import torch
from PIL import Image
import cloudscraper
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoImageProcessor, AutoModel
from dtos import SearchItem
from .repository import get_upload_bytes_by_id
from model.repository.user_uploads import get_embedding_by_upload_id, insert_embedding_for_upload

MODEL_ID = "facebook/dinov2-base"
processor = AutoImageProcessor.from_pretrained(MODEL_ID)
model = AutoModel.from_pretrained(MODEL_ID)
print("[SUCCESS] Initialised local DINOv2 for vector extraction")

def process_and_rank_pool(scraped_items: set[SearchItem], upload_id: int) -> list[SearchItem]:  
    try:
        anchor_features = get_embedding_by_upload_id(upload_id)
    except Exception as e:
        anchor_bytes = get_upload_bytes_by_id(upload_id) 
        anchor_features = process_and_normalise(anchor_bytes)
        insert_embedding_for_upload(upload_id, anchor_features.squeeze().numpy().tolist())

    ranked_pool = set()
    for item in scraped_items:
        try:
            image = fetch_image_bytes_from_url(item)
            if image is None:
                continue

            scraped_item_features = process_and_normalise(image)
                
            # Compute pure spatial similarity matrix
            similarity = cosine_similarity(
                anchor_features.numpy(), 
                scraped_item_features.numpy()
            )[0][0]

            item.similarity_score = float(similarity)
            item.embedding = (
                scraped_item_features
                    .squeeze()
                    .numpy()
                    .tolist()
            )
            ranked_pool.add(item)  
        except Exception as e:
            print(f"[WARN] Skipping item due to error: {e}")
            continue

    return sorted(list(ranked_pool), key=lambda x: x.similarity_score, reverse=True)

def process_and_normalise(image_bytes) -> list:
    """Extracts DINOv2 visual features from a single image."""
    image_payload = image_bytes.getvalue() if hasattr(image_bytes, "getvalue") else image_bytes
    image = Image.open(io.BytesIO(image_payload)).convert("L").convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
        features = outputs.pooler_output
        features /= features.norm(dim=-1, keepdim=True)
    return features

def fetch_image_bytes_from_url(item: SearchItem) -> bytes:
    """Fetches image bytes from a given item using cloudscraper."""
    scraper = cloudscraper.create_scraper()
    image_url = item.image_url
    if not image_url:
        print(f"[WARN] No image URL found for item: {item.title}")
        return None
        
    response = scraper.get(image_url, timeout=3)
    if response.status_code != 200:
        print(f"[WARN] Failed to fetch image from {image_url}, status code: {response.status_code}")
        return None
    return response.content