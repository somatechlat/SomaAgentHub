from fastapi.testclient import TestClient

from services.slm_service.app.main import app

client = TestClient(app)


def test_health_payload():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "slm-service"


def test_metrics_contains_slm_names():
    # Trigger endpoints to increment metrics
    client.post("/v1/infer/sync", json={"prompt": "hi", "max_tokens": 4, "temperature": 0.5})
    client.post("/v1/embeddings", json={"input": ["hello world"]})

    resp = client.get("/metrics")
    assert resp.status_code == 200
    text = resp.text

    # Ensure new metric names are present
    assert "slm_infer_sync_requests_total" in text
    assert "slm_infer_sync_latency_seconds" in text
    assert "slm_embedding_requests_total" in text
    assert "slm_embedding_latency_seconds" in text

    # Ensure legacy names are not present anymore
    assert "somallm_infer_sync_requests_total" not in text
    assert "somallm_infer_sync_latency_seconds" not in text
    assert "somallm_embedding_requests_total" not in text
    assert "somallm_embedding_latency_seconds" not in text
