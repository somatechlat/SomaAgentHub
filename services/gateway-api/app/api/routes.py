"""HTTP routes for the Gateway API."""

from __future__ import annotations

import time
from typing import Any, List

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..config import GatewaySettings, get_settings
from ..core.metrics import observe_forward_latency, record_moderation_decision
from ..core.moderation import ModerationError, ModerationGuard
from ..dependencies import moderation_guard_dependency, request_context_dependency
from ..models.context import RequestContext
from ..models.sessions import (
    ModerationDetail,
    SessionCreateRequest,
    SessionCreateResponse,
)
from services.common.models.agent import AgentSpec, CrewSpec
from services.common.models.workflow import GraphWorkflow

router = APIRouter(prefix="/v1", tags=["gateway"])

@router.get("/status")
def read_status(
    ctx: RequestContext = Depends(request_context_dependency),
) -> dict[str, str]:
    """Return gateway status plus basic request context."""
    return {
        "service": "gateway",
        "state": "ready",
        "tenant": ctx.tenant_id,
        "client_type": ctx.client_type,
        "deployment_mode": ctx.deployment_mode,
    }

# ---------------------------------------------------------------------------
# Central health‑aggregation endpoint
# ---------------------------------------------------------------------------
@router.get("/aggregate-status", tags=["gateway"], response_model=dict)
async def aggregate_status(
    ctx: RequestContext = Depends(request_context_dependency),
    settings: GatewaySettings = Depends(get_settings),
) -> dict:
    """Query health endpoints of all downstream services and return a summary."""
    from asyncio import gather

    service_urls = {
        "orchestrator": getattr(settings, "orchestrator_url", "http://orchestrator:8000"),
        "identity": getattr(settings, "auth_url", "http://identity-service:8000"),
        "policy": getattr(settings, "policy_engine_url", "http://policy-engine:8000"),
        "memory_gateway": getattr(settings, "memory_gateway_url", "http://memory-gateway:8000"),
        "llm_hub": getattr(settings, "llm_hub_url", "http://llm-hub:8000"),
    }

    async def fetch(url: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{url.rstrip('/')}/health")
                if resp.status_code == 200:
                    return resp.json()
        except Exception as exc:
            pass
        return {"status": "unhealthy", "service": url}

    results = await gather(*[fetch(u) for u in service_urls.values()])
    aggregated = {name: result for name, result in zip(service_urls.keys(), results)}
    
    # Gateway's own health (simplified)
    aggregated["gateway"] = {"status": "ok", "service": "gateway"}

    return aggregated

def _build_forward_headers(ctx: RequestContext) -> dict[str, str]:
    headers: dict[str, str] = {
        "X-Tenant-ID": ctx.tenant_id,
        "X-Client-Type": ctx.client_type,
        "X-Deployment-Mode": ctx.deployment_mode,
    }
    if ctx.user_id:
        headers["X-User-ID"] = ctx.user_id
    if ctx.capabilities:
        headers["X-Capabilities"] = ",".join(ctx.capabilities)
    return headers

# ---------------------------------------------------------------------------
# Agent Registry Endpoints
# ---------------------------------------------------------------------------
@router.post("/agents", status_code=status.HTTP_201_CREATED, tags=["agents"])
async def create_agent(
    agent: AgentSpec,
    ctx: RequestContext = Depends(request_context_dependency),
    settings: GatewaySettings = Depends(get_settings),
):
    """Create a new AgentSpec."""
    url = f"{settings.orchestrator_url}/v1/agents"
    headers = _build_forward_headers(ctx)
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=agent.dict(), headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

@router.get("/agents/{agent_id}", tags=["agents"])
async def get_agent(
    agent_id: str,
    ctx: RequestContext = Depends(request_context_dependency),
    settings: GatewaySettings = Depends(get_settings),
):
    """Retrieve AgentSpec."""
    url = f"{settings.orchestrator_url}/v1/agents/{agent_id}"
    headers = _build_forward_headers(ctx)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Agent not found")
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

@router.put("/agents/{agent_id}", tags=["agents"])
async def update_agent(
    agent_id: str,
    agent: AgentSpec,
    ctx: RequestContext = Depends(request_context_dependency),
    settings: GatewaySettings = Depends(get_settings),
):
    """Update AgentSpec."""
    url = f"{settings.orchestrator_url}/v1/agents/{agent_id}"
    headers = _build_forward_headers(ctx)
    async with httpx.AsyncClient() as client:
        resp = await client.put(url, json=agent.dict(), headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

@router.post("/crews", status_code=status.HTTP_201_CREATED, tags=["crews"])
async def create_crew(
    crew: CrewSpec,
    ctx: RequestContext = Depends(request_context_dependency),
    settings: GatewaySettings = Depends(get_settings),
):
    """Create a CrewSpec."""
    url = f"{settings.orchestrator_url}/v1/crews"
    headers = _build_forward_headers(ctx)
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=crew.dict(), headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

# ---------------------------------------------------------------------------
# Workflow Endpoints
# ---------------------------------------------------------------------------
@router.post("/workflows", status_code=status.HTTP_201_CREATED, tags=["workflows"])
async def register_workflow(
    workflow: GraphWorkflow,
    ctx: RequestContext = Depends(request_context_dependency),
    settings: GatewaySettings = Depends(get_settings),
):
    """Register a new GraphWorkflow."""
    url = f"{settings.orchestrator_url}/v1/workflows"
    headers = _build_forward_headers(ctx)
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=workflow.dict(), headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

class ExecuteWorkflowRequest(BaseModel):
    input: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)

@router.post("/workflows/{workflow_id}/execute", status_code=status.HTTP_202_ACCEPTED, tags=["workflows"])
async def execute_workflow(
    workflow_id: str,
    payload: ExecuteWorkflowRequest,
    ctx: RequestContext = Depends(request_context_dependency),
    settings: GatewaySettings = Depends(get_settings),
):
    """Start execution of a workflow version."""
    url = f"{settings.orchestrator_url}/v1/workflows/{workflow_id}/execute"
    headers = _build_forward_headers(ctx)
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload.dict(), headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

@router.get("/instances/{instance_id}", tags=["workflows"])
async def get_instance(
    instance_id: str,
    ctx: RequestContext = Depends(request_context_dependency),
    settings: GatewaySettings = Depends(get_settings),
):
    """Get status & current state of a workflow instance."""
    url = f"{settings.orchestrator_url}/v1/instances/{instance_id}"
    headers = _build_forward_headers(ctx)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

class ReplayRequest(BaseModel):
    checkpoint_id: str = Field(..., alias="checkpointId")
    overrides: dict[str, Any] = Field(default_factory=dict)

@router.post("/instances/{instance_id}/replay", status_code=status.HTTP_202_ACCEPTED, tags=["workflows"])
async def replay_workflow(
    instance_id: str,
    payload: ReplayRequest,
    ctx: RequestContext = Depends(request_context_dependency),
    settings: GatewaySettings = Depends(get_settings),
):
    """Replay from a checkpoint."""
    url = f"{settings.orchestrator_url}/v1/instances/{instance_id}/replay"
    headers = _build_forward_headers(ctx)
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload.dict(), headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

# ---------------------------------------------------------------------------
# Human-in-the-Loop (HITL) Endpoints
# ---------------------------------------------------------------------------
class ApprovalRequest(BaseModel):
    comment: str

@router.post("/hitls/{session_id}/approve", tags=["hitl"])
async def approve_hitl(
    session_id: str,
    payload: ApprovalRequest,
    ctx: RequestContext = Depends(request_context_dependency),
    settings: GatewaySettings = Depends(get_settings),
):
    """Approve a human‑in‑the‑loop request."""
    url = f"{settings.orchestrator_url}/v1/hitls/{session_id}/approve"
    headers = _build_forward_headers(ctx)
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload.dict(), headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

class RejectionRequest(BaseModel):
    reason: str

@router.post("/hitls/{session_id}/reject", tags=["hitl"])
async def reject_hitl(
    session_id: str,
    payload: RejectionRequest,
    ctx: RequestContext = Depends(request_context_dependency),
    settings: GatewaySettings = Depends(get_settings),
):
    """Reject a HITL request."""
    url = f"{settings.orchestrator_url}/v1/hitls/{session_id}/reject"
    headers = _build_forward_headers(ctx)
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload.dict(), headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
