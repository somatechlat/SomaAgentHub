"""Service managing SLM execution requests."""

from __future__ import annotations

import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI

import redis.asyncio as redis

from .api.routes import router
from .core.config import get_settings, settings
from .core.providers import get_provider
from .core.queue import QueueWorker

@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = get_settings()
    redis_client = redis.from_url(cfg.redis_url, decode_responses=True)
    worker = QueueWorker(redis_client, get_provider, cfg)
    task = asyncio.create_task(worker.run_forever())
    try:
        yield
    finally:
        worker.stop()
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        await redis_client.aclose()

app = FastAPI(
    title="SomaGent SLM Service",
    version="0.1.0",
    description=(
        "Async workers responsible for executing SLM requests against SomaBrain or external providers."
    ),
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    """Return service heartbeat."""

    return {"status": "ok", "service": settings.service_name}
