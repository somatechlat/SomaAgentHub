"""FastAPI application for the SomaGent Constitution service."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .api.routes import router
from .core.cache import close_redis_client, create_redis_client
from .core.config import settings
from .core.constitution import ConstitutionRegistry, load_verified_constitution

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        verified = load_verified_constitution(settings.bundle_path, settings.public_key_path)
        redis_client = await create_redis_client(str(settings.redis_url))
        if redis_client is None:
            logger.warning("Redis unavailable; serving constitution from in-memory registry only")
        else:
            for tenant in settings.tenants:
                await redis_client.setex(f"constitution:{tenant}", settings.cache_ttl_seconds, verified.hash)
        app.state.redis_client = redis_client
        app.state.constitution_registry = ConstitutionRegistry(verified, tenants=settings.tenants)
        try:
            yield
        finally:
            await close_redis_client(redis_client)

    app = FastAPI(
        title="SomaGent Constitution Service",
        version="0.2.0",
        description="Serves the signed SomaGent constitution with cryptographic verification.",
        lifespan=lifespan,
    )

    @app.get("/health", tags=["system"])
    async def healthcheck() -> dict[str, str]:
        registry_present = hasattr(app.state, "constitution_registry")
        status = "ok" if registry_present else "degraded"
        return {"status": status, "service": settings.service_name}

    @app.get("/metrics", tags=["system"])
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "SomaGent Constitution Service"}

    app.include_router(router)
    return app


app = create_app()
