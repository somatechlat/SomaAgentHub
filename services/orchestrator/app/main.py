"""FastAPI application entry point for the Orchestrator service."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from temporalio import client as temporal_client

from .api.routes import router as orchestrator_router
from .core.config import settings
from .observability import setup_observability


def create_app() -> FastAPI:
    app = FastAPI(title="SomaGent Orchestrator", version="0.1.0")

    # Sprint-6: Initialize OpenTelemetry instrumentation
    setup_observability("orchestrator", app, service_version="0.1.0")

    @app.on_event("startup")
    async def _startup_temporal_client() -> None:
        app.state.temporal_client = await temporal_client.Client.connect(
            settings.temporal_target_host,
            namespace=settings.temporal_namespace,
        )

    @app.on_event("shutdown")
    async def _shutdown_temporal_client() -> None:
        client = getattr(app.state, "temporal_client", None)
        if client is not None:
            await client.close()

    @app.get("/health", tags=["system"])
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok", "service": settings.service_name}

    @app.get("/metrics", tags=["system"])
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/")
    async def root():
        return {"message": "SomaGent Orchestrator Service"}

    app.include_router(orchestrator_router)

    return app


app = create_app()
