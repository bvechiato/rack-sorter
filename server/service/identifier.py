import io
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from service.static.CONSTANTS import CANDIDATE_TAGS, COLOUR_MAP, CATEGORY_HIERARCHY

MODEL_ID = "patrickjohncyh/fashion-clip"
model = CLIPModel.from_pretrained(MODEL_ID)
processor = CLIPProcessor.from_pretrained(MODEL_ID)
print("[SUCCESS] Initialised local CLIP model for item classification and feedback")

CONCEPT_VOCABULARY = list(dict.fromkeys(CANDIDATE_TAGS))

# 3. Pre-compute concept text embeddings once on startup using your exact tags
def precompute_concept_embeddings(concepts: list[str]) -> np.ndarray:
    print(f"[INFO] Pre-computing text embeddings for {len(concepts)} unique concept tags...")
    inputs = processor(text=concepts, return_tensors="pt", padding=True)
    with torch.no_grad():
        text_features = model.get_text_features(**inputs)
        # Normalize vectors to unit length for clean cosine similarity
        text_features /= text_features.norm(dim=-1, keepdim=True)
    return text_features.numpy()

# Global cache of concept vectors (Shape: [len(unique_tags), 512])
CACHED_CONCEPT_EMBEDDINGS = precompute_concept_embeddings(CONCEPT_VOCABULARY)

def extract_tags_from_image(image_bytes: bytes) -> dict:
    """Uses zero-shot classification to confirm item structure archetype tags."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image_greyscale = image.convert("L")

    # CLIP not that good at identifying categories, so we first identify the major category and then the sub-category
    major_cat = zero_shot_classification(image, list(CATEGORY_HIERARCHY.keys()), limit=1)["archetype"]
    sub_categories = CATEGORY_HIERARCHY.get(major_cat, ["All clothes"])
    suggested_category = zero_shot_classification(image, sub_categories, limit=1)
    
    # Use zero-shot classification to identify keywords and colours
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
    inputs = processor(text=candidate_tags, images=image, return_tensors="pt", padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
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


def get_single_clip_embedding(image_bytes: bytes) -> np.ndarray:
    """Helper to generate a clean, normalized FashionCLIP vector from image bytes."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        features = model.get_image_features(**inputs)
        features /= features.norm(dim=-1, keepdim=True)
    return features.squeeze().numpy()


def extract_relative_feedback_chips(anchor_image_bytes: bytes, clicked_item_image_bytes: bytes, top_k: int = 3) -> list[str]:
    """
    Finds concepts highly present in the clicked item but weaker or absent in the anchor.
    """
    anchor_vector = get_single_clip_embedding(anchor_image_bytes).reshape(1, -1)
    clicked_vector = get_single_clip_embedding(clicked_item_image_bytes).reshape(1, -1)
    
    # Calculate similarities to all vocabulary terms
    anchor_similarities = cosine_similarity(anchor_vector, CACHED_CONCEPT_EMBEDDINGS)[0]
    clicked_similarities = cosine_similarity(clicked_vector, CACHED_CONCEPT_EMBEDDINGS)[0]
    relative_differences = clicked_similarities - anchor_similarities
    
    ranked_indices = np.argsort(relative_differences)[::-1]
    
    dynamic_chips = []
    for idx in ranked_indices:
        if clicked_similarities[idx] > 0.18: 
            dynamic_chips.append(CONCEPT_VOCABULARY[idx])
        
        if len(dynamic_chips) >= top_k:
            break
            
    return dynamic_chips