"""Basic integration tests for the Memory Gateway service.

The Memory Gateway provides simple key/value storage with optional vector
support via Qdrant. These tests verify the core HTTP contract:

* ``/health`` returns ``200 OK`` with body ``OK``.
* ``/v1/remember`` stores a payload.
* ``/v1/recall/{key}`` retrieves the stored payload.
* ``/metrics`` is reachable and contains the ``somabrain_requests_total``
  metric that the service increments on each request.

The tests use FastAPI's ``TestClient`` so they run without needing a running
container or external dependencies.
"""

from fastapi.testclient import TestClient

# Import the FastAPI app from the service implementation
from app.main import app  # type: ignore

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.text == "OK"


def test_remember_and_recall():
    # Store a value
    payload = {"key": "test_key", "value": {"msg": "hello"}}
    remember_resp = client.post("/v1/remember", json=payload)
    assert remember_resp.status_code == 200
    assert remember_resp.json() == payload

    # Retrieve the same value
    recall_resp = client.get("/v1/recall/test_key")
    assert recall_resp.status_code == 200
    data = recall_resp.json()
    assert data["key"] == "test_key"
    assert data["value"] == {"msg": "hello"}


def test_metrics_endpoint():
    # Trigger a request to increment the counter
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    # Ensure the metric name appears in the output
    assert "somabrain_requests_total" in response.text
