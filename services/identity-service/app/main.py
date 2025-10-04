"""FastAPI application factory for the identity service."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from redis.asyncio import from_url as redis_from_url

from .api.routes import router
from .core.config import settings
from .core.storage import IdentityStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = redis_from_url(str(settings.redis_url), decode_responses=True)
    app.state.redis = redis
    app.state.identity_store = IdentityStore(redis)
    try:
        yield
    finally:
        store = getattr(app.state, "identity_store", None)
        if store is not None:
            await store.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="SomaGent Identity Service",
        version="0.2.0",
        description="Handles user authentication, JWT tokens, and identity management.",
        lifespan=lifespan,
    )

    @app.get("/health", tags=["system"])
    async def healthcheck() -> dict[str, str]:
        store: IdentityStore = app.state.identity_store
        healthy = await store.ping()
        return {"status": "ok" if healthy else "degraded", "service": settings.service_name}

    @app.get("/metrics", tags=["system"])
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "SomaGent Identity Service"}

    app.include_router(router)
    return app


app = create_app()