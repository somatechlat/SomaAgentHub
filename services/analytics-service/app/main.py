"""Entry point for analytics service."""

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .api.routes import router
from .core.config import settings
from .observability import setup_observability

app = FastAPI(
    title="SomaGent Analytics Service",
    version="0.1.0",
    description="Aggregates capsule telemetry, persona regression outcomes, and governance reports.",
)

app.include_router(router)

# REAL OpenTelemetry instrumentation - no mocks, exports to Prometheus
setup_observability("analytics-service", app, service_version="0.1.0")


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/metrics", tags=["system"])
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
