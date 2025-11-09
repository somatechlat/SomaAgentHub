"""Simple in‑memory capsule repository service.

This service provides a minimal HTTP API for storing and retrieving capsule
manifest YAML files.  It is deliberately lightweight – the production version
will likely back the storage with a persistent object store (MinIO, S3, etc.) –
but for the current roadmap the in‑memory implementation is sufficient to
exercise the end‑to‑end capsule execution flow.

Endpoints (all under ``/v1``):
* ``POST /capsules/{capsule_id}/{version}`` – upload a manifest (plain text
  YAML body).
* ``GET  /capsules/{capsule_id}/{version}`` – retrieve the stored manifest.
* ``GET  /capsules`` – list all stored capsule identifiers.

The service is included in the Helm chart via ``templates/capsule-repo.yaml``
and registered in the top‑level FastAPI application ``services/capsule-repo/app/__init__.py``
so that it can be started independently or as part of the Soma‑Infra chart.
"""

from __future__ import annotations

from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.responses import PlainTextResponse

# ---------------------------------------------------------------------------
# In‑memory store – ``{capsule_id}:{version} -> manifest_yaml``
# ---------------------------------------------------------------------------
_store: dict[str, str] = {}

router = APIRouter(prefix="/v1", tags=["capsule-repo"])


def _key(capsule_id: str, version: str) -> str:
    return f"{capsule_id}:{version}"


@router.post(
    "/capsules/{capsule_id}/{version}",
    status_code=status.HTTP_201_CREATED,
    response_class=PlainTextResponse,
)
async def upload_capsule(capsule_id: str, version: str, request: Request) -> str:
    """Store a capsule manifest.

    The request body must be raw YAML (``text/plain``).  The endpoint returns a
    simple confirmation string; the OpenAPI spec treats it as ``text/plain``.
    """
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Empty manifest body")
    try:
        # Validate that the body is UTF‑8 decodable – the manifest itself will
        # be parsed later by the executor, so we only check basic text.
        body_str = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Manifest must be UTF‑8 text") from exc
    _store[_key(capsule_id, version)] = body_str
    return f"Capsule {capsule_id}:{version} stored"


@router.get("/capsules/{capsule_id}/{version}", response_class=PlainTextResponse)
async def get_capsule(capsule_id: str, version: str) -> str:
    """Retrieve a previously uploaded capsule manifest."""
    try:
        return _store[_key(capsule_id, version)]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Capsule not found") from exc


@router.get("/capsules", response_model=list[str])
async def list_capsules() -> list[str]:
    """Return a list of ``"{capsule_id}:{version}"`` identifiers present in the store."""
    return list(_store.keys())


def create_app() -> FastAPI:
    app = FastAPI(title="SomaAgentHub Capsule Repository", version="0.1.0")
    app.include_router(router)
    return app


app = create_app()
