"""Capsule run endpoints for the Gateway API.

Forwards capsule execution requests to the Orchestrator service.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from httpx import AsyncClient, HTTPError
from pydantic import BaseModel, Field

from ..config import GatewaySettings, get_settings
from ..dependencies import request_context_dependency
from ..models.context import RequestContext

router = APIRouter(tags=["capsules"])


class CapsuleRunRequest(BaseModel):
    params: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


    class CapsuleRunResponse(BaseModel):
    workflow_id: str
    run_id: str | None = None
    task_queue: str
    capsule_id: str
    version: str


    @router.post(
    "/v1/capsules/{capsule_id}/{version}/run",
    response_model=CapsuleRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    )
    async def start_capsule_run(
    capsule_id: str,
    version: str,
    payload: CapsuleRunRequest,
    ctx: RequestContext = Depends(request_context_dependency),
    settings: GatewaySettings = Depends(get_settings),
    ) -> CapsuleRunResponse:
    """Forward a capsule run request to the orchestrator."""

    forward = {
    "tenant": ctx.tenant_id,
    "user": ctx.user_id or "anonymous",
    "capsule_id": capsule_id,
    "version": version,
    "params": payload.params,
    "metadata": payload.metadata,
    }

    async with AsyncClient(timeout=15.0) as client:
        try:
    resp = await client.post(
        f"{settings.orchestrator_url}/v1/capsule/run", json=forward
    )
    except HTTPError as exc:  # noqa: BLE001
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Orchestrator unreachable: {exc}",
    ) from exc

    if resp.status_code >= 400:
        raise HTTPException(
    status_code=status.HTTP_502_BAD_GATEWAY,
    detail=f"Orchestrator error: {resp.text}",
    )

    return CapsuleRunResponse(**resp.json())
