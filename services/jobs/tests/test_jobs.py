import asyncio

import pytest
from httpx import AsyncClient
from fastapi import status

from services.jobs.app.main import app

@pytest.mark.asyncio
async def test_create_and_get_job():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create a job
        payload = {"task": "demo", "payload": {"foo": "bar"}}
        resp = await client.post("/v1/jobs", json=payload)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        job_id = data["id"]
        assert data["status"] == "queued"
        # Immediately fetch – should be queued or running
        resp2 = await client.get(f"/v1/jobs/{job_id}")
        assert resp2.status_code == status.HTTP_200_OK
        # Wait for background job to finish
        await asyncio.sleep(3)
        resp3 = await client.get(f"/v1/jobs/{job_id}")
        assert resp3.status_code == status.HTTP_200_OK
        final = resp3.json()
        assert final["status"] == "completed"
        assert final["result"]["message"] == "Task demo completed"

@pytest.mark.asyncio
async def test_health_and_metrics():
    async with AsyncClient(app=app, base_url="http://test") as client:
        health = await client.get("/health")
        assert health.status_code == status.HTTP_200_OK
        metrics = await client.get("/metrics")
        assert metrics.status_code == status.HTTP_200_OK
        # Simple sanity check that metric output contains our counter name
        assert "jobs_requests_total" in metrics.text
