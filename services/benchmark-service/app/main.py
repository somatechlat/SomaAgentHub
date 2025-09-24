"""Benchmark service entrypoint."""

from __future__ import annotations

import asyncio

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from .api.routes import router
from .core.config import settings
from .core.db import get_engine, metadata


async def startup(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)


app = FastAPI(
    title="SomaGent Benchmark Service",
    version="0.1.0",
    description="Runs benchmark capsules against SLM providers and computes scores.",
)

_engine = get_engine()


@app.on_event("startup")
async def on_startup() -> None:
    await startup(_engine)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await _engine.dispose()


app.include_router(router)


@app.get("/health", tags=["system"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}
