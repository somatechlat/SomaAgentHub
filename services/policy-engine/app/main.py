"""Entry point for the policy evaluation service."""

from fastapi import FastAPI

from .api.routes import router
from .core.config import settings

app = FastAPI(
    title="SomaGent Policy Engine",
    version="0.1.0",
    description=(
        "Evaluates actions against the constitution using weighted constraints. Exposes a "
        "simple API consumed by the orchestrator and MAO."
    ),
)

app.include_router(router)


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    """Policy engine readiness signal."""

    return {"status": "ok", "service": settings.service_name}
