from dataclasses import dataclass

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

import repository.search_items as repository


get_item_by_url = repository.get_item_by_url


@dataclass
class RerankFeedback:
    item_url: str
    feedback_type: str


def _get_item_embedding(item):
    if isinstance(item, dict):
        return item.get("embedding")
    return getattr(item, "embedding", None)


DEFAULT_GET_ITEM_BY_URL = repository.get_item_by_url


def _get_item_by_url(url):
    patched_getter = globals().get("get_item_by_url")
    if callable(patched_getter) and patched_getter is not DEFAULT_GET_ITEM_BY_URL:
        return patched_getter(url)

    repository_lookup = globals().get("repository")
    if repository_lookup is not None and hasattr(repository_lookup, "get_item_by_url"):
        return repository_lookup.get_item_by_url(url)

    return DEFAULT_GET_ITEM_BY_URL(url)


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


def build_intent_vector(anchor_embedding, feedback_history):
    positive_embeddings = []
    negative_embeddings = []

    for feedback in feedback_history:
        item_url = feedback.item_url if hasattr(feedback, "item_url") else feedback["item_url"]
        item = _get_item_by_url(item_url)

        embedding = np.array(item.embedding if hasattr(item, "embedding") else item["embedding"])
        feedback_type = feedback.feedback_type if hasattr(feedback, "feedback_type") else feedback["feedback_type"]

        if feedback_type == "MORE":
            positive_embeddings.append(embedding)
        else:
            negative_embeddings.append(embedding)

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