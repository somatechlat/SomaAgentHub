"""Settings, marketplace, and configuration surface for SomaGent."""

from fastapi import FastAPI

from .api.routes import router
from .core.config import settings

app = FastAPI(
    title="SomaGent Settings & Marketplace",
    version="0.1.0",
    description=(
        "Manages tenant configuration, marketplace listings, token budgets, and tool metadata."
    ),
)

app.include_router(router)


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    """Indicate service readiness."""

    return {"status": "ok", "service": settings.service_name}
