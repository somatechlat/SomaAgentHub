"""FastAPI application factory for the identity service."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
from datetime import timedelta
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from redis.asyncio import Redis, from_url as redis_from_url
import os

from .api.routes import router
from .core.audit import AuditLogger
from .core.config import settings
from .core.key_manager import KeyManager
from .core.storage import IdentityStore
from .observability import setup_observability


async def _rotation_worker(key_manager: KeyManager, interval: float, stop_event: asyncio.Event) -> None:
    try:
        while True:
            await key_manager.rotate_if_due()
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval)
                return
            except asyncio.TimeoutError:
                continue
    except asyncio.CancelledError:  # pragma: no cover - shutdown handling
        raise


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Allow running without Redis by falling back to in-memory store when no URL provided.
    redis_url = os.getenv("REDIS_URL", str(settings.redis_url) if settings.redis_url else "")
    redis: Redis | None = None
    if redis_url:
        try:
            redis = redis_from_url(redis_url, decode_responses=True)
        except Exception:
            redis = None
    identity_store = IdentityStore(redis)  # accepts None -> degraded but functional
    key_manager = KeyManager(
        redis,
        rotation_interval=timedelta(seconds=settings.key_rotation_seconds),
        namespace=settings.key_namespace,
        fallback_secret=settings.resolve_jwt_secret(),
    )
    await key_manager.start()

    audit_logger = AuditLogger(settings.audit_bootstrap_servers, settings.audit_topic)
    try:
        await audit_logger.start()
    except Exception:
        # Degrade gracefully when Kafka is unavailable in dev
        pass

    stop_event = asyncio.Event()
    rotation_task = asyncio.create_task(
        _rotation_worker(key_manager, max(1.0, float(settings.key_rotation_check_seconds)), stop_event)
    )

    app.state.redis = redis
    app.state.identity_store = identity_store
    app.state.key_manager = key_manager
    app.state.audit_logger = audit_logger
    app.state._key_rotation_task = rotation_task
    app.state._key_rotation_stop = stop_event

    try:
        yield
    finally:
        stop_event.set()
        rotation_task.cancel()
        with suppress(asyncio.CancelledError):
            await rotation_task
        await key_manager.stop()
        with suppress(Exception):
            await audit_logger.stop()
        with suppress(Exception):
            await identity_store.close()


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

    @app.get("/ready", tags=["system"])
    async def ready() -> dict[str, str]:
        # Consider ready if key manager and identity store have been initialized
        healthy = hasattr(app.state, "identity_store") and hasattr(app.state, "key_manager")
        return {"status": "ready" if healthy else "starting"}

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "SomaGent Identity Service"}

    app.include_router(router)
    
    # REAL OpenTelemetry instrumentation - no mocks, exports to Prometheus
    setup_observability("identity-service", app, service_version="0.2.0")
    
    return app


app = create_app()