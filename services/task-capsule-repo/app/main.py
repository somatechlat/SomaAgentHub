"""Main entrypoint for the task-capsule repository."""

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

app = FastAPI(
    title="Task Capsule Repository",
    version="0.1.0",
    description="Manages versioned collections of autonomous AI task definitions.",
)

@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Health endpoint for orchestration monitoring."""
    return {"status": "ok", "service": "task-capsule-repo"}

@app.get("/metrics", tags=["system"])
def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/")
def root():
    return {"message": "Task Capsule Repository"}

# Task capsule endpoints
@app.get("/v1/capsules", tags=["capsules"])
def list_capsules():
    return {"capsules": [{"id": "demo-capsule", "version": "1.0.0", "status": "active"}]}

@app.post("/v1/capsules", tags=["capsules"])
def create_capsule(capsule: dict):
    return {"id": "new-capsule-id", "status": "created", "capsule": capsule}

@app.get("/v1/capsules/{capsule_id}", tags=["capsules"])
def get_capsule(capsule_id: str):
    return {"id": capsule_id, "version": "1.0.0", "definition": {"task": "demo_task"}}
