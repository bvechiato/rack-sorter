"""HTTP-layer smoke tests for the FastAPI app.

These complement the pure service tests by exercising routing, validation and
the liveness probe. They do not scrape Vinted or load ML models.
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_requires_a_file():
    response = client.post("/analyze")
    assert response.status_code == 422


def test_fetch_initial_validates_required_fields():
    response = client.post("/fetch_initial", json={})
    assert response.status_code == 422


def test_rerank_validates_required_fields():
    response = client.post("/rerank", json={})
    assert response.status_code == 422


def test_rerank_batch_validates_required_fields():
    response = client.post("/rerank_batch", json={})
    assert response.status_code == 422


def test_trait_profile_requires_upload_id():
    response = client.get("/trait-profile")
    assert response.status_code == 422
