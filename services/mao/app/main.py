"""Entrypoint for the Multi-Agent Orchestrator (MAO)."""

from fastapi import FastAPI

from .api.routes import router
from .core.config import settings
from .core.db import get_engine, metadata
from .core.worker import executor

_engine = get_engine()

app = FastAPI(
    title="SomaGent Multi-Agent Orchestrator",
    version="0.1.0",
    description=(
        "Task planning and workflow orchestration layer built on Temporal/Argo. Manages "
        "task DAGs, resource allocation, workspace provisioning, and telemetry."
    ),
)

app.include_router(router)

@app.on_event("startup")
async def on_startup() -> None:
    async with _engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    await executor.start()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await executor.stop()
    await _engine.dispose()



@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    """Return MAO health metadata."""

    return {"status": "ok", "service": settings.service_name}
