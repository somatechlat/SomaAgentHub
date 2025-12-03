"""Entry point for the SomaAgentHub (SAH) service."""

from __future__ import annotations

import asyncio
import logging
import importlib
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from services.common.fastapi.bootstrap import create_app
from services.common.spiffe_auth import init_spiffe

# Import app-local modules
api_router = importlib.import_module("app.api.routes").router
get_settings = importlib.import_module("app.config").get_settings
ContextMiddleware = importlib.import_module("app.core.middleware").ContextMiddleware
close_redis_client = importlib.import_module("app.core.redis").close_redis_client
get_redis_client = importlib.import_module("app.core.redis").get_redis_client

logger = logging.getLogger(__name__)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize SPIFFE early
    spiffe_identity = init_spiffe(settings.service_name or "sah")
    if spiffe_identity:
        logger.info("SPIFFE identity loaded", extra={"spiffe_id": spiffe_identity.spiffe_id})
    else:
        logger.info("SPIFFE identity not initialized; falling back to non-mTLS workload identity")

    yield
    # Shutdown: ensure Redis client closes cleanly
    await close_redis_client()

def _attach_routes(app: FastAPI) -> None:
    app.add_middleware(ContextMiddleware)
    app.include_router(api_router)

    @app.get("/healthz", tags=["system"])
    async def healthz() -> dict[str, Any]:
        kafka_ok, auth_ok, redis_ok = await asyncio.gather(
            _check_kafka(),
            _check_auth(),
            _check_redis(),
        )
        status = kafka_ok and auth_ok and redis_ok
        return {
            "status": "ok" if status else "degraded",
            "checks": {
                "kafka": kafka_ok,
                "auth": auth_ok,
                "redis": redis_ok,
            },
        }

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, Any]:
        return await healthz()

    @app.get("/ready", tags=["system"])
    async def ready() -> dict[str, Any]:
        health = await healthz()
        return {"status": health["status"], "details": health["checks"]}

    @app.get("/metrics", tags=["system"])
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/")
    def root() -> dict[str, str]:
        return {"message": "SomaAgentHub Service"}

async def _check_kafka() -> bool:
    if not settings.kafka.bootstrap_servers:
        return False
    for endpoint in settings.kafka.bootstrap_servers:
        host, _, port_raw = endpoint.partition(":")
        port = int(port_raw or 9092)
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=3
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            continue
    return False

async def _check_auth() -> bool:
    if not settings.auth.url:
        return False
    url = settings.auth.url.rstrip("/") + "/health"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            return resp.status_code < 500
    except Exception:
        return False

async def _check_redis() -> bool:
    client = get_redis_client()
    return await client.health_check()

app = create_app(
    service_name=settings.service_name or "sah",
    settings=settings,
    routes_factory=_attach_routes,
    version=settings.service_version,
    instrumentation=True,
    lifespan=lifespan,
)

