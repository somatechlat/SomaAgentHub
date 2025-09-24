"""Agent One Sight dashboard endpoints."""

from __future__ import annotations

from typing import Any, Dict

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import request_context_dependency
from ..models.context import RequestContext
from ..core.config import get_settings

router = APIRouter(prefix="/v1/dashboard", tags=["dashboard"])


async def fetch_json(url: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
    if resp.status_code >= 400:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to fetch {url}: {resp.text}")
    return resp.json()


@router.get("/health")
async def dashboard_health(ctx: RequestContext = Depends(request_context_dependency)) -> Dict[str, Any]:
    settings = get_settings()
    try:
        slm_health = await fetch_json("http://localhost:8700/v1/health")
    except HTTPException as exc:
        slm_health = {"status": "error", "detail": exc.detail}

    data = {
        "tenant": ctx.tenant_id,
        "deployment_mode": ctx.deployment_mode,
        "services": {
            "slm": slm_health,
            "somabrain": "http://localhost:9696/metrics",
            "kafka": "localhost:9092",
            "postgres": "localhost:5432",
            "redis": "localhost:6379",
        },
    }
    return data
