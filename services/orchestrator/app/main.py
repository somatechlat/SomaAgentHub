"""Main module for the SomaGent Orchestrator."""

from fastapi import FastAPI

from .api.routes import router
from .core.config import settings

app = FastAPI(
    title="SomaGent Orchestrator",
    version="0.1.0",
    description=(
        "Conversation engine enforcing the constitution, coordinating SLM calls, memory access, "
        "and persona execution for single-agent workloads."
    ),
)

app.include_router(router)


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    """Return orchestrator health metadata."""

    return {"status": "ok", "service": settings.service_name}
