"""Memory gateway bridging SomaGent and SomaBrain."""

from fastapi import FastAPI

from .api.routes import router
from .core.config import settings

app = FastAPI(
    title="SomaGent Memory Gateway",
    version="0.1.0",
    description=(
        "Wraps SomaBrain memory APIs and exposes local fallbacks for development."
    ),
)

app.include_router(router)


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    """Service readiness check."""

    return {"status": "ok", "service": settings.service_name}
