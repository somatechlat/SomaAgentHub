import os
import pytest
import json
from fastapi import status
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import the FastAPI app from the orchestrator package
from services.orchestrator.app.main import app

client = TestClient(app)

# Helper to build payload with required fields
def build_payload():
    return {
        "session_id": "sess1",
        "tenant": os.getenv("TEST_TENANT", "t1"),
        "user": os.getenv("TEST_USER", "u1"),
        "prompt": "test prompt",
        "role": "user",
    }

def test_session_start_success():
    """Integration test – hits real Policy Engine and Identity Service.
    Assumes the services are reachable (via docker‑compose) at the URLs
    configured in the orchestrator (env vars POLICY_ENGINE_URL and
    IDENTITY_SERVICE_URL)."""
    payload = build_payload()
    response = client.post("/v1/sessions/start", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # Verify the orchestrator returned the session id we sent
    assert data["session_id"] == payload["session_id"]
    # Policy result must be a dict with an "allowed" key
    assert isinstance(data.get("policy"), dict)
    assert "allowed" in data["policy"]
    # Token response must contain a JWT
    assert isinstance(data.get("token"), dict)
    assert "token" in data["token"]

@ pytest.mark.asyncio
async def test_turn_stream():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        async with ac.stream("GET", f"/v1/turn/{build_payload()['session_id']}") as resp:
            assert resp.status_code == status.HTTP_200_OK
            events = []
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    events.append(json.loads(line[5:].strip()))
                if len(events) == 3:
                    break
            assert len(events) == 3
            assert events[0]["event"] == "turn_started"
            assert events[2]["event"] == "turn_completed"

def test_marketplace_publish_and_list():
    payload = {"name": "test_capsule", "content": "dummy"}
    resp = client.post("/v1/marketplace/publish", json=payload)
    assert resp.status_code == status.HTTP_200_OK
    capsule_id = resp.json()["capsule_id"]
    list_resp = client.get("/v1/marketplace/capsules")
    assert list_resp.status_code == status.HTTP_200_OK
    caps = list_resp.json()
    assert any(c["capsule_id"] == capsule_id for c in caps)

def test_job_start_and_status():
    payload = {"task": "example"}
    start_resp = client.post("/v1/jobs/start", json=payload)
    assert start_resp.status_code == status.HTTP_200_OK
    job_id = start_resp.json()["job_id"]
    status_resp = client.get(f"/v1/jobs/{job_id}")
    assert status_resp.status_code == status.HTTP_200_OK
    assert status_resp.json()["status"] == "running"
    # Wait for background job to finish (2 s simulated)
    import time
    time.sleep(2.5)
    final_resp = client.get(f"/v1/jobs/{job_id}")
    assert final_resp.json()["status"] == "completed"
