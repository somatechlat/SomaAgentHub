import os
from importlib.machinery import SourceFileLoader

import httpx
from fastapi.testclient import TestClient
from httpx import Response

# Add service path then dynamically load gateway main to avoid package shadowing
BASE = os.path.dirname(os.path.dirname(__file__))
gateway_main = SourceFileLoader("gateway_app_main", os.path.join(BASE, "app", "main.py")).load_module()
app = gateway_main.app  # noqa: E402

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
            return Response(
                200,
                content=json.dumps(data),
                headers={"Content-Type": "application/json"},
            )
        if url.endswith("/v1/pricing/snapshot"):
            data = {"snapshot_id": "test-snap-123", "offers": 1, "hash": "abc"}
            return Response(
                200,
                content=json.dumps(data),
                headers={"Content-Type": "application/json"},
            )
        if url.endswith("/v1/build-runs"):
            data = {"id": "run-1", "status": "queued"}
            return Response(
                200,
                content=json.dumps(data),
                headers={"Content-Type": "application/json"},
            )
        return Response(404, json={"detail": "not found"})


def test_cost_precheck(monkeypatch):
    monkeypatch.setenv("SOMAGENT_GATEWAY_ORCHESTRATOR_URL", "http://orchestrator-mock")
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
    monkeypatch.setenv("SOMAGENT_GATEWAY_ORCHESTRATOR_URL", "http://orchestrator-mock")
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
