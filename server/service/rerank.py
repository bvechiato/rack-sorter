import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from typing import Optional, List, Set

from model.repository.search_items import get_item_by_url
from model.repository.user_uploads import get_embedding_by_upload_id
from dtos import SearchItem, RerankFeedback


def compute_base_visual_scores(items: List[SearchItem], intent_vector: np.ndarray) -> List[SearchItem]:
    """Calculates pure spatial cosine similarities between the drift vector and DINO embeddings."""
    scored_items = []
    for item in items:
        try:
            candidate_embedding = np.array(item.embedding, dtype=float).reshape(1, -1)
            base_score = cosine_similarity(intent_vector, candidate_embedding)[0][0]
            item.rerank_score = float(base_score)
        except Exception as e:
            print(f"[WARN] Failed visual score computation for item: {item.item_url}. Error: {e}")
            item.rerank_score = 0.0
        scored_items.append(item)
    return scored_items

def apply_text_concept_modifiers(items: List[SearchItem], concept_feedback: List[RerankFeedback]) -> List[SearchItem]:
    """Scans item text data/tags and modifies scores based on explicit trait adjustments."""
    if not concept_feedback:
        return items


    for item in items:
        characteristic_modifier = 0.0
        
        for fb in concept_feedback:
            target_concept = fb.concept.lower()
            item_has_attribute = False
            
            # Match against explicit structured list characteristics
            if hasattr(item, 'characteristics') and item.characteristics:
                item_has_attribute = any(target_concept in c.lower() for c in item.characteristics)
            # Fallback string matching against text descriptions
            elif hasattr(item, 'description') and item.description:
                item_has_attribute = target_concept in item.description.lower()

            if item_has_attribute:
                if fb.feedback_type == "MORE":
                    characteristic_modifier += 0.15  # Soft boost for matching desired criteria
                elif fb.feedback_type == "LESS":
                    characteristic_modifier -= 0.35  # Heavy penalty to filter out unwanted criteria

        # Apply the textual adjustments directly on top of the visual foundation score
        item.rerank_score += characteristic_modifier
        
    return items


def rerank(previous_results: Set[SearchItem], feedback_history: List[RerankFeedback], upload_id: int) -> List[SearchItem]:
    print(f"[INFO] Running dual-engine rerank pipeline on {len(previous_results)} items.")
    
    # 1. Split the data history streams early
    image_fb = [fb for fb in feedback_history if not fb.concept]
    concept_fb = [fb for fb in feedback_history if fb.concept]

    # 2. Build the visual intent vector using visual-only interactions
    anchor_embedding = np.asarray(get_embedding_by_upload_id(upload_id), dtype=float).reshape(1, -1)
    intent_vector = build_intent_vector(anchor_embedding, image_fb)
    print(f"[SUCCESS] Intent vector created")

    # 3. Execute Engine 1: Establish our DINO baseline image similarity rankings
    items_with_base_scores = compute_base_visual_scores(list(previous_results), intent_vector)
    print(f"[SUCCESS] Generic image feedback computed")

    # 4. Execute Engine 2: Layer text rule boosts/penalties over the visual baseline
    final_ranked_items = apply_text_concept_modifiers(items_with_base_scores, concept_fb)
    print(f"[SUCCESS] Concept image feedback computed")

    # 5. Coordinate sorting positions for final delivery
    final_ranked_items.sort(key=lambda x: x.rerank_score, reverse=True)
    return final_ranked_items


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
            if feedback.feedback_type == "MORE":
                positive_embeddings.append(embedding)
            else:
                negative_embeddings.append(embedding)
        except Exception as e:
            print(f"[WARN] Error fetching embedding for vector update: {e}")

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