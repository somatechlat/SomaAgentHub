"""Task capsule repository service."""

from fastapi import FastAPI

from .api.routes import router
from .core.config import settings

app = FastAPI(
    title="SomaGent Task Capsule Repository",
    version="0.1.0",
    description=(
        "Stores and retrieves capsule templates, persona molds, and tool bundles."
    ),
)

app.include_router(router)


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    """Return service status."""

    return {"status": "ok", "service": settings.service_name}
