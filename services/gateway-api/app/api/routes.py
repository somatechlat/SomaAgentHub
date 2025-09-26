"""HTTP routes for the Gateway API."""

from __future__ import annotations

from typing import Any, Dict

import time

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from ..core.config import Settings, get_settings
from ..core.moderation import ModerationError, ModerationGuard
from ..core.metrics import observe_forward_latency, record_moderation_decision
from ..dependencies import moderation_guard_dependency, request_context_dependency
from ..models.context import RequestContext
from ..models.sessions import ModerationDetail, SessionCreateRequest, SessionCreateResponse
from .dashboard import router as dashboard_router

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
) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "prompt": payload.prompt,
        "capsule_id": payload.capsule_id,
        "metadata": payload.metadata,
        "tenant_id": ctx.tenant_id,
        "user_id": ctx.user_id,
        "capabilities": ctx.capabilities,
        "client_type": ctx.client_type,
        "deployment_mode": ctx.deployment_mode,
    }
    return data


def _build_forward_headers(ctx: RequestContext) -> Dict[str, str]:
    headers = {
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
    settings: Settings = Depends(get_settings),
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
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
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

    orchestrator_data: Dict[str, Any] = resp.json()
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

router.include_router(dashboard_router)
