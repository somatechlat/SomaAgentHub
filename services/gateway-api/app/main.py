"""Entry point for the SomaAgentHub (SAH) service."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

from services.common.observability import setup_observability

from .api.routes import router as api_router
from .config import get_sah_settings
from .core.middleware import ContextMiddleware
from .core.redis import close_redis_client, get_redis_client
from .wizard_engine import wizard_engine

settings = get_sah_settings()

app = FastAPI(
    title="SomaAgentHub",
    version=settings.service_version,
    description="Public entrypoint for UI, CLI, and integrations.",
)

app.add_middleware(ContextMiddleware)


class WizardStartRequest(BaseModel):
    wizard_id: str
    user_id: str = "demo-user"
    metadata: dict[str, Any] | None = None


class WizardAnswerRequest(BaseModel):
    value: Any


setup_observability(settings.service_name or "sah", app, service_version=settings.service_version)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await close_redis_client()


async def _check_kafka() -> bool:
    if not settings.kafka.bootstrap_servers:
        return False
    for endpoint in settings.kafka.bootstrap_servers:
        host, _, port_raw = endpoint.partition(":")
        port = int(port_raw or 9092)
        try:
            _reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=3)
        except Exception:
            continue
        writer.close()
        await writer.wait_closed()
        return True
    return False


async def _check_auth() -> bool:
    if not settings.auth.url:
        return False
    url = settings.auth.url.rstrip("/") + "/health"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
        return resp.status_code < 500
    except Exception:
        return False


async def _check_redis() -> bool:
    client = get_redis_client()
    return await client.health_check()


@app.get("/healthz", tags=["system"])
async def healthz() -> dict[str, Any]:
    kafka_ok, auth_ok, redis_ok = await asyncio.gather(
        _check_kafka(),
        _check_auth(),
        _check_redis(),
    )
    status = kafka_ok and auth_ok and redis_ok
    return {
        "status": "ok" if status else "degraded",
        "checks": {
            "kafka": kafka_ok,
            "auth": auth_ok,
            "redis": redis_ok,
        },
    }


@app.get("/ready", tags=["system"])
async def ready() -> dict[str, Any]:
    # Placeholder for migration checks (no database yet). Tie into migrations when SB is integrated.
    health = await healthz()
    return {"status": health["status"], "details": health["checks"]}


@app.get("/metrics", tags=["system"])
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "SomaAgentHub Service"}


app.include_router(api_router)


@app.get("/v1/wizards", tags=["wizard"])
def list_wizards() -> dict[str, Any]:
    return {"wizards": wizard_engine.list_wizards()}


@app.post("/v1/wizards/start", tags=["wizard"])
def start_wizard(request: WizardStartRequest) -> dict[str, Any]:  # pragma: no cover - interacts with external services
    try:
        return wizard_engine.start_wizard(
            wizard_id=request.wizard_id,
            user_id=request.user_id,
            metadata=request.metadata,
        )
    except ValueError as exc:  # pragma: no cover - input validation
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # pragma: no cover - unexpected failure
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/v1/wizards/{session_id}/answer", tags=["wizard"])
def submit_wizard_answer(session_id: str, answer: WizardAnswerRequest) -> dict[str, Any]:
    try:
        return wizard_engine.submit_answer(session_id=session_id, answer={"value": answer.value})
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/v1/wizards/{session_id}", tags=["wizard"])
def get_wizard_session(session_id: str) -> dict[str, Any]:
    session = wizard_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return session


@app.post("/v1/wizards/{session_id}/approve", tags=["wizard"])
def approve_wizard_execution(session_id: str) -> dict[str, Any]:
    try:
        return wizard_engine.approve_execution(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
