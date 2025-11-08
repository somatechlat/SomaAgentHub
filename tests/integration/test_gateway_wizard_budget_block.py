"""Negative-path integration test: wizard approval blocked by pricing budget precheck.

Simulates scenario where pricing service reports over-budget so wizard approval returns status 'blocked'.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

import requests
from fastapi.testclient import TestClient

# Match import technique used in other gateway tests
BASE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "services", "gateway-api")
)
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from app.wizard_engine import wizard_engine  # type: ignore  # noqa: E402

from app.main import app  # type: ignore  # noqa: E402

client = TestClient(app)


def _register_block_wizard():
    wizard_engine.wizard_schemas["block-wiz"] = {
        "wizard_id": "block-wiz",
        "title": "Block Wizard",
        "version": "1.0",
        "questions": [
            {
                "id": "budget_cap",
                "step": 1,
                "prompt": "Budget cap?",
                "type": "number",
                "required": True,
            },
            {
                "id": "hours_planned",
                "step": 2,
                "prompt": "Hours planned?",
                "type": "number",
                "required": True,
            },
        ],
        "modules": [],
    }


def test_wizard_approval_blocked(monkeypatch):
    _register_block_wizard()
    monkeypatch.setenv("SOMAGENT_GATEWAY_ORCHESTRATOR_URL", "http://mock-orchestrator")
    monkeypatch.setenv("PRICING_SERVICE_URL", "http://mock-pricing")

    class FakeResp:
        def __init__(self, status_code: int, data: dict[str, Any]):
            self.status_code = status_code
            self._data = data
            self.text = json.dumps(data)

        def json(self):  # noqa: D401
            return self._data

    def fake_post(url: str, *args, **kwargs):  # noqa: ANN001
        if url.endswith("/v1/pricing/evaluate-budget/with-policy"):
            return FakeResp(
                200,
                {
                    "within_budget": False,
                    "estimated_cost": 250.0,
                    "currency": "USD",
                    "chosen_offer": {"id": "offer-x", "price_per_hour": 25.0},
                    "policy_decision": {"allow_build": True},
                },
            )
        if url.endswith("/v1/mao/start"):
            return FakeResp(
                200,
                {
                    "workflow_id": "wf-ignored",
                    "orchestration_id": "orc-ignored",
                    "task_queue": "q",
                },
            )
        return FakeResp(404, {"detail": "unexpected URL"})

    monkeypatch.setattr(requests, "post", fake_post)

    start = client.post(
        "/v1/wizards/start", json={"wizard_id": "block-wiz", "user_id": "tester"}
    )
    assert start.status_code == 200, start.text
    session_id = start.json()["session_id"]

    assert (
        client.post(f"/v1/wizards/{session_id}/answer", json={"value": 100}).status_code
        == 200
    )
    assert (
        client.post(f"/v1/wizards/{session_id}/answer", json={"value": 12}).status_code
        == 200
    )

    approve = client.post(f"/v1/wizards/{session_id}/approve")
    assert approve.status_code == 200
    data = approve.json()
    assert data["status"] == "blocked"
    assert data["reason"] == "budget_exceeded"
