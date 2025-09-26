"""API endpoints for tool service."""

from __future__ import annotations

import math
from typing import Any, Dict, List
from uuid import uuid4

import time

from fastapi import APIRouter, Depends, Header, HTTPException, status
import httpx

from ..core.config import Settings, get_settings
from ..core.metrics import record_execution, record_rate_limit
from ..core.ratelimit import RateLimitExceeded, RateLimiter
from ..core.registry import get_adapter, list_adapters
from ..core.sandbox import SandboxRunner
from ..core.security import verify_release_signature
from ..models.tools import (
    AdapterExecuteRequest,
    AdapterExecuteResponse,
    AdapterListResponse,
    AdapterMetadata,
    ProvisionRequest,
    ProvisionResponse,
    ProvisionResult,
)

router = APIRouter(prefix="/v1", tags=["tools"])

_settings = get_settings()
_rate_limiter = RateLimiter(_settings.default_rate_limit_per_minute)
_sandbox_runner = SandboxRunner(_settings.sandbox_base_path)
_provision_logs: List[Dict[str, str]] = []


async def _emit_billing_event(
    adapter: Dict[str, Any],
    tenant_id: str,
    action: str,
    duration_seconds: float,
    tokens: int | None,
) -> None:
    analytics_url = _settings.analytics_url
    if not analytics_url:
        return

    billing_cfg = adapter.get("billing") or {}
    cost = float(billing_cfg.get("cost_per_call", 0.0))
    currency = billing_cfg.get("currency", _settings.billing_default_currency)
    service = billing_cfg.get("service", adapter.get("id", "tool-adapter"))

    if cost <= 0 and (tokens is None or tokens <= 0):
        return

    payload = {
        "tenant_id": tenant_id,
        "service": service,
        "cost": cost,
        "currency": currency,
        "tokens": tokens or 0,
        "capsule_id": billing_cfg.get("capsule_id"),
        "metadata": {
            "adapter_id": adapter.get("id"),
            "action": action,
            "duration_seconds": f"{duration_seconds:.3f}",
        },
    }

    endpoint = f"{analytics_url.rstrip('/')}/v1/billing/events"
    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            await client.post(endpoint, json=payload)
        except httpx.HTTPError:
            pass


@router.get("/adapters", response_model=AdapterListResponse)
def list_adapters_route(settings: Settings = Depends(get_settings)) -> AdapterListResponse:
    """Return available tool adapters."""

    adapters = [AdapterMetadata(**adapter) for adapter in list_adapters(settings)]
    return AdapterListResponse(adapters=adapters)


@router.post(
    "/adapters/{adapter_id}/execute",
    response_model=AdapterExecuteResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def execute_adapter(
    adapter_id: str,
    request: AdapterExecuteRequest,
    tenant_id: str = Header(..., alias="X-Tenant-ID"),
    user_id: str | None = Header(default=None, alias="X-User-ID"),
    settings: Settings = Depends(get_settings),
) -> AdapterExecuteResponse:
    """Execute adapter action within sandbox after verification and rate limiting."""

    adapter = get_adapter(adapter_id, settings)
    if adapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Adapter not found")
    if adapter.get("status") != "available":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Adapter unavailable")

    if not verify_release_signature(adapter, settings.release_signing_secret):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Adapter signature invalid")

    rate_key = f"{tenant_id}:{adapter_id}"
    start = time.perf_counter()
    try:
        remaining = _rate_limiter.check(rate_key, adapter.get("rate_limit_per_minute"))
    except RateLimitExceeded as exc:
        record_rate_limit(adapter_id, tenant_id)
        retry_after = math.ceil(exc.remaining_seconds)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
            headers={"Retry-After": str(retry_after)},
        )

    execution_metadata: Dict[str, str] = {}
    if user_id:
        execution_metadata["requested_by"] = user_id

    result = await _sandbox_runner.run(adapter, request.action, request.arguments | execution_metadata)
    duration_seconds = time.perf_counter() - start
    record_execution(adapter_id, tenant_id, result.status, duration_seconds)

    tokens = None
    if isinstance(result.output, dict):
        raw_tokens = result.output.get("tokens")
        if isinstance(raw_tokens, (int, float)):
            tokens = int(raw_tokens)

    await _emit_billing_event(adapter, tenant_id, request.action, duration_seconds, tokens)

    return AdapterExecuteResponse(
        job_id=result.job_id,
        status=result.status,
        duration_ms=result.duration_ms,
        output=result.output,
        sandbox=result.sandbox,
        signature=adapter["signature"],
        rate_limit_remaining=remaining,
    )


@router.post(
    "/provision",
    response_model=ProvisionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def provision_resources(
    request: ProvisionRequest,
    settings: Settings = Depends(get_settings),
) -> ProvisionResponse:
    if not request.actions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="actions required")

    results: List[ProvisionResult] = []
    for action in request.actions:
        job_id = str(uuid4())
        message = "dry-run" if request.dry_run else "submitted"
        results.append(
            ProvisionResult(
                tool=action.tool,
                status="simulated" if request.dry_run else "queued",
                job_id=job_id,
                message=message,
                dry_run=request.dry_run,
            )
        )

    _provision_logs.append(
        {
            "deliverable_id": request.deliverable_id,
            "tenant_id": request.tenant_id,
            "result_count": str(len(results)),
            "dry_run": str(request.dry_run).lower(),
        }
    )

    return ProvisionResponse(
        deliverable_id=request.deliverable_id,
        tenant_id=request.tenant_id,
        results=results,
    )
