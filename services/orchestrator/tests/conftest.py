from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Tuple
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import sys
import os

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("ENABLE_SPIFFE", "false")

from services.orchestrator.app.main import create_app
from services.orchestrator.app.workflows.mao import AgentExecutionResult, MAOResult
from services.orchestrator.app.workflows.session import SessionStartResult
from temporalio.client import RPCError, RPCStatusCode


class FakeWorkflowHandle:
    def __init__(
        self,
        workflow_id: str,
        run_id: str,
        result: SessionStartResult,
        history_length: int = 3,
        status: str = "COMPLETED",
    ) -> None:
        self.id = workflow_id
        self.run_id = run_id
        self._result = result
        self._history_length = history_length
        self._status = status

    async def describe(self) -> SimpleNamespace:
        return SimpleNamespace(
            status=SimpleNamespace(name=self._status),
            execution=SimpleNamespace(run_id=self.run_id),
            history_length=self._history_length,
        )

    async def result(self) -> SessionStartResult:
        return self._result


class FakeTemporalClient:
    def __init__(self) -> None:
        self.workflows: Dict[str, FakeWorkflowHandle] = {}
        self.closed = False

    async def start_workflow(self, workflow: str, payload: Any, *, id: str, **kwargs: Any) -> FakeWorkflowHandle:  # noqa: D417
        run_id = str(uuid4())
        if workflow == "multi-agent-orchestration-workflow":
            agent_results = [
                AgentExecutionResult(
                    agent_id=directive.agent_id,
                    goal=directive.goal,
                    status="completed",
                    slm_response={"completion": f"ok:{directive.prompt[:15]}"},
                    token={"access_token": f"token-{directive.agent_id}"},
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                )
                for directive in payload.directives
            ]
            result = MAOResult(
                orchestration_id=payload.orchestration_id,
                tenant=payload.tenant,
                initiator=payload.initiator,
                status="completed",
                agent_results=agent_results,
                audit_event_id=str(uuid4()),
                notifications_sent=[],
                completed_at=datetime.now(timezone.utc),
                policy={"allowed": True, "workflow": workflow},
            )
        else:
            result = SessionStartResult(
                session_id=payload.session_id,
                tenant=payload.tenant,
                user=payload.user,
                status="completed",
                policy={"allowed": True, "workflow": workflow},
                token={"access_token": "fake-token", "user": payload.user},
                slm_response={"completion": f"ok:{payload.prompt[:10]}"},
                audit_event_id=str(uuid4()),
                completed_at=datetime.now(timezone.utc),
            )
        handle = FakeWorkflowHandle(workflow_id=id, run_id=run_id, result=result)
        handle.input_payload = payload  # type: ignore[attr-defined]
        self.workflows[id] = handle
        return handle

    def get_workflow_handle(self, workflow_id: str) -> FakeWorkflowHandle:
        try:
            return self.workflows[workflow_id]
        except KeyError as exc:
            raise RPCError(
                f"Workflow {workflow_id} not found",
                RPCStatusCode.NOT_FOUND,
                b"",
            ) from exc

    async def close(self) -> None:
        self.closed = True


@pytest.fixture
def api_client(monkeypatch: pytest.MonkeyPatch) -> Tuple[TestClient, FakeTemporalClient]:
    fake_client = FakeTemporalClient()

    async def _connect(*args: Any, **kwargs: Any) -> FakeTemporalClient:
        return fake_client

    monkeypatch.setattr(
        "services.orchestrator.app.main.temporal_client.Client.connect",
        _connect,
    )

    app = create_app()
    with TestClient(app) as client:
        yield client, fake_client