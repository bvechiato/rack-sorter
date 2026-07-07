import io
import torch
from PIL import Image
import cloudscraper
from sklearn.metrics.pairwise import cosine_similarity
from transformers import CLIPProcessor, CLIPModel
from transformers import AutoImageProcessor, AutoModel
from repository.search_items import get_item_by_url
from service.static.CONSTANTS import CANDIDATE_TAGS, COLOUR_MAP, CATEGORY_HIERARCHY
import numpy as np

print("Initializing local CLIP visual model architecture...")
MODEL_ID = "facebook/dinov2-base"
processor = AutoImageProcessor.from_pretrained(MODEL_ID)
model = AutoModel.from_pretrained(MODEL_ID)

clip_model_id = "patrickjohncyh/fashion-clip"
clip_model = CLIPModel.from_pretrained(clip_model_id)
clip_processor = CLIPProcessor.from_pretrained(clip_model_id)
print("Model vectors staged in RAM successfully.")

def extract_tags_from_image(image_bytes: bytes) -> dict:
    """Uses zero-shot classification to confirm item structure archetype tags."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image_greyscale = image.convert("L")

    major_cat = zero_shot_classification(image, list(CATEGORY_HIERARCHY.keys()), limit=1)["archetype"]
    sub_categories = CATEGORY_HIERARCHY.get(major_cat, ["All clothes"])
    suggested_category = zero_shot_classification(image, sub_categories, limit=1)
    
    suggested_tags = zero_shot_classification(image_greyscale, CANDIDATE_TAGS)
    suggested_colours = zero_shot_classification(image, list(COLOUR_MAP.keys()), limit=3)
    return {
        "archetype": suggested_tags["archetype"],
        "classified_tags": suggested_tags["classified_tags"],
        "colour_archetype": suggested_colours["archetype"],
        "colour_classified_tags": suggested_colours["classified_tags"],
        "category_archetype": suggested_category["archetype"]
    }

def zero_shot_classification(image: Image, candidate_tags: list[str], limit: int = 5) -> dict:
    inputs = clip_processor(text=candidate_tags, images=image, return_tensors="pt", padding=True)
    with torch.no_grad():
        outputs = clip_model(**inputs)
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=-1).numpy()[0]
        
    sorted_pairs = sorted(zip(candidate_tags, probs), key=lambda x: x[1], reverse=True)

    # Filter: Keep only those above threshold
    filtered_pairs = [pair for pair in sorted_pairs if pair[1] >= 0.1]
    
    # Take up to 'limit' after filtering
    final_tags = filtered_pairs[:limit]
    
    return {
        "archetype": final_tags[0][0] if final_tags else sorted_pairs[0][0],
        "classified_tags": [pair[0] for pair in final_tags]
    }

def process_and_rank_pool(scraped_items: list, anchor_image_bytes: bytes) -> list:
    scraper = cloudscraper.create_scraper()
    
    # 1. Process Anchor Image: Convert to Grayscale to neutralize color
    anchor_image = Image.open(io.BytesIO(anchor_image_bytes)).convert("L").convert("RGB")
    
    # 2. Extract DINOv2 Visual Features for the Anchor
    anchor_inputs = processor(images=anchor_image, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**anchor_inputs)
        # DINOv2 pooler_output gives a unified 768-dimensional visual feature vector
        anchor_features = outputs.pooler_output
        
    # Normalise the anchor vector
    anchor_features /= anchor_features.norm(dim=-1, keepdim=True)
    
    ranked_pool = []
    
    # 3. Process the Scraped Pool
    for item in scraped_items:
        try:
            image_url = item.get("image_url")
            if not image_url:
                continue
                
            response = scraper.get(image_url, timeout=3)
            if response.status_code != 200:
                continue
                
            # Process Vinted listing: Force Grayscale to match anchor context
            item_image = Image.open(io.BytesIO(response.content)).convert("L").convert("RGB")
            
            # Extract DINOv2 features for the Vinted listing
            item_inputs = processor(images=item_image, return_tensors="pt")
            with torch.no_grad():
                item_outputs = model(**item_inputs)
                item_features = item_outputs.pooler_output
                
            # Normalise item vector
            item_features /= item_features.norm(dim=-1, keepdim=True)
                
            # Compute pure spatial similarity matrix
            similarity = cosine_similarity(
                anchor_features.numpy(), 
                item_features.numpy()
            )[0][0]
            
            item["similarity_score"] = float(similarity)
            item["embedding"] = (
                item_features
                    .squeeze()
                    .numpy()
                    .tolist()
            )
            ranked_pool.append(item)
            
        except Exception as e:
            print(f"[WARN] Skipping item due to error: {e}")
            continue

    # Sort best geometric matches to the top
    ranked_pool.sort(key=lambda x: x["similarity_score"], reverse=True)
    return ranked_pool

def _get_item_embedding(item):
    if isinstance(item, dict):
        return item.get("embedding")
    return getattr(item, "embedding", None)


def rerank(previous_results, feedback_history):
    print(f"[INFO] Reranking {len(previous_results)} items based on {len(feedback_history)} feedback entries.")
    anchor_item = max(
        previous_results,
        key=lambda x: x["similarity_score"] if isinstance(x, dict) else x.similarity_score
    )

    anchor_embedding = np.array(_get_item_embedding(anchor_item))

    intent_vector = build_intent_vector(
        anchor_embedding,
        feedback_history
    )

    reranked = []

    for item in previous_results:
        candidate_embedding = np.array(
            _get_item_embedding(item)
        ).reshape(1, -1)

        score = cosine_similarity(
            intent_vector,
            candidate_embedding
        )[0][0]

        if isinstance(item, dict):
            item["rerank_score"] = float(score)
        else:
            setattr(item, "rerank_score", float(score))

        reranked.append(item)

    reranked.sort(
        key=lambda x: x["rerank_score"] if isinstance(x, dict) else x.rerank_score,
        reverse=True
    )

    return reranked

def get_embedding(image_bytes: bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("L").convert("RGB")

    inputs = processor(images=image, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
        embedding = outputs.pooler_output

    embedding /= embedding.norm(dim=-1, keepdim=True)

    return embedding.numpy()

def get_image_embedding_from_url(image_url: str):
    scraper = cloudscraper.create_scraper()

    response = scraper.get(image_url, timeout=3)
    response.raise_for_status()

    return get_embedding(response.content)

def build_intent_vector(anchor_embedding, feedback_history):
    positive_embeddings = []
    negative_embeddings = []

    for feedback in feedback_history:
        item_url = feedback.item_url if hasattr(feedback, "item_url") else feedback["item_url"]
        item = get_item_by_url(item_url)

        embedding = np.array(item.embedding if hasattr(item, "embedding") else item["embedding"])
        feedback_type = feedback.feedback_type if hasattr(feedback, "feedback_type") else feedback["feedback_type"]

        if feedback_type == "MORE":
            positive_embeddings.append(embedding)
        else:
            negative_embeddings.append(embedding)

    intent = anchor_embedding.copy()

    if positive_embeddings:
        intent += (0.3 * np.mean(positive_embeddings, axis=0))

    if negative_embeddings:
        intent -= (0.2 * np.mean(negative_embeddings, axis=0))

    intent = intent / np.linalg.norm(intent)

    return intent.reshape(1, -1)