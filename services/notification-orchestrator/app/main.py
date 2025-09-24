"""Notification orchestrator entrypoint."""

from __future__ import annotations

import contextlib

from fastapi import FastAPI

from .api.routes import router
from .core.config import settings
from .core.consumer import notification_consumer

app = FastAPI(
    title="SomaGent Notification Orchestrator",
    version="0.1.0",
    description="Broadcasts notifications from Kafka to websocket clients.",
)


@app.on_event("startup")
async def on_startup() -> None:
    with contextlib.suppress(Exception):  # noqa: S110
        await notification_consumer.start()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    with contextlib.suppress(Exception):
        await notification_consumer.stop()


app.include_router(router)


@app.get("/health", tags=["system"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}
