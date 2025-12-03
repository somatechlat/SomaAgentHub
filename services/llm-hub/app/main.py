from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

app = FastAPI(
    title="SomaAgent LLM Hub",
    version="0.1.0",
    description="Centralized LLM capabilities (Placeholder for real integration).",
)

@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "healthy", "service": "llm-hub"}

@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

