import repository.feedback as fb
import service.repository as repo
import service.vector_engine as ve


def test_rerank_with_feedback_history(monkeypatch):
    items = [
        {'title': 'a', 'url': 'u1', 'image_url': 'i1', 'embedding': [1.0, 0.0, 0.0], 'similarity_score': 0.5},
        {'title': 'b', 'url': 'u2', 'image_url': 'i2', 'embedding': [0.0, 1.0, 0.0], 'similarity_score': 0.9},
    ]

    feedback_history = [
        fb.RerankFeedback(item_url='u1', feedback_type='MORE')
    ]

    # patch repository.get_item_by_url to return object-like structure
    class FakeItem:
        def __init__(self, embedding):
            self.embedding = embedding

    monkeypatch.setattr(ve, 'get_item_by_url', lambda url: FakeItem([1.0, 0.0, 0.0]))

    reranked = ve.rerank(items, feedback_history)

    assert reranked[0]['url'] == 'u1'
    assert reranked[0]['rerank_score'] >= reranked[1]['rerank_score']
