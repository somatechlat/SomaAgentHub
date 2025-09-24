"""Service responsible for fetching and validating the SomaGent constitution."""

from fastapi import FastAPI

from .api.routes import router
from .core.config import settings

app = FastAPI(
    title="SomaGent Constitution Service",
    version="0.1.0",
    description=(
        "Fetches signed constitution versions from SomaBrain, verifies signatures, and exposes "
        "the current policy hash to downstream services."
    ),
)

app.include_router(router)


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    """Health endpoint to verify constitution service availability."""

    return {"status": "ok", "service": settings.service_name}
