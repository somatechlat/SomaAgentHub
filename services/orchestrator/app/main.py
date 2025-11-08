"""FastAPI application entry point for the Orchestrator service."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from temporalio import client as temporal_client

from services.common.observability import setup_observability
from services.common.spiffe_auth import init_spiffe

from .api.routes import router as orchestrator_router
from .core.config import settings
from .database import init_db

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="SomaGent Orchestrator", version="0.1.0")

    # Sprint-6: Initialize OpenTelemetry instrumentation
    setup_observability("orchestrator", app, service_version="0.1.0")

    spiffe_identity = init_spiffe(settings.service_name)
    if spiffe_identity:
        logger.info(
            "SPIFFE identity loaded", extra={"spiffe_id": spiffe_identity.spiffe_id}
        )
    else:
        logger.info("SPIFFE identity not initialized; continuing without workload SVID")

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        # Startup phase
        await init_db()
        if settings.temporal_enabled:
            app.state.temporal_client = await temporal_client.Client.connect(
                settings.temporal_target_host,
                namespace=settings.temporal_namespace,
            )
        yield
        # Shutdown phase
        client = getattr(app.state, "temporal_client", None)
        if client is not None:
            close_fn = getattr(client, "close", None)
            if close_fn is not None:
                try:
                    await close_fn()
                except TypeError:
                    close_fn()

    @app.get("/health", tags=["system"])
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok", "service": settings.service_name}

    @app.get("/ready", tags=["system"])
    async def ready() -> dict[str, str]:
        # Basic readiness check: temporal client present
        if (
            settings.temporal_enabled
            and getattr(app.state, "temporal_client", None) is None
        ):
            return {"status": "starting"}
        return {"status": "ready"}

    @app.get("/metrics", tags=["system"])
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/")
    async def root():
        return {"message": "SomaGent Orchestrator Service"}

    app.include_router(orchestrator_router)
    app.router.lifespan_context = lifespan

    return app


app = create_app()
