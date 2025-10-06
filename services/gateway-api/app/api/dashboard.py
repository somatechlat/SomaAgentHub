"""Agent One Sight dashboard endpoints."""

from __future__ import annotations

from typing import Any, Dict

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
import os

from ..dependencies import request_context_dependency
from ..models.context import RequestContext
# --- configuration for external services (Kubernetes DNS names) ---
SOMALLM_PROVIDER_HEALTH_URL = (
    os.getenv("SOMALLM_PROVIDER_HEALTH_URL")
    or os.getenv("SLM_HEALTH_URL", "http://somallm-provider:8000/v1/health")
)
SOMABRAIN_METRICS_URL = os.getenv("SOMABRAIN_METRICS_URL", "http://memory-gateway:9696/metrics")
KAFKA_HOST = os.getenv("KAFKA_HOST", "kafka:9092")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres:5432")
REDIS_HOST = os.getenv("REDIS_HOST", "redis:6379")

router = APIRouter(prefix="/v1/dashboard", tags=["dashboard"])


async def fetch_json(url: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
    if resp.status_code >= 400:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to fetch {url}: {resp.text}")
    return resp.json()


@router.get("/health")
async def dashboard_health(ctx: RequestContext = Depends(request_context_dependency)) -> Dict[str, Any]:
    try:
        somallm_health = await fetch_json(SOMALLM_PROVIDER_HEALTH_URL)
    except HTTPException as exc:
        somallm_health = {"status": "error", "detail": exc.detail}

    data = {
        "tenant": ctx.tenant_id,
        "deployment_mode": ctx.deployment_mode,
        "services": {
            "somallm_provider": somallm_health,
            "somabrain": SOMABRAIN_METRICS_URL,
            "kafka": KAFKA_HOST,
            "postgres": POSTGRES_HOST,
            "redis": REDIS_HOST,
        },
    }
    return data
