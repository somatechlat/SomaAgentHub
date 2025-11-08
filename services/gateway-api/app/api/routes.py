"""HTTP routes for the Gateway API."""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from httpx import AsyncClient, HTTPError

from ..config import GatewaySettings, get_sah_settings
from ..core.metrics import observe_forward_latency, record_moderation_decision
from ..core.moderation import ModerationError, ModerationGuard
from ..dependencies import moderation_guard_dependency, request_context_dependency
from ..models.context import RequestContext
from ..models.sessions import ModerationDetail, SessionCreateRequest, SessionCreateResponse
from .dashboard import router as dashboard_router
from .capsules import router as capsules_router
from pydantic import BaseModel, Field
from ..config import GatewaySettings, get_sah_settings

router = APIRouter(prefix="/v1", tags=["gateway"])


@router.get("/status")
def read_status(ctx: RequestContext = Depends(request_context_dependency)) -> dict[str, str]:
    """Return gateway status plus basic request context."""

    return {
        "service": "gateway",
        "state": "ready",
        "tenant": ctx.tenant_id,
        "client_type": ctx.client_type,
        "deployment_mode": ctx.deployment_mode,
    }


def _build_orchestrator_payload(
    payload: SessionCreateRequest,
    ctx: RequestContext,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "prompt": payload.prompt,
        "capsule_id": payload.capsule_id,
        "metadata": payload.metadata,
        # Orchestrator expects 'tenant' and 'user' field names
        "tenant": ctx.tenant_id,
        "user": ctx.user_id,
        "capabilities": ctx.capabilities,
        "client_type": ctx.client_type,
        "deployment_mode": ctx.deployment_mode,
    }
    return data


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


@router.post("/sessions", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreateRequest,
    ctx: RequestContext = Depends(request_context_dependency),
    guard: ModerationGuard = Depends(moderation_guard_dependency),
    settings: GatewaySettings = Depends(get_sah_settings),
) -> SessionCreateResponse:
    """Moderate input before forwarding to orchestrator."""

    if settings.kill_switch_enabled:
        record_moderation_decision(ctx.tenant_id, "kill_switch", False, 0)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gateway kill-switch active",
        )

    try:
        verdict = await guard.evaluate(ctx, payload.prompt)
    except ModerationError as exc:
        record_moderation_decision(ctx.tenant_id, "error", False, 0)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    if not verdict.allowed:
        record_moderation_decision(
            ctx.tenant_id,
            "blocked",
            bool(verdict.flagged_terms),
            verdict.strike_delta,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Content blocked by moderation",
                "strike_count": verdict.strike_count,
                "flagged_terms": verdict.flagged_terms,
                "reasons": verdict.reasons,
            },
        )

    forward_payload = _build_orchestrator_payload(payload, ctx)
    headers = _build_forward_headers(ctx)

    record_moderation_decision(
        ctx.tenant_id,
        "allowed",
        bool(verdict.flagged_terms),
        verdict.strike_delta,
    )

    start = time.perf_counter()
    async with AsyncClient(timeout=15.0) as client:
        try:
            # Forward the prepared payload to the Orchestrator
            resp = await client.post(
                f"{settings.orchestrator_url}/v1/sessions/start",
                json=forward_payload,
                headers=headers,
            )
        except HTTPError as exc:  # noqa: BLE001
            observe_forward_latency(ctx.tenant_id, time.perf_counter() - start)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Orchestrator unreachable: {exc}",
            ) from exc

    if resp.status_code >= 400:
        observe_forward_latency(ctx.tenant_id, time.perf_counter() - start)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Orchestrator error: {resp.text}",
        )

    orchestrator_data: dict[str, Any] = resp.json()
    observe_forward_latency(ctx.tenant_id, time.perf_counter() - start)
    moderation = ModerationDetail(
        strike_count=verdict.strike_count,
        flagged_terms=verdict.flagged_terms,
        reasons=verdict.reasons,
        bypassed=verdict.bypassed,
    )

    return SessionCreateResponse(
        session_id=str(orchestrator_data.get("session_id", "")),
        status=str(orchestrator_data.get("status", "accepted")),
        moderation=moderation,
        payload=orchestrator_data,
    )


