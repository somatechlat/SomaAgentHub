"""Agent One Sight dashboard endpoints."""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from ..config import get_settings
from ..dependencies import request_context_dependency
from ..models.context import RequestContext
from services.common.config.base_settings import resolve_env

router = APIRouter(prefix="/v1/dashboard", tags=["dashboard"])


async def fetch_json(url: str) -> dict[str, Any]:
    async with httpx.AsyncClient(
    timeout=httpx.Timeout(5.0, read=5.0, connect=3.0),
    limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
    ) as client:
        resp = await client.get(url)
    if resp.status_code >= 400:
        raise HTTPException(
    status_code=status.HTTP_502_BAD_GATEWAY,
    detail=f"Failed to fetch {url}: {resp.text}",
    )
    return resp.json()


    @router.get("/health")
    async def dashboard_health(
    ctx: RequestContext = Depends(request_context_dependency),
    ) -> dict[str, Any]:
    settings = get_settings()
    extra = settings.model_extra or {}
    llm_health_url = str(
    extra.get("LLM_HUB_HEALTH_URL")
    or resolve_env("LLM_HUB_HEALTH_URL", "http://llm-hub:10022/health")
    )
    default_port = resolve_env("MEMORY_GATEWAY_PORT", "10021")
    somabrain_metrics_url = str(
    extra.get("SOMABRAIN_METRICS_URL")
    or resolve_env(
    "SOMABRAIN_METRICS_URL",
    f"http://memory-gateway:{default_port}/metrics",
    )
    )
    kafka_endpoint = (
    settings.kafka.bootstrap_servers[0]
    if settings.kafka.bootstrap_servers
    else "kafka:9092"
    )
    postgres_host = extra.get("POSTGRES_HOST") or resolve_env(
    "POSTGRES_HOST", "postgres:5432"
    )
    if settings.redis.host and settings.redis.port:
        redis_host = f"{settings.redis.host}:{settings.redis.port}"
    elif settings.redis.url:
        redis_host = settings.redis.url
    else:
        redis_host = "redis:6379"

    try:
        llm_hub_health = await fetch_json(llm_health_url)
    except HTTPException as exc:
        llm_hub_health = {"status": "error", "detail": exc.detail}

    return {
    "tenant": ctx.tenant_id,
    "deployment_mode": ctx.deployment_mode,
    "services": {
    "llm_hub": llm_hub_health,
    "somabrain": somabrain_metrics_url,
    "kafka": kafka_endpoint,
    "postgres": postgres_host,
    "redis": redis_host,
    },
    }
