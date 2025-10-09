"""HTTP routes for the orchestrator service backed by Temporal workflows."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from temporalio import client as temporal_client
from temporalio.client import RPCError, RPCStatusCode

from ..core.config import settings
from ..workflows.mao import AgentDirective, MAOStartInput
from ..workflows.session import SessionStartInput

# Import conversation and training endpoints
from .conversation import router as conversation_router
from .projects import router as projects_router
from .training import router as training_router

router = APIRouter(prefix="/v1", tags=["orchestrator"])
router.include_router(conversation_router)
router.include_router(projects_router)
router.include_router(training_router)


class SessionStartRequest(BaseModel):
    tenant: str = Field(..., description="Tenant identifier")
    user: str = Field(..., description="User starting the session")
    prompt: str = Field(..., description="Conversation seed prompt")
    model: str = Field(default="somagent-demo", description="Requested model identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional session metadata")


class SessionStartResponse(BaseModel):
    workflow_id: str
    run_id: str
    session_id: str
    task_queue: str


class SessionStatusResponse(BaseModel):
    workflow_id: str
    run_id: str
    status: str
    history_length: int | None = None
    result: Dict[str, Any] | None = None


class AgentDirectiveModel(BaseModel):
    agent_id: str
    goal: str
    prompt: str
    capabilities: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MultiAgentStartRequest(BaseModel):
    tenant: str
    initiator: str
    directives: List[AgentDirectiveModel]
    notification_channel: str | None = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MultiAgentStartResponse(BaseModel):
    workflow_id: str
    run_id: str
    orchestration_id: str
    task_queue: str


async def get_temporal_client(request: Request) -> temporal_client.Client:
    client = getattr(request.app.state, "temporal_client", None)
    if client is None:
        raise HTTPException(status_code=503, detail="Temporal client not initialised")
    return client


def _normalize_result(result_obj: Any) -> Dict[str, Any] | None:
    if result_obj is None:
        return None
    if is_dataclass(result_obj):
        return asdict(result_obj)
    if isinstance(result_obj, dict):
        return result_obj
    if isinstance(result_obj, list):
        return {"items": result_obj}
    return {"value": result_obj}


@router.post("/sessions/start", response_model=SessionStartResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_session(payload: SessionStartRequest, client: temporal_client.Client = Depends(get_temporal_client)) -> SessionStartResponse:
    """Kick off the Temporal session workflow and return identifiers for tracking."""
    session_id = payload.metadata.get("session_id") or f"session-{uuid4()}"
    workflow_id = f"session-{session_id}"

    handle = await client.start_workflow(
        "session-start-workflow",
        SessionStartInput(
            session_id=session_id,
            tenant=payload.tenant,
            user=payload.user,
            prompt=payload.prompt,
            model=payload.model,
            metadata=payload.metadata,
        ),
        id=workflow_id,
        task_queue=settings.temporal_task_queue,
    )

    return SessionStartResponse(
        workflow_id=handle.id,
        run_id=handle.run_id,
        session_id=session_id,
        task_queue=settings.temporal_task_queue,
    )


@router.get("/sessions/{workflow_id}", response_model=SessionStatusResponse)
async def get_session_status(workflow_id: str, client: temporal_client.Client = Depends(get_temporal_client)) -> SessionStatusResponse:
    """Fetch workflow status and (if completed) the result payload."""

    try:
        handle = client.get_workflow_handle(workflow_id)
        desc = await handle.describe()
    except RPCError as exc:
        if exc.status == RPCStatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    status_name = desc.status.name.lower()
    result: Dict[str, Any] | None = None
    if status_name == "completed":
        try:
            result_obj = await handle.result()
            result = _normalize_result(result_obj)
        except Exception as exc:  # pragma: no cover - Temporal result retrieval edge cases
            result = {"error": str(exc)}

    return SessionStatusResponse(
        workflow_id=workflow_id,
        run_id=desc.execution.run_id,
        status=status_name,
        history_length=desc.history_length,
        result=result,
    )


@router.post("/mao/start", response_model=MultiAgentStartResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_multi_agent(
    payload: MultiAgentStartRequest,
    client: temporal_client.Client = Depends(get_temporal_client),
) -> MultiAgentStartResponse:
    orchestration_id = payload.metadata.get("orchestration_id") or f"mao-{uuid4()}"
    workflow_id = f"mao-{orchestration_id}"

    directives = [AgentDirective(**directive.model_dump()) for directive in payload.directives]

    handle = await client.start_workflow(
        "multi-agent-orchestration-workflow",
        MAOStartInput(
            orchestration_id=orchestration_id,
            tenant=payload.tenant,
            initiator=payload.initiator,
            directives=directives,
            notification_channel=payload.notification_channel,
            metadata=payload.metadata,
        ),
        id=workflow_id,
        task_queue=settings.temporal_task_queue,
    )

    return MultiAgentStartResponse(
        workflow_id=handle.id,
        run_id=handle.run_id,
        orchestration_id=orchestration_id,
        task_queue=settings.temporal_task_queue,
    )


@router.get("/mao/{workflow_id}", response_model=SessionStatusResponse)
async def get_multi_agent_status(
    workflow_id: str,
    client: temporal_client.Client = Depends(get_temporal_client),
) -> SessionStatusResponse:
    return await get_session_status(workflow_id, client)