class BuildCostPrecheckRequest(BaseModel):
    project_id: str = Field(..., description="Project identifier")
    tenant: str | None = Field(default=None, description="Tenant ID (defaults from context)")
    gpu_model: str | None = Field(default=None)
    region: str | None = Field(default=None)
    hours_planned: float = Field(..., gt=0)
    quantity: int = Field(default=1, ge=1)
    budget_cap: float = Field(..., gt=0)
    payment_approved: bool = Field(default=False)
    required_feature: str | None = Field(default=None)
    current_agents: int = Field(default=0, ge=0)


class BuildCostPrecheckResponse(BaseModel):
    within_budget: bool
    estimated_cost: float
    currency: str | None
    policy_decision: dict | None
    require_payment: bool
    recommended_action: str | None


@router.post("/build/cost-precheck", response_model=BuildCostPrecheckResponse, tags=["build"])
async def build_cost_precheck(
    payload: BuildCostPrecheckRequest,
    ctx: RequestContext = Depends(request_context_dependency),
    settings: GatewaySettings = Depends(get_sah_settings),
) -> BuildCostPrecheckResponse:
    pricing_url = settings.orchestrator_url  # orchestrator aggregates precheck logic too
    # Prefer calling orchestrator precheck so policy stays central
    url = pricing_url.rstrip("/") + "/v1/build/precheck"

    tenant = payload.tenant or ctx.tenant_id
    body = {
        "tenant": tenant,
        "project_id": payload.project_id,
        "gpu_model": payload.gpu_model,
        "region": payload.region,
        "hours_planned": payload.hours_planned,
        "quantity": payload.quantity,
        "budget_cap": payload.budget_cap,
        "payment_approved": payload.payment_approved,
        "required_feature": payload.required_feature,
        "current_agents": payload.current_agents,
    }
    # Remove None entries
    body = {k: v for k, v in body.items() if v is not None}

    headers = _build_forward_headers(ctx)
    start = time.perf_counter()
    async with AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(url, json=body, headers=headers)
        except HTTPError as exc:
            observe_forward_latency(ctx.tenant_id, time.perf_counter() - start)
            raise HTTPException(status_code=502, detail=f"Precheck unreachable: {exc}") from exc
    observe_forward_latency(ctx.tenant_id, time.perf_counter() - start)
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data = resp.json()
    return BuildCostPrecheckResponse(
        within_budget=bool(data.get("within_budget", False)),
        estimated_cost=float(data.get("estimated_cost", 0.0)),
        currency=data.get("currency"),
        policy_decision=data.get("policy_decision"),
        require_payment=bool(data.get("require_payment", False)),
        recommended_action=data.get("recommended_action"),
    )


class BuildRunStartRequest(BaseModel):
    project_id: str
    pricing_snapshot_id: str
    budget_cap: float
    estimated_cost: float
    template_set: str = "default"
    policy_reason: str | None = None
    tenant: str | None = None


class BuildRunStartResponse(BaseModel):
    build_run_id: str
    status: str


@router.post("/build/run", response_model=BuildRunStartResponse, tags=["build"])
async def start_build_run(
    payload: BuildRunStartRequest,
    ctx: RequestContext = Depends(request_context_dependency),
    settings: GatewaySettings = Depends(get_sah_settings),
) -> BuildRunStartResponse:
    orchestrator_url = settings.orchestrator_url.rstrip("/") + "/v1/build-runs"
    tenant = payload.tenant or ctx.tenant_id
    body = {
        "tenant": tenant,
        "project_id": payload.project_id,
        "pricing_snapshot_id": payload.pricing_snapshot_id,
        "budget_cap": payload.budget_cap,
        "estimated_cost": payload.estimated_cost,
        "template_set": payload.template_set,
        "policy_reason": payload.policy_reason or "",
    }
    headers = _build_forward_headers(ctx)
    start = time.perf_counter()
    async with AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(orchestrator_url, json=body, headers=headers)
        except HTTPError as exc:
            observe_forward_latency(ctx.tenant_id, time.perf_counter() - start)
            raise HTTPException(status_code=502, detail=f"Orchestrator unreachable: {exc}") from exc
    observe_forward_latency(ctx.tenant_id, time.perf_counter() - start)
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    br = resp.json()
    return BuildRunStartResponse(build_run_id=str(br.get("id")), status=str(br.get("status")))

router.include_router(dashboard_router)
router.include_router(capsules_router)
