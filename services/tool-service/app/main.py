"""Tool integration orchestration service."""

from fastapi import FastAPI

from .api.routes import router
from .core.config import settings

app = FastAPI(
    title="SomaGent Tool Service",
    version="0.1.0",
    description=(
        "Hosts adapters for external systems (Plane, GitHub, Notion, etc.) and records audit events."
    ),
)

app.include_router(router)


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    """Return health metadata."""

    return {"status": "ok", "service": settings.service_name}
