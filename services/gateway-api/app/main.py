"""Entry point for the SomaAgentHub Gateway API service (no mocks)."""

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .api.routes import router as api_router
from .observability import setup_observability
from .wizard_engine import wizard_engine
from .core.middleware import ContextMiddleware

app = FastAPI(
    title="SomaAgentHub Gateway API",
    version="0.1.0",
    description="Public entrypoint for UI, CLI, and integrations.",
)

# Add request context middleware so routes that depend on RequestContext
# receive a populated context built from JWT claims / headers.
app.add_middleware(ContextMiddleware)


# Request/Response models for Wizard endpoints
class WizardStartRequest(BaseModel):
    wizard_id: str
    user_id: str = "demo-user"
    metadata: Optional[Dict[str, Any]] = None


class WizardAnswerRequest(BaseModel):
    value: Any


# REAL OpenTelemetry instrumentation - no mocks, exports to Prometheus
setup_observability("gateway-api", app, service_version="0.1.0")


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    """Lightweight health endpoint used by orchestration and platform monitors."""
    return {"status": "ok", "service": "gateway-api"}

@app.get("/ready", tags=["system"])
def ready() -> dict[str, str]:
    """Readiness probe (static for gateway; upstream checks happen at request time)."""
    return {"status": "ready"}


@app.get("/metrics", tags=["system"])
def metrics() -> Response:
    """Expose Prometheus metrics."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
def root() -> Dict[str, str]:
    return {"message": "SomaAgentHub Gateway API Service"}


# Include REAL gateway API routes that forward to the Orchestrator
app.include_router(api_router)


# Wizard endpoints (real engine, no mock execution)
@app.get("/v1/wizards", tags=["wizard"])
def list_wizards() -> Dict[str, Any]:
    """List all available project wizards."""
    return {"wizards": wizard_engine.list_wizards()}


@app.post("/v1/wizards/start", tags=["wizard"])
def start_wizard(request: WizardStartRequest) -> Dict[str, Any]:
    """Start a new wizard session."""
    try:
        result = wizard_engine.start_wizard(
            wizard_id=request.wizard_id,
            user_id=request.user_id,
            metadata=request.metadata,
        )
        return result
    except ValueError as e:  # pragma: no cover - input validation
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:  # pragma: no cover - unexpected failure
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/wizards/{session_id}/answer", tags=["wizard"])
def submit_wizard_answer(session_id: str, answer: WizardAnswerRequest) -> Dict[str, Any]:
    """Submit an answer to the current wizard question."""
    try:
        result = wizard_engine.submit_answer(session_id=session_id, answer={"value": answer.value})
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/wizards/{session_id}", tags=["wizard"])
def get_wizard_session(session_id: str) -> Dict[str, Any]:
    """Get wizard session details."""
    session = wizard_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return session


@app.post("/v1/wizards/{session_id}/approve", tags=["wizard"])
def approve_wizard_execution(session_id: str) -> Dict[str, Any]:
    """Approve and execute the wizard plan via the real Orchestrator."""
    try:
        result = wizard_engine.approve_execution(session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
