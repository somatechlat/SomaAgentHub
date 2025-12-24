"""Gateway endpoints implemented with Django Ninja."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
from django.conf import settings
from django.http import HttpResponse
from ninja import Router
from ninja.errors import HttpError
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

from admin.common.messages import get_message
from services.common.models.agent import AgentSpec, CrewSpec
from services.common.models.workflow import GraphWorkflow

from .context import RequestContext, get_request_context

logger = logging.getLogger(__name__)

router = Router(tags=["gateway"])


@router.get("/status")
async def read_status(request) -> dict[str, Any]:
    """Return gateway status plus basic request context."""
    ctx = get_request_context(request)
    return {
        "service": "gateway",
        "state": "ready",
        "tenant": ctx.tenant_id,
        "client_type": ctx.client_type,
        "deployment_mode": ctx.deployment_mode,
    }


@router.get("/status/aggregate")
async def aggregate_status(request) -> dict[str, Any]:
    """Query health endpoints of all downstream services and return a summary."""
    ctx = get_request_context(request)
    service_urls = {
        "orchestrator": settings.ORCHESTRATOR_URL,
        "identity": settings.IDENTITY_URL,
        "policy": settings.POLICY_ENGINE_URL,
        "memory_gateway": settings.MEMORY_GATEWAY_URL,
        "llm_hub": settings.LLM_HUB_URL,
    }

    async def fetch(name: str, url: str) -> tuple[str, dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{url.rstrip('/')}/health")
                if resp.status_code == 200:
                    return name, resp.json()
                return (
                    name,
                    {
                        "status": "unhealthy",
                        "service": url,
                        "message": get_message(
                            "gateway.aggregate.unhealthy_status",
                            code=resp.status_code,
                            service=name,
                        ),
                    },
                )
        except Exception as exc:
            logger.warning("Health check failed for %s at %s: %s", name, url, exc)
            return (
                name,
                {
                    "status": "unhealthy",
                    "service": url,
                    "message": get_message("gateway.aggregate.unreachable", service=name),
                },
            )

    results = await asyncio.gather(*(fetch(name, url) for name, url in service_urls.items()))
    aggregated = {name: result for name, result in results}
    aggregated["gateway"] = {
        "status": "ok",
        "service": "gateway",
        "tenant": ctx.tenant_id,
        "client_type": ctx.client_type,
        "deployment_mode": ctx.deployment_mode,
    }
    return aggregated


def _error(service: str, code: int, detail: str) -> HttpError:
    return HttpError(code, detail or get_message("gateway.forward.error", service=service))


async def _forward_json(
    service: str,
    url: str,
    ctx: RequestContext,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    expected: tuple[int, ...] = (200, 201, 202),
) -> Any:
    """Forward JSON request to a downstream service with context headers."""
    headers = ctx.as_headers()
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.request(method, url, json=payload, headers=headers)
    except httpx.HTTPError as exc:  # noqa: BLE001
        raise HttpError(502, get_message("gateway.forward.unreachable", service=service)) from exc

    if resp.status_code in expected:
        if resp.content:
            return resp.json()
        return None

    if resp.status_code == 404:
        raise HttpError(404, get_message("gateway.forward.not_found", service=service))

    raise _error(service, resp.status_code, resp.text)


# ---------------------------------------------------------------------------
# Agent / Crew Endpoints
# ---------------------------------------------------------------------------
@router.post("/agents", tags=["agents"])
async def create_agent(request, agent: AgentSpec):
    ctx = get_request_context(request)
    url = f"{settings.ORCHESTRATOR_URL.rstrip('/')}/v1/agents"
    return await _forward_json("orchestrator", url, ctx, method="POST", payload=agent.dict())


@router.get("/agents/{agent_id}", tags=["agents"])
async def get_agent(request, agent_id: str):
    ctx = get_request_context(request)
    url = f"{settings.ORCHESTRATOR_URL.rstrip('/')}/v1/agents/{agent_id}"
    return await _forward_json("orchestrator", url, ctx)


@router.put("/agents/{agent_id}", tags=["agents"])
async def update_agent(request, agent_id: str, agent: AgentSpec):
    ctx = get_request_context(request)
    url = f"{settings.ORCHESTRATOR_URL.rstrip('/')}/v1/agents/{agent_id}"
    return await _forward_json("orchestrator", url, ctx, method="PUT", payload=agent.dict())


@router.post("/crews", tags=["crews"])
async def create_crew(request, crew: CrewSpec):
    ctx = get_request_context(request)
    url = f"{settings.ORCHESTRATOR_URL.rstrip('/')}/v1/crews"
    return await _forward_json("orchestrator", url, ctx, method="POST", payload=crew.dict())


# ---------------------------------------------------------------------------
# Workflow Endpoints
# ---------------------------------------------------------------------------
class ExecuteWorkflowRequest(BaseModel):
    input: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.post("/workflows", tags=["workflows"])
async def register_workflow(request, workflow: GraphWorkflow):
    ctx = get_request_context(request)
    url = f"{settings.ORCHESTRATOR_URL.rstrip('/')}/v1/workflows"
    return await _forward_json("orchestrator", url, ctx, method="POST", payload=workflow.dict())


@router.post("/workflows/{workflow_id}/execute", tags=["workflows"])
async def execute_workflow(request, workflow_id: str, payload: ExecuteWorkflowRequest):
    ctx = get_request_context(request)
    url = f"{settings.ORCHESTRATOR_URL.rstrip('/')}/v1/workflows/{workflow_id}/execute"
    return await _forward_json("orchestrator", url, ctx, method="POST", payload=payload.dict())


@router.get("/instances/{instance_id}", tags=["workflows"])
async def get_instance(request, instance_id: str):
    ctx = get_request_context(request)
    url = f"{settings.ORCHESTRATOR_URL.rstrip('/')}/v1/instances/{instance_id}"
    return await _forward_json("orchestrator", url, ctx)


class ReplayRequest(BaseModel):
    checkpoint_id: str = Field(..., alias="checkpointId")
    overrides: dict[str, Any] = Field(default_factory=dict)


@router.post("/instances/{instance_id}/replay", tags=["workflows"])
async def replay_workflow(request, instance_id: str, payload: ReplayRequest):
    ctx = get_request_context(request)
    url = f"{settings.ORCHESTRATOR_URL.rstrip('/')}/v1/instances/{instance_id}/replay"
    return await _forward_json("orchestrator", url, ctx, method="POST", payload=payload.dict(by_alias=True))


# ---------------------------------------------------------------------------
# HITL Endpoints
# ---------------------------------------------------------------------------
class ApprovalRequest(BaseModel):
    comment: str


@router.post("/hitls/{session_id}/approve", tags=["hitl"])
async def approve_hitl(request, session_id: str, payload: ApprovalRequest):
    ctx = get_request_context(request)
    url = f"{settings.ORCHESTRATOR_URL.rstrip('/')}/v1/hitls/{session_id}/approve"
    return await _forward_json("orchestrator", url, ctx, method="POST", payload=payload.dict())


class RejectionRequest(BaseModel):
    reason: str


@router.post("/hitls/{session_id}/reject", tags=["hitl"])
async def reject_hitl(request, session_id: str, payload: RejectionRequest):
    ctx = get_request_context(request)
    url = f"{settings.ORCHESTRATOR_URL.rstrip('/')}/v1/hitls/{session_id}/reject"
    return await _forward_json("orchestrator", url, ctx, method="POST", payload=payload.dict())


# ---------------------------------------------------------------------------
# Capsule Endpoints
# ---------------------------------------------------------------------------
class CapsuleRunRequest(BaseModel):
    params: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.post("/capsules/{capsule_id}/{version}/run", tags=["capsules"])
async def start_capsule_run(request, capsule_id: str, version: str, payload: CapsuleRunRequest):
    ctx = get_request_context(request)
    forward = {
        "tenant": ctx.tenant_id,
        "user": ctx.user_id or "anonymous",
        "capsule_id": capsule_id,
        "version": version,
        "params": payload.params,
        "metadata": payload.metadata,
    }
    url = f"{settings.ORCHESTRATOR_URL.rstrip('/')}/v1/capsule/run"
    return await _forward_json("orchestrator", url, ctx, method="POST", payload=forward)


# ---------------------------------------------------------------------------
# System endpoints
# ---------------------------------------------------------------------------
@router.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", tags=["system"])
async def ready() -> dict[str, str]:
    return {"status": "ready"}


@router.get("/healthz", tags=["system"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/metrics", tags=["system"])
def metrics():
    """Expose Prometheus metrics."""
    data = generate_latest()
    return HttpResponse(data, content_type=CONTENT_TYPE_LATEST)


@router.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {"message": "SomaAgentHub Django Gateway v2"}
