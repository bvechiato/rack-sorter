import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from model.repository.search_items import get_item_by_url
from model.repository.user_uploads import get_embedding_by_upload_id
from dtos import SearchItem, RerankFeedback


def rerank(previous_results: set[SearchItem], feedback_history: list[RerankFeedback], upload_id: int) -> list[SearchItem]:
    print(f"[INFO] Reranking {len(previous_results)} items based on {len(feedback_history)} feedback entries.")
    anchor_embedding = np.asarray(get_embedding_by_upload_id(upload_id), dtype=float).reshape(1, -1)

    intent_vector = build_intent_vector(
        anchor_embedding,
        feedback_history
    )

    reranked = []
    try:
        for item in previous_results:
            candidate_embedding = np.array(item.embedding, dtype=float).reshape(1, -1)

            score = cosine_similarity(
                intent_vector,
                candidate_embedding
            )[0][0]

            item.rerank_score = float(score)
            reranked.append(item)
    except Exception as e:
        print(f"[WARN] Error during reranking: {e}. Returning original results.")
        return list(previous_results)

    reranked.sort(
        key=lambda x: x.rerank_score,
        reverse=True
    )

    return reranked


def build_intent_vector(anchor_embedding: np.ndarray, feedback_history: list[RerankFeedback]) -> np.ndarray:
    print(f"[INFO] Building intent vector from anchor embedding {anchor_embedding.shape[0]} and feedback entries.")

    positive_embeddings = []
    negative_embeddings = []

    try:
        for feedback in feedback_history:
            item_url = feedback.item_url
            item = get_item_by_url(item_url)

            embedding = np.array(item.embedding, dtype=float)
            feedback_type = feedback.feedback_type
            if feedback_type == "MORE":
                positive_embeddings.append(embedding)
            else:
                negative_embeddings.append(embedding)
    except Exception as e:
        print(f"[WARN] Error while building intent vector: {e}. Falling back to anchor embedding.")
        return anchor_embedding.reshape(1, -1)

    if positive_embeddings:
        intent = np.mean(positive_embeddings, axis=0)
        if negative_embeddings:
            intent -= (0.3 * np.mean(negative_embeddings, axis=0))
    else:
        intent = anchor_embedding.copy()
        if negative_embeddings:
            intent -= (0.3 * np.mean(negative_embeddings, axis=0))

    intent = intent / np.linalg.norm(intent)

    return intent.reshape(1, -1)