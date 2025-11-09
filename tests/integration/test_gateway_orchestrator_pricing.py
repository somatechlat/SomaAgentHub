"""Integration test: Gateway wizard approval triggers pricing precheck and orchestrator start.

This focuses on the combined flow inside `wizard_engine.approve_execution`:
- Builds execution plan from answers and modules
- Performs optional pricing budget precheck (evaluate-budget/with-policy)
- Dispatches orchestration request to orchestrator `/v1/mao/start`

Network calls are monkeypatched to avoid external dependencies.
"""

from __future__ import annotations

import json

# Ensure we import the gateway service's `app` package correctly despite hyphen in path
import os
import sys
from typing import Any

import requests
from fastapi.testclient import TestClient

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "services", "gateway-api"))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from app.wizard_engine import wizard_engine  # type: ignore  # noqa: E402

from app.main import app  # type: ignore  # noqa: E402

client = TestClient(app)


def _register_test_wizard():
    """Register a minimal wizard schema exercising budget gating + plan directives."""
    wizard_engine.wizard_schemas["orch-budget-wiz"] = {
        "wizard_id": "orch-budget-wiz",
        "title": "Orchestrated Budget Wizard",
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
            {
                "id": "campaign_name",
                "step": 3,
                "prompt": "Campaign name?",
                "type": "text",
                "required": True,
            },
        ],
        "modules": [
            {
                "id": "m1",
                "title": "Primary Module for {campaign_name}",
                "agent": "agent-alpha",
                "tasks": [
                    {
                        "action": "chat.generate",
                        "description": "Generate assets for {campaign_name}",
                    },
                    {
                        "action": "memory_gateway.remember",
                        "description": "Persist campaign metadata",
                    },
                ],
                "outputs": ["artifact_bundle"],
            }
        ],
    }


def test_wizard_approval_triggers_pricing_and_orchestrator(monkeypatch):
    _register_test_wizard()

    # Ensure env directs wizard to mock endpoints (values arbitrary; we match on suffix).
    monkeypatch.setenv("SOMAGENT_GATEWAY_ORCHESTRATOR_URL", "http://mock-orchestrator")
    monkeypatch.setenv("PRICING_SERVICE_URL", "http://mock-pricing")

    # Monkeypatch requests.post used by approve_execution for pricing & orchestrator.
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
                    "within_budget": True,
                    "estimated_cost": 45.0,
                    "currency": "USD",
                    "chosen_offer": {"id": "offer-1", "price_per_hour": 9.0},
                    "policy_decision": {"allow_build": True},
                },
            )
        if url.endswith("/v1/mao/start"):
            return FakeResp(
                200,
                {
                    "workflow_id": "wf-xyz",
                    "orchestration_id": "orc-123",
                    "task_queue": "campaign-q",
                },
            )
        return FakeResp(404, {"detail": "unexpected URL"})

    monkeypatch.setattr(requests, "post", fake_post)

    # Start wizard session
    start = client.post("/v1/wizards/start", json={"wizard_id": "orch-budget-wiz", "user_id": "tester"})
    assert start.status_code == 200, start.text
    session_id = start.json()["session_id"]

    # Provide answers for all steps
    assert client.post(f"/v1/wizards/{session_id}/answer", json={"value": 100}).status_code == 200  # budget_cap
    assert client.post(f"/v1/wizards/{session_id}/answer", json={"value": 5}).status_code == 200  # hours_planned
    assert (
        client.post(f"/v1/wizards/{session_id}/answer", json={"value": "Autumn Launch"}).status_code == 200
    )  # campaign_name completes wizard

    # Approve execution (should pass pricing precheck and invoke orchestrator)
    approve = client.post(f"/v1/wizards/{session_id}/approve")
    assert approve.status_code == 200, approve.text

    data = approve.json()
    assert data["status"] == "approved"
    assert data["execution_status"] == "queued"
    assert data.get("workflow_id") == "wf-xyz"
    # Budget gating should not block since within_budget True
    assert "reason" not in data

    # Sanity: execution plan cached in session metadata
    session = wizard_engine.sessions[session_id]
    assert session.metadata.get("_execution_plan") is not None
    plan = session.metadata["_execution_plan"]
    assert plan["campaign_name"] == "Autumn Launch"
    assert any(t["action"] == "chat.generate" for m in plan["modules"] for t in m["tasks"])  # directive build
