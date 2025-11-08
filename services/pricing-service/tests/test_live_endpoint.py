import os
import sys
from fastapi.testclient import TestClient

# Adjust path to import pricing-service app
BASE = os.path.dirname(os.path.dirname(__file__))
sys.path.append(BASE)

from app.main import app  # noqa: E402

client = TestClient(app)


def test_live_basic():
    r = client.get("/v1/pricing/live")
    assert r.status_code == 200
    data = r.json()
    assert "offers" in data
    assert data["summary"]["count"] >= len(data["offers"])  # simple sanity


def test_filter_gpu_model():
    r = client.get("/v1/pricing/live", params={"gpu_model": "A100"})
    assert r.status_code == 200
    data = r.json()
    for o in data["offers"]:
        assert "A100" in o["gpu_model"]


def test_budget_evaluation():
    r = client.post("/v1/pricing/evaluate-budget", params={"gpu_model": "A100", "hours_planned": 1.5, "quantity": 2, "budget_cap": 20})
    assert r.status_code == 200
    payload = r.json()
    assert "estimated_cost" in payload
    assert "within_budget" in payload
