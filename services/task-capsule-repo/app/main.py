"""Task capsule repository service."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .api.routes import router
from .core.config import settings
from .core.db import get_engine, metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure schema creation on startup and close engine on shutdown."""

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    try:
        yield
    finally:
        await engine.dispose()


app = FastAPI(
    title="SomaGent Task Capsule Repository",
    version="0.1.0",
    description=(
        "Stores capsule templates, marketplace submissions, and approval state."
    ),
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    """Return service status."""

    return {"status": "ok", "service": settings.service_name}


@app.get("/metrics", tags=["system"])
def metrics() -> Response:
    """Expose Prometheus metrics."""

    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
