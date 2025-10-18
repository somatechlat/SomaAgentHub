"""Agent One Sight dashboard endpoints."""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from ..config import get_sah_settings
from ..dependencies import request_context_dependency
from ..models.context import RequestContext

router = APIRouter(prefix="/v1/dashboard", tags=["dashboard"])


async def fetch_json(url: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, read=5.0, connect=3.0), limits=httpx.Limits(max_connections=50, max_keepalive_connections=20)) as client:
        resp = await client.get(url)
    if resp.status_code >= 400:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to fetch {url}: {resp.text}")
    return resp.json()


@router.get("/health")
async def dashboard_health(ctx: RequestContext = Depends(request_context_dependency)) -> dict[str, Any]:
    settings = get_sah_settings()
    extra = settings.model_extra or {}
    slm_health_url = extra.get("SLM_HEALTH_URL") or os.getenv("SLM_HEALTH_URL", "http://slm-service:10022/health")
    somabrain_metrics_url = extra.get("SOMABRAIN_METRICS_URL") or os.getenv("SOMABRAIN_METRICS_URL", "http://memory-gateway:9696/metrics")
    kafka_endpoint = settings.kafka.bootstrap_servers[0] if settings.kafka.bootstrap_servers else "kafka:9092"
    postgres_host = extra.get("SOMASTACK_POSTGRES_HOST") or "postgres:5432"
    if settings.redis.host and settings.redis.port:
        redis_host = f"{settings.redis.host}:{settings.redis.port}"
    elif settings.redis.url:
        redis_host = settings.redis.url
    else:
        redis_host = "redis:6379"

    try:
        somallm_health = await fetch_json(slm_health_url)
    except HTTPException as exc:
        somallm_health = {"status": "error", "detail": exc.detail}

    data = {
        "tenant": ctx.tenant_id,
        "deployment_mode": ctx.deployment_mode,
        "services": {
            "slm_service": somallm_health,
            "somabrain": somabrain_metrics_url,
            "kafka": kafka_endpoint,
            "postgres": postgres_host,
            "redis": redis_host,
        },
    }
    return data
