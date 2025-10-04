"""Entry point for the notification orchestrator service."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .api.routes import router
from .core.bus import get_notification_bus
from .core.config import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    bus = get_notification_bus(settings)
    await bus.startup()
    try:
        yield
    finally:
        await bus.shutdown()


app = FastAPI(
    title="SomaGent Notification Service",
    version="0.1.0",
    description="Orchestrates delivery of cross-channel notifications for SomaGent operators.",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health", tags=["system"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/metrics", tags=["system"])
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
