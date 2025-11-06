"""Simple Policy Engine Service

This service provides a minimal wrapper around Open Policy Agent (OPA) style
policy evaluation. It is deliberately lightweight – the goal is to have a
running HTTP endpoint that other services can call to ask whether a given
action is allowed. In a production deployment the service would be backed by a
real OPA server or a policy DSL interpreter. For now we implement a very small
in‑memory rule set that can be extended via environment variables.

Endpoints
~~~~~~~~~
* ``GET /health`` – health check used by Docker/Kubernetes probes.
* ``GET /metrics`` – Prometheus metrics (a simple request counter).
* ``POST /v1/allow`` – Accepts a JSON payload with ``subject``, ``action`` and
  ``resource`` fields and returns ``{"allowed": true}`` or ``{"allowed": false}``.

Configuration
~~~~~~~~~~~~~
* ``POLICY_ENGINE_PORT`` – Port the FastAPI app listens on (default ``10020``).
* ``ALLOWED_ACTIONS`` – Comma‑separated list of ``action:resource`` strings that
  are permitted. Example: ``read:memory,write:memory``.

The service is included in ``docker-compose.yml`` and exposed on the canonical
port range via the ``MEMORY_GATEWAY_PORT`` variable.
"""

from __future__ import annotations

import os
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

app = FastAPI(title="SOMA Policy Engine")

# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------
def _parse_allowed_actions(env_value: str | None) -> List[tuple[str, str]]:
    """Parse ``ALLOWED_ACTIONS`` into a list of ``(action, resource)`` tuples.

    The environment variable format is ``action:resource,action:resource``. Empty
    values result in an empty list which means *deny all*.
    """
    if not env_value:
        return []
    pairs: List[tuple[str, str]] = []
    for item in env_value.split(","):
        if ":" not in item:
            continue
        action, resource = item.split(":", 1)
        pairs.append((action.strip(), resource.strip()))
    return pairs

ALLOWED_ACTIONS = _parse_allowed_actions(os.getenv("ALLOWED_ACTIONS"))

# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------
class AllowRequest(BaseModel):
    subject: str = Field(..., description="Identity of the caller")
    action: str = Field(..., description="Action being requested, e.g. 'read'")
    resource: str = Field(..., description="Target resource, e.g. 'memory'")

class AllowResponse(BaseModel):
    allowed: bool

# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
REQUESTS = Counter("policy_engine_requests_total", "Total requests to policy engine")

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health", tags=["system"])  # pragma: no cover - trivial
async def health() -> Response:
    """Simple health check used by Docker/Kubernetes probes."""
    return Response(content="OK", media_type="text/plain")


@app.get("/metrics", response_class=Response)
async def metrics() -> Response:
    """Expose Prometheus metrics. The counter increments on each request to
    ``/v1/allow``.
    """
    REQUESTS.inc()
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.post("/v1/allow", response_model=AllowResponse)
async def allow(request: AllowRequest) -> AllowResponse:
        """Very simple policy evaluation.

        The logic is:
        * If ``ALLOWED_ACTIONS`` is empty → deny everything.
        * Otherwise, allow only when the ``action:resource`` pair appears in the
            configured list.
        """
        # In a real implementation we would also evaluate ``subject`` based rules.
        pair = (request.action, request.resource)
        is_allowed = pair in ALLOWED_ACTIONS
        return AllowResponse(allowed=is_allowed)


# ---------------------------------------------------------------------------
# Compatibility endpoint – the orchestrator expects ``/v1/evaluate``.
# ---------------------------------------------------------------------------
@app.post("/v1/evaluate", response_model=AllowResponse)
async def evaluate(request: AllowRequest) -> AllowResponse:
        """Alias for the ``/v1/allow`` endpoint used by legacy orchestrator code.

        The orchestrator configuration builds the URL as
        ``${POLICY_ENGINE_URL}/v1/evaluate``. To avoid breaking existing flows we
        expose the same logic under this path.
        """
        return await allow(request)
"""Entry point for policy engine service.

This module simply re-exports the application defined in :mod:`policy_app`
so ``uvicorn app.main:app`` uses the fully featured service implementation.
"""

from .policy_app import app  # noqa: F401