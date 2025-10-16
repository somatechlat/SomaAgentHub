import os
import time
import asyncio

import httpx
import pytest

GATEWAY_URL = os.getenv("E2E_GATEWAY_URL", "http://localhost:8080")
ORCH_URL = os.getenv("E2E_ORCHESTRATOR_URL", "http://localhost:1004")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_gateway_to_orchestrator_session_flow():
    # 1) Create a session via Gateway (moderation + forward)
    payload = {
        "prompt": "Write a short hello world.",
        "capsule_id": "demo",
        "metadata": {"source": "e2e"},
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{GATEWAY_URL}/v1/sessions", json=payload)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        workflow_id = data["payload"]["workflow_id"]
        assert workflow_id

    # 2) Poll orchestrator status until completed (or timeout)
    deadline = time.time() + 60  # 1 minute max
    status = None
    async with httpx.AsyncClient(timeout=10.0) as client:
        while time.time() < deadline:
            r = await client.get(f"{ORCH_URL}/v1/sessions/{workflow_id}")
            assert r.status_code == 200, r.text
            status = r.json()["status"]
            if status in {"completed", "failed", "terminated"}:
                break
            await asyncio.sleep(2)

    assert status == "completed", f"Workflow did not complete, status={status}"
