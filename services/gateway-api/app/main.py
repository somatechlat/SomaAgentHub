"""Entry point for the SomaGent Gateway API service."""

from fastapi import FastAPI

from .api.routes import router
from .api.dashboard import router as dashboard_router
from .core.config import settings
from .core.middleware import ContextMiddleware

app = FastAPI(
    title="SomaGent Gateway API",
    version="0.1.0",
    description=(
        "Public entrypoint for UI, CLI, and integrations. Handles request validation, "
        "rate limiting hooks, and forwards traffic to internal orchestrators."
    ),
)

app.add_middleware(ContextMiddleware)

app.include_router(router)
app.include_router(dashboard_router)

# TLS placeholders: run with `uvicorn` using cert/key if configured.
# Example: uvicorn app.main:app --port 8080 --ssl-keyfile /path/key.pem --ssl-certfile /path/cert.pem



@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    """Lightweight health endpoint used by orchestration and platform monitors."""
    return {"status": "ok", "service": settings.service_name}
