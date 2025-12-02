"""Main entrypoint for the PostgreSQL-backed task-capsule repository."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import router
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context."""
    await init_db()
    yield


    app = FastAPI(
    title="Task Capsule Repository",
    version="0.2.0",
    description="PostgreSQL-backed repository for versioned autonomous AI task definitions",
    lifespan=lifespan,
    )

# Include the new PostgreSQL-backed API
    app.include_router(router)


    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
    """Health endpoint for orchestration monitoring."""
    return {"status": "ok", "service": "task-capsule-repo", "backend": "postgresql"}


    @app.get("/metrics", tags=["system"])
    def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


    @app.get("/")
    async def root():
    return {
    "message": "Task Capsule Repository",
    "backend": "PostgreSQL",
    "version": "0.2.0",
    "endpoints": [
    "/v1/capsules",
    "/v1/capsules/{capsule_id}/{version}",
    "/health",
    "/metrics"
    ]
    }