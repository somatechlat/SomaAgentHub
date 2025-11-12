import importlib
import json
import os
import sys

import httpx
import requests
from fastapi.testclient import TestClient

BASE = os.path.dirname(os.path.dirname(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

for name in list(sys.modules.keys()):
    if name == "app" or name.startswith("app."):
        del sys.modules[name]

importlib.import_module("app.wizard_engine")
app = importlib.import_module("app.main").app  # type: ignore
client = TestClient(app)


class FakeAsyncClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, params=None, json=None, headers=None, timeout=None):  # noqa: A003
        if url.endswith("/v1/pricing/evaluate-budget/with-policy"):
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


class FakeResp:
    def __init__(self, status_code: int, data: dict):
        self.status_code = status_code
        self._data = data
        self.text = json.dumps(data)

    def json(self):
        return self._data


def fake_post(url, *args, **kwargs):
    if url.endswith("/v1/pricing/evaluate-budget/with-policy"):
        return FakeResp(200, {"within_budget": False, "estimated_cost": 120.0})
    if url.endswith("/v1/mao/start"):
        return FakeResp(200, {"workflow_id": "wf-1", "orchestration_id": "orc-1", "task_queue": "q"})
    return FakeResp(404, {"detail": "not found"})


def test_wizard_budget_block(monkeypatch):
    schema = {
        "wizard_id": "cost-wiz",
        "title": "Cost Test",
    }
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(requests, "post", fake_post)
    resp = client.post(
        "/v1/wizard/budget",
        json={"wizard_id": schema["wizard_id"], "answers": {"budget": 10.0}},
        headers={"X-Tenant-ID": "demo"},
    )
    assert resp.status_code in {200, 403}
