from fastapi import status
from fastapi.testclient import TestClient

from services.orchestrator.app.main import app

client = TestClient(app)

def test_health_check():
    resp = client.get("/v1/healthz")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data.get("status") == "ok"

def test_analytics_capsules():
    # Ensure the endpoint returns a count (even if zero)
    resp = client.get("/v1/analytics/capsules")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "total_capsules" in data
    # The count should be an integer >= 0
    assert isinstance(data["total_capsules"], int)
    assert data["total_capsules"] >= 0
