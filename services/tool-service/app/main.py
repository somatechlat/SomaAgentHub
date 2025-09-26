"""Tool integration orchestration service."""

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .api.routes import router
from .core.config import settings
from .core.otel import configure_otel

app = FastAPI(
    title="SomaGent Tool Service",
    version="0.1.0",
    description=(
        "Hosts adapters for external systems (Plane, GitHub, Notion, etc.) and records audit events."
    ),
)

configure_otel(app, settings.service_name)

app.include_router(router)


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    """Return health metadata."""

    return {"status": "ok", "service": settings.service_name}


@app.get("/metrics", tags=["system"])
def metrics() -> Response:
    """Expose Prometheus metrics."""

    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
