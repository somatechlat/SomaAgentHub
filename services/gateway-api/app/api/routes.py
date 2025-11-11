"""HTTP routes for the Gateway API."""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
import httpx
from pydantic import BaseModel, Field

from ..config import GatewaySettings, get_sah_settings
from ..core.metrics import observe_forward_latency, record_moderation_decision
from ..core.moderation import ModerationError, ModerationGuard
from ..dependencies import moderation_guard_dependency, request_context_dependency
from ..models.context import RequestContext
from ..models.sessions import (
    ModerationDetail,
    SessionCreateRequest,
    SessionCreateResponse,
)
from .capsules import router as capsules_router
from .dashboard import router as dashboard_router
from services.common.config.base_settings import resolve_env

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


@router.post(
    "/sessions",
    response_model=SessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
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
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

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
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            # Forward the prepared payload to the Orchestrator
            resp = await client.post(
                f"{settings.orchestrator_url}/v1/sessions/start",
                json=forward_payload,
                headers=headers,
            )
        except httpx.HTTPError as exc:  # noqa: BLE001
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
    tenant: str | None = Field(
        default=None, description="Tenant ID (defaults from context)"
    )
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


@router.post(
    "/build/cost-precheck", response_model=BuildCostPrecheckResponse, tags=["build"]
)
async def build_cost_precheck(
    payload: BuildCostPrecheckRequest,
    ctx: RequestContext = Depends(request_context_dependency),
    settings: GatewaySettings = Depends(get_sah_settings),
) -> BuildCostPrecheckResponse:
    pricing_url = (
        settings.orchestrator_url
    )  # orchestrator aggregates precheck logic too
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
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(url, json=body, headers=headers)
        except httpx.HTTPError as exc:
            observe_forward_latency(ctx.tenant_id, time.perf_counter() - start)
            raise HTTPException(
                status_code=502, detail=f"Precheck unreachable: {exc}"
            ) from exc
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
    pricing_snapshot_id: str | None = None
    budget_cap: float
    estimated_cost: float
    template_set: str = "default"
    policy_reason: str | None = None
    tenant: str | None = None
    requires_reaccept: bool | None = Field(
        default=None, description="If true, user must reaccept after reconcile drift"
    )


class BuildRunStartResponse(BaseModel):
    build_run_id: str
    status: str
    pricing_snapshot_id: str | None = None
    requires_reaccept: bool | None = None


@router.post("/build/run", response_model=BuildRunStartResponse, tags=["build"])
async def start_build_run(
    payload: BuildRunStartRequest,
    ctx: RequestContext = Depends(request_context_dependency),
    settings: GatewaySettings = Depends(get_sah_settings),
) -> BuildRunStartResponse:
    orchestrator_url = settings.orchestrator_url.rstrip("/") + "/v1/build-runs"
    # Auto-create snapshot if client didn't supply one
    snapshot_id = payload.pricing_snapshot_id
    if not snapshot_id:
        # We call pricing service through gateway network; orchestrator URL won't expose pricing.
        # Adjust to pricing service if directly reachable.
        pricing_direct = getattr(
            settings, "pricing_service_url", "http://pricing-service:10026"
        )
        snapshot_ep = pricing_direct.rstrip("/") + "/v1/pricing/snapshot"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp_snap = await client.post(snapshot_ep)
                if resp_snap.status_code == 200:
                    snapshot_id = resp_snap.json().get("snapshot_id")
                else:
                    raise HTTPException(
                        status_code=502,
                        detail=f"Snapshot creation failed: {resp_snap.text}",
                    )
            except HTTPError as exc:
                raise HTTPException(
                    status_code=502, detail=f"Snapshot request error: {exc}"
                ) from exc
    tenant = payload.tenant or ctx.tenant_id
    body = {
        "tenant": tenant,
        "project_id": payload.project_id,
        "pricing_snapshot_id": snapshot_id,
        "budget_cap": payload.budget_cap,
        "estimated_cost": payload.estimated_cost,
        "template_set": payload.template_set,
        "policy_reason": payload.policy_reason or "",
    }
    headers = _build_forward_headers(ctx)
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(orchestrator_url, json=body, headers=headers)
        except httpx.HTTPError as exc:
            observe_forward_latency(ctx.tenant_id, time.perf_counter() - start)
            raise HTTPException(
                status_code=502, detail=f"Orchestrator unreachable: {exc}"
            ) from exc
    observe_forward_latency(ctx.tenant_id, time.perf_counter() - start)
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    br = resp.json()
    return BuildRunStartResponse(
        build_run_id=str(br.get("id")),
        status=str(br.get("status")),
        pricing_snapshot_id=snapshot_id,
        requires_reaccept=payload.requires_reaccept,
    )


class LiveSummaryResponse(BaseModel):
    snapshot_id: str
    estimated_total: float
    currency: str | None = None
    hours_planned: float | None = None
    gpu_model: str | None = None
    budget_cap: float | None = None
    within_budget: bool | None = None


@router.get(
    "/pricing/live-summary", response_model=LiveSummaryResponse, tags=["pricing"]
)
async def pricing_live_summary(
    hours_planned: float | None = None,
    gpu_model: str | None = None,
    budget_cap: float | None = None,
    ctx: RequestContext = Depends(request_context_dependency),
    settings: GatewaySettings = Depends(get_sah_settings),
):
    pricing_service = getattr(
        settings, "pricing_service_url", "http://pricing-service:10026"
    )
    url = pricing_service.rstrip("/") + "/v1/pricing/live-summary"
    params = {}
    if hours_planned is not None:
        params["hours_planned"] = hours_planned
    if gpu_model is not None:
        params["gpu_model"] = gpu_model
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data = resp.json()
    snapshot_id = data.get("snapshot_id") or data.get("id") or "unknown"
    est_total = float(data.get("estimated_total", data.get("total", 0.0)))
    within_budget = None
    if budget_cap is not None:
        within_budget = est_total <= budget_cap
    return LiveSummaryResponse(
        snapshot_id=snapshot_id,
        estimated_total=est_total,
        currency=data.get("currency"),
        hours_planned=hours_planned,
        gpu_model=gpu_model,
        budget_cap=budget_cap,
        within_budget=within_budget,
    )


class ReconcileRequest(BaseModel):
    snapshot_id: str
    billing_quantity: int = Field(default=1, ge=1)
    hours_actual: float | None = None
    gpu_model: str | None = None
    budget_cap: float | None = None


class ReconcileResponse(BaseModel):
    snapshot_id: str
    reconciled_total: float
    estimated_total: float
    drift_ratio: float | None
    currency: str | None = None
    requires_reaccept: bool
    within_budget: bool | None


@router.post("/pricing/reconcile", response_model=ReconcileResponse, tags=["pricing"])
async def pricing_reconcile(
    payload: ReconcileRequest,
    ctx: RequestContext = Depends(request_context_dependency),
    settings: GatewaySettings = Depends(get_sah_settings),
):
    pricing_service = getattr(
        settings, "pricing_service_url", "http://pricing-service:10026"
    )
    url = pricing_service.rstrip("/") + "/v1/pricing/reconcile"
    body = {
        "snapshot_id": payload.snapshot_id,
        "billing_quantity": payload.billing_quantity,
    }
    if payload.hours_actual is not None:
        body["hours_actual"] = payload.hours_actual
    if payload.gpu_model is not None:
        body["gpu_model"] = payload.gpu_model
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json=body)
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data = resp.json()
    reconciled = float(data.get("reconciled_total", data.get("total", 0.0)))
    estimated = float(
        data.get("estimated_total", data.get("original_total", reconciled))
    )
    drift_ratio = None
    if estimated > 0:
        drift_ratio = (reconciled - estimated) / estimated
    requires_reaccept = False
    if (
        drift_ratio is not None and abs(drift_ratio) > 0.2
    ):  # threshold aligned with policy
        requires_reaccept = True
    within_budget = None
    if payload.budget_cap is not None:
        within_budget = reconciled <= payload.budget_cap
    return ReconcileResponse(
        snapshot_id=payload.snapshot_id,
        reconciled_total=reconciled,
        estimated_total=estimated,
        drift_ratio=drift_ratio,
        currency=data.get("currency"),
        requires_reaccept=requires_reaccept,
        within_budget=within_budget,
    )


router.include_router(dashboard_router)
router.include_router(capsules_router)
