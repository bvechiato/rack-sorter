import io
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from curl_cffi import requests
from service.static.CONSTANTS import CANDIDATE_TAGS, COLOUR_MAP, CATEGORY_HIERARCHY

print("Initializing local CLIP visual model architecture...")
MODEL_ID = "openai/clip-vit-base-patch32"
model = CLIPModel.from_pretrained(MODEL_ID)
processor = CLIPProcessor.from_pretrained(MODEL_ID)
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

def rank_pool_by_sliders(pool_data: list, parsed_weights: dict) -> list:
    """Applies multi-vector weighting profiles to re-order scraped listings."""
    if not pool_data:
        return []
        
    words = list(parsed_weights.keys())
    scalar_values = list(parsed_weights.values())
    
    # 1. Compute unified multi-modal query target vector
    text_inputs = processor(text=words, return_tensors="pt", padding=True)
    with torch.no_grad():
        text_features = model.get_text_features(**text_inputs)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
    weight_tensor = torch.tensor(scalar_values, dtype=torch.float32).unsqueeze(1)
    weighted_query_vector = (text_features * weight_tensor).sum(dim=0, keepdim=True)
    weighted_query_vector = weighted_query_vector / weighted_query_vector.norm(dim=-1, keepdim=True)

    # 2. Iterate and image-embed the active sandbox pool items
    valid_items = []
    image_tensors = []
    
    for item in pool_data:
        try:
            img_res = requests.get(item["image_url"], timeout=3, impersonate="chrome124")
            if img_res.status_code == 200:
                img_obj = Image.open(io.BytesIO(img_res.content)).convert("RGB")
                valid_items.append(item)
                
                img_input = processor(images=img_obj, return_tensors="pt")
                with torch.no_grad():
                    img_feat = model.get_image_features(**img_input)
                    img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)
                    image_tensors.append(img_feat)
        except:
            continue # Pass over corrupted image paths dynamically

    if not image_tensors:
        return pool_data

    # 3. Complete scoring using dot-product matrix operations
    stacked_images = torch.cat(image_tensors, dim=0)
    similarity_scores = torch.matmul(weighted_query_vector, stacked_images.T).squeeze(0).numpy()
    
    ranked_records = []
    for idx, score in enumerate(similarity_scores):
        item = valid_items[idx]
        item["score"] = float(score)
        ranked_records.append(item)
        
    return sorted(ranked_records, key=lambda x: x["score"], reverse=True)