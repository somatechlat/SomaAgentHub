"""Entry point for the SomaGent Gateway API service."""

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

app = FastAPI(
    title="SomaGent Gateway API",
    version="0.1.0",
    description="Public entrypoint for UI, CLI, and integrations.",
)

@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    """Lightweight health endpoint used by orchestration and platform monitors."""
    return {"status": "ok", "service": "gateway-api"}

@app.get("/metrics", tags=["system"])
def metrics() -> Response:
    """Expose Prometheus metrics."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/")
def root():
    return {"message": "SomaGent Gateway API Service"}

# Gateway API endpoints
@app.post("/v1/chat/completions", tags=["gateway"])
def chat_completions(request: dict):
    return {"id": "chatcmpl-demo", "object": "chat.completion", "choices": [{"message": {"role": "assistant", "content": "Hello from SomaGent Gateway!"}}]}

@app.get("/v1/models", tags=["gateway"])
def list_models():
    return {"object": "list", "data": [{"id": "somaagent-demo", "object": "model", "created": 1696118400}]}

@app.post("/v1/sessions", tags=["gateway"])
def create_session(session: dict):
    return {"session_id": "demo_session", "status": "created", "session": session}
