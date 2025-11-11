import os
import sys
import sys
import json
import httpx
from fastapi.testclient import TestClient
from httpx import Response

BASE = os.path.dirname(os.path.dirname(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)
from app.main import app  # type: ignore
from services.common.config.base_settings import resolve_env

client = TestClient(app)

# Minimal monkeypatch for settings if needed


class FakeAsyncClient:
    def __init__(self, *a, **kw):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None, headers=None):  # noqa: A003
        if url.endswith("/v1/build/precheck"):
            data = {
                "within_budget": True,
                "estimated_cost": 9.5,
                "currency": "USD",
                "policy_decision": {"allow_build": True},
                "require_payment": False,
                "recommended_action": None,
            }
            return Response(status_code=200, json=data)
        if url.endswith("/v1/pricing/snapshot"):
            data = {"snapshot_id": "test-snap-123", "offers": 1, "hash": "abc"}
            return Response(status_code=200, json=data)
        if url.endswith("/v1/build-runs"):
            data = {"id": "run-1", "status": "queued"}
            return Response(status_code=200, json=data)
        return Response(status_code=404, json={"detail": "not found"})


def test_cost_precheck(monkeypatch):
    # Use canonical env var prefix for orchestrator URL
    monkeypatch.setenv("SOMA_AGENT_HUB_GATEWAY_ORCHESTRATOR_URL", "http://orchestrator-mock")
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    resp = client.post(
        "/v1/build/cost-precheck",
        json={
            "project_id": "proj1",
            "hours_planned": 1.0,
            "quantity": 1,
            "budget_cap": 10.0,
        },
        headers={
            "X-Tenant-ID": "demo",
            "X-Client-Type": "web",
            "X-Deployment-Mode": "developer-light",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["within_budget"] is True
    assert data["estimated_cost"] == 9.5


def test_build_run_requires_snapshot_auto(monkeypatch):
    # Mock orchestrator endpoint and pricing snapshot creation via monkeypatching AsyncClient
    monkeypatch.setenv("SOMA_AGENT_HUB_GATEWAY_ORCHESTRATOR_URL", "http://orchestrator-mock")
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    resp = client.post(
        "/v1/build/run",
        json={"project_id": "proj1", "budget_cap": 100.0, "estimated_cost": 10.0},
        headers={
            "X-Tenant-ID": "demo",
            "X-Client-Type": "web",
            "X-Deployment-Mode": "developer-light",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["build_run_id"] == "run-1"
    assert data["status"] == "queued"
