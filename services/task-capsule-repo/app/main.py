"""Main entrypoint for the task-capsule repository."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import PlainTextResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from services.common.config.base_settings import resolve_env

app = FastAPI(
    title="Task Capsule Repository",
    version="0.1.0",
    description="Manages versioned collections of autonomous AI task definitions.",
)

# ----------------------------------------------------------------------------
# In-memory capsule manifest store (capsule_id:version -> YAML text)
# ----------------------------------------------------------------------------
_store: dict[str, str] = {}

def _key(capsule_id: str, version: str) -> str:
    return f"{capsule_id}:{version}"


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
@app.get("/v1/capsules", tags=["capsules"], response_model=list[str])
def list_capsules() -> list[str]:
    return list(_store.keys())


@app.post(
    "/v1/capsules/{capsule_id}/{version}",
    tags=["capsules"],
    status_code=status.HTTP_201_CREATED,
    response_class=PlainTextResponse,
)
async def upload_capsule(capsule_id: str, version: str, request: Request) -> str:
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Empty manifest body")
    try:
        body_str = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Manifest must be UTF-8 text") from exc
    _store[_key(capsule_id, version)] = body_str
    return f"Capsule {capsule_id}:{version} stored"


@app.get(
    "/v1/capsules/{capsule_id}/{version}",
    tags=["capsules"],
    response_class=PlainTextResponse,
)
def get_capsule_version(capsule_id: str, version: str) -> str:
    try:
        return _store[_key(capsule_id, version)]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Capsule not found") from exc
