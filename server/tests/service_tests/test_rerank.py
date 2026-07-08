import numpy as np
import service.rerank as ve


def test_build_intent_vector_with_feedback(monkeypatch):
    # anchor embedding
    anchor = np.ones(4)

    # feedback history contains two items; monkeypatch repository.get_item_by_url
    def fake_get_item_by_url(url):
        if url == 'u_pos':
            return {'embedding': [1.0, 1.0, 1.0, 1.0]}
        return {'embedding': [-1.0, -1.0, -1.0, -1.0]}

    monkeypatch.setattr(ve, 'repository', type('R', (), {'get_item_by_url': fake_get_item_by_url}))

    feedback_history = [
        {'item_url': 'u_pos', 'feedback_type': 'MORE'},
        {'item_url': 'u_neg', 'feedback_type': 'LESS'}
    ]

    intent = ve.build_intent_vector(anchor, feedback_history)
    assert intent.shape == (1, 4)


def test_rerank_simple(monkeypatch):
    # create previous_results with embeddings and similarity_score
    prev = [
        {'embedding': [1, 0, 0], 'similarity_score': 0.5},
        {'embedding': [0, 1, 0], 'similarity_score': 0.9},
    ]

    # feedback_history: keep empty so intent will be based on anchor
    feedback_history = []

    # monkeypatch build_intent_vector to return a simple vector
    monkeypatch.setattr(ve, 'build_intent_vector', lambda anchor, fb: np.array([[1.0, 0.0, 0.0]]))

    reranked = ve.rerank(prev, feedback_history)
    assert len(reranked) == 2
    # expect item with embedding [1,0,0] to score higher
    assert reranked[0]['embedding'] == [1, 0, 0]

def test_rerank_with_feedback_history(monkeypatch):
    items = [
        {'title': 'a', 'url': 'u1', 'image_url': 'i1', 'embedding': [1.0, 0.0, 0.0], 'similarity_score': 0.5},
        {'title': 'b', 'url': 'u2', 'image_url': 'i2', 'embedding': [0.0, 1.0, 0.0], 'similarity_score': 0.9},
    ]

    feedback_history = [
        ve.RerankFeedback(item_url='u1', feedback_type='MORE')
    ]

    # patch repository.get_item_by_url to return object-like structure
    class FakeItem:
        def __init__(self, embedding):
            self.embedding = embedding

    monkeypatch.setattr(ve, 'get_item_by_url', lambda url: FakeItem([1.0, 0.0, 0.0]))

    reranked = ve.rerank(items, feedback_history)

    assert reranked[0]['url'] == 'u1'
    assert reranked[0]['rerank_score'] >= reranked[1]['rerank_score']