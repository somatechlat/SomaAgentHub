from __future__ import annotations

from types import SimpleNamespace
from typing import Any, List

import pytest

from services.orchestrator.app.integrations import (
    run_autogen_group_chat,
    run_crewai_delegation,
    run_langgraph_routing,
)
from services.orchestrator.app.workflows.session import (
    PolicyEvaluationContext,
    emit_audit_event,
    evaluate_policy,
)
from services.orchestrator.app.workflows.unified_multi_agent import UnifiedMultiAgentWorkflow
from temporalio import workflow as temporal_workflow


class DummyLogger:
    def info(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - noiseless stub
        pass


@pytest.fixture(autouse=True)
def patch_workflow_info(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(temporal_workflow, "info", lambda: SimpleNamespace(workflow_id="wf-test"))
    monkeypatch.setattr(temporal_workflow, "logger", DummyLogger())


@pytest.mark.asyncio
async def test_unified_workflow_routes_group_chat(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: List[str] = []

    async def fake_execute_activity(activity, *args: Any, **kwargs: Any):
        calls.append(activity.__name__)
        if activity is evaluate_policy:
            ctx = args[0]
            assert isinstance(ctx, PolicyEvaluationContext)
            assert ctx.tenant == "tenant-123"
            return {"allowed": True, "policy_id": "ok"}
        if activity is run_autogen_group_chat:
            payload = args[0]
            assert payload["task"] == "brainstorm"
            return {"framework": "autogen", "result": "done"}
        if activity is emit_audit_event:
            event = args[0]
            assert event["pattern"] == "group_chat"
            return "audit-1"
        raise AssertionError(f"Unexpected activity {activity}")

    monkeypatch.setattr(temporal_workflow, "execute_activity", fake_execute_activity)

    workflow_instance = UnifiedMultiAgentWorkflow()
    result = await workflow_instance.run(
        {
            "session_id": "sess-1",
            "tenant": "tenant-123",
            "user": "jane",
            "agents": [{"name": "a", "model": "gpt-4o"}, {"name": "b", "model": "gpt-4o"}, {"name": "c", "model": "gpt-4o"}],
            "task": "brainstorm",
        }
    )

    assert result["activity"] == "autogen-group-chat"
    assert result["pattern"] == "group_chat"
    assert result["status"] == "completed"
    assert calls == ["evaluate_policy", "run_autogen_group_chat", "emit_audit_event"]


@pytest.mark.asyncio
async def test_unified_workflow_routes_delegation(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: List[str] = []

    async def fake_execute_activity(activity, *args: Any, **kwargs: Any):
        calls.append(activity.__name__)
        if activity is evaluate_policy:
            return {"allowed": True}
        if activity is run_crewai_delegation:
            payload = args[0]
            assert len(payload["tasks"]) == 1
            return {"framework": "crewai", "tasks_completed": 1}
        if activity is emit_audit_event:
            return "audit-2"
        raise AssertionError(f"Unexpected activity {activity}")

    monkeypatch.setattr(temporal_workflow, "execute_activity", fake_execute_activity)

    workflow_instance = UnifiedMultiAgentWorkflow()
    result = await workflow_instance.run(
        {
            "session_id": "sess-2",
            "tenant": "tenant-xyz",
            "user": "alex",
            "manager": {"role": "lead", "goal": "ship"},
            "workers": [{"role": "writer", "goal": "draft"}],
            "tasks": [{"description": "draft doc"}],
        }
    )

    assert result["activity"] == "crewai-delegation"
    assert result["pattern"] == "task_delegation"
    assert result["status"] == "completed"
    assert calls == ["evaluate_policy", "run_crewai_delegation", "emit_audit_event"]


@pytest.mark.asyncio
async def test_unified_workflow_routes_langgraph(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: List[str] = []

    async def fake_execute_activity(activity, *args: Any, **kwargs: Any):
        calls.append(activity.__name__)
        if activity is evaluate_policy:
            return {"allowed": True}
        if activity is run_langgraph_routing:
            payload = args[0]
            assert payload["graph"]["start"] == "begin"
            return {"framework": "langgraph", "history": []}
        if activity is emit_audit_event:
            return "audit-3"
        raise AssertionError(f"Unexpected activity {activity}")

    monkeypatch.setattr(temporal_workflow, "execute_activity", fake_execute_activity)

    workflow_instance = UnifiedMultiAgentWorkflow()
    result = await workflow_instance.run(
        {
            "session_id": "sess-3",
            "tenant": "tenant-lang",
            "user": "cam",
            "graph": {"nodes": [{"name": "begin", "handler": "math.floor"}], "start": "begin"},
        }
    )

    assert result["activity"] == "langgraph-routing"
    assert result["pattern"] == "state_machine_routing"
    assert result["status"] == "completed"
    assert calls == ["evaluate_policy", "run_langgraph_routing", "emit_audit_event"]


@pytest.mark.asyncio
async def test_unified_workflow_policy_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: List[str] = []

    async def fake_execute_activity(activity, *args: Any, **kwargs: Any):
        calls.append(activity.__name__)
        if activity is evaluate_policy:
            return {"allowed": False, "reason": "blocked"}
        raise AssertionError("No other activities should be invoked")

    monkeypatch.setattr(temporal_workflow, "execute_activity", fake_execute_activity)

    workflow_instance = UnifiedMultiAgentWorkflow()
    result = await workflow_instance.run({"session_id": "sess-4", "tenant": "tenant-a", "user": "rory"})

    assert result["status"] == "rejected"
    assert result["reason"] == "policy_denied"
    assert result["policy"] == {"allowed": False, "reason": "blocked"}
    assert calls == ["evaluate_policy"]
