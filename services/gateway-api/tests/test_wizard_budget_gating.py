import json
import os
import sys

import httpx
import requests
from fastapi.testclient import TestClient

BASE = os.path.dirname(os.path.dirname(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

# Ensure we import the gateway app package, not others
for name in list(sys.modules.keys()):
    if name == "app" or name.startswith("app."):
        del sys.modules[name]

from app.wizard_engine import wizard_engine  # type: ignore  # noqa: E402

from app.main import app  # type: ignore  # noqa: E402
from services.common.config.base_settings import resolve_env

client = TestClient(app)


class FakeAsyncClient:
    def __init__(self, *a, **kw):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(
        self, url, params=None, json=None, headers=None, timeout=None
    ):  # noqa: A003
        # pricing budget check
        if url.endswith("/v1/pricing/evaluate-budget/with-policy"):
            # Fake over-budget response
            data = {
                "within_budget": False,
                "estimated_cost": 120.0,
                "currency": "USD",
                "chosen_offer": {"id": "x", "price_per_hour": 10.0},
                "policy_decision": {"allow_build": True},
            }
            return httpx.Response(
                200,
                content=json.dumps(data),
                headers={"Content-Type": "application/json"},
            )
        # orchestrator run start
        if url.endswith("/v1/mao/start"):
            data = {
                "workflow_id": "wf-1",
                "orchestration_id": "orc-1",
                "task_queue": "q",
            }
            return httpx.Response(
                200,
                content=json.dumps(data),
                headers={"Content-Type": "application/json"},
            )
        return httpx.Response(
            404,
            content=json.dumps({"detail": "not found"}),
            headers={"Content-Type": "application/json"},
        )


json_module = json  # alias for response building


def test_wizard_budget_block(monkeypatch):
    # Prepare wizard schema with budget questions
    schema = {
        "wizard_id": "cost-wiz",
        "title": "Cost Test",
        "version": "1",
        "questions": [
            {"id": "budget_cap", "step": 1, "prompt": "Budget?", "type": "number"},
            {"id": "hours", "step": 2, "prompt": "Hours?", "type": "number"},
        ],
        "modules": [],
    }
    wizard_engine.wizard_schemas["cost-wiz"] = schema

    # Start session
    r = client.post(
        "/v1/wizards/start", json={"wizard_id": "cost-wiz", "user_id": "u1"}
    )
    assert r.status_code == 200
    sid = r.json()["session_id"]

    # Answer budget and hours
    r1 = client.post(f"/v1/wizards/{sid}/answer", json={"value": 100})
    assert r1.status_code == 200
    r2 = client.post(f"/v1/wizards/{sid}/answer", json={"value": 12})
    assert r2.status_code == 200

    # Monkeypatch requests.post used in wizard budget precheck
    class FakeResp:
        def __init__(self, status_code: int, data: dict):
            self.status_code = status_code
            self._data = data
            self.text = json.dumps(data)

        def json(self):
            return self._data

    def fake_post(url, *args, **kwargs):
        if url.endswith("/v1/pricing/evaluate-budget/with-policy"):
            return FakeResp(
                200,
                {
                    "within_budget": False,
                    "estimated_cost": 120.0,
                    "currency": "USD",
                    "chosen_offer": {"id": "x", "price_per_hour": 10.0},
                    "policy_decision": {"allow_build": True},
                },
            )
        # For safety if orchestrator is called (should not be)
        if url.endswith("/v1/mao/start"):
            return FakeResp(
                200,
                {"workflow_id": "wf-1", "orchestration_id": "orc-1", "task_queue": "q"},
            )
        return FakeResp(404, {"detail": "not found"})

    monkeypatch.setattr(requests, "post", fake_post)

    # Approve (should block due to fake over-budget)
    r3 = client.post(f"/v1/wizards/{sid}/approve")
    assert r3.status_code == 200
    data = r3.json()
    assert data["status"] == "blocked"
    assert data["reason"] == "budget_exceeded"
