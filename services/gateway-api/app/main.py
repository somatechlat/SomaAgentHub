"""Entry point for the SomaGent Gateway API service."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .api.routes import router
from .api.dashboard import router as dashboard_router
from .core.config import settings
from .core.middleware import ContextMiddleware
from .core.redis import close_redis_client, get_redis_client
from .core.otel import configure_otel


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure shared clients are ready and cleaned up."""

    _ = get_redis_client()
    try:
        yield
    finally:
        await close_redis_client()


app = FastAPI(
    title="SomaGent Gateway API",
    version="0.1.0",
    description=(
        "Public entrypoint for UI, CLI, and integrations. Handles request validation, "
        "rate limiting hooks, and forwards traffic to internal orchestrators."
    ),
    lifespan=lifespan,
)

configure_otel(app, settings.service_name)

app.add_middleware(ContextMiddleware)

app.include_router(router)
app.include_router(dashboard_router)

# TLS placeholders: run with `uvicorn` using cert/key if configured.
# Example: uvicorn app.main:app --port 8080 --ssl-keyfile /path/key.pem --ssl-certfile /path/cert.pem



@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    """Lightweight health endpoint used by orchestration and platform monitors."""
    return {"status": "ok", "service": settings.service_name}


@app.get("/metrics", tags=["system"])
def metrics() -> Response:
    """Expose Prometheus metrics."""

    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
