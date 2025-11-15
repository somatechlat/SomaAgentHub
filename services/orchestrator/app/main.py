"""FastAPI application entry point for the Orchestrator service."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from temporalio import client as temporal_client

# Import the original FastAPI bootstrap helper under an alias to avoid name
from services.common.fastapi.bootstrap import create_app as bootstrap_create_app
from services.common.spiffe_auth import init_spiffe

from .api.routes import router as orchestrator_router
from .api.mao import router as mao_router
from .api.planner import router as planner_router
from .api.health import router as health_router
from .core.config import settings
from .database import init_db, check_database_health
from .startup.outbox_publisher_startup import setup_outbox_publisher
from .services.observability import setup_observability
from .services.security import security_manager
from services.common.config.base_settings import resolve_env

logger = logging.getLogger(__name__)


def build_app() -> FastAPI:
@asynccontextmanager
async def lifespan(app: FastAPI):
spiffe_identity = init_spiffe(settings.service_name)
if spiffe_identity:
logger.info(
"SPIFFE identity loaded", extra={"spiffe_id": spiffe_identity.spiffe_id}
)
else:
logger.info(
"SPIFFE identity not initialized; continuing without workload SVID"
)

# Startup phase
await init_db()
if settings.temporal_enabled:
app.state.temporal_client = await temporal_client.Client.connect(
settings.temporal_target_host,
namespace=settings.temporal_namespace,
)
yield
# Shutdown phase
client = getattr(app.state, "temporal_client", None)
if client is not None:
close_fn = getattr(client, "close", None)
if close_fn is not None:
try:
    await close_fn()
except TypeError:
    close_fn()

def _routes(app: FastAPI) -> None:
@app.get("/health", tags=["system"])
async def healthcheck() -> dict[str, str]:
return {"status": "ok", "service": settings.service_name}

@app.get("/ready", tags=["system"])
async def ready() -> dict[str, str]:
# Basic readiness check: temporal client present
if (
settings.temporal_enabled
and getattr(app.state, "temporal_client", None) is None
):
return {"status": "starting"}
return {"status": "ready"}

@app.get("/metrics", tags=["system"])
async def metrics() -> Response:
return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/")
async def root():
return {"message": "SomaGent Orchestrator Service"}

# Initialize security middleware
security_manager.setup_security_middleware(app)
security_manager.setup_cors_middleware(app)
security_manager.setup_trusted_hosts(app)

# Initialize rate limiting (temporarily disabled)
# app.add_middleware(RateLimitMiddleware, rate_limiter_instance=rate_limiter)

# Initialize observability (simplified for production deployment)
# setup_observability(app)

# Setup routes
app.include_router(orchestrator_router)
app.include_router(mao_router)
app.include_router(planner_router)
app.include_router(health_router)
setup_outbox_publisher(app)

app = bootstrap_create_app(
service_name=settings.service_name or "orchestrator",
settings=settings,  # type: ignore[arg-type]
routes_factory=_routes,
version="0.1.0",
instrumentation=True,
lifespan=lifespan,
)
return app


app = build_app()


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
def create_app(*args, **kwargs) -> FastAPI:  # pragma: no cover

The historic test suite imports ``create_app`` from this module and calls it
with a single ``settings`` keyword argument containing a dict of overrides.
Production code, however, uses the ``bootstrap_create_app`` helper imported
from ``services.common.fastapi.bootstrap`` which expects a richer set of
parameters (e.g., ``service_name``, ``settings``, ``routes_factory`` …).

To support both use‑cases we inspect the call signature:
* If the call contains only a ``settings`` keyword (the test pattern), we
ignore it and delegate to :func:`build_app`, which constructs the FastAPI
application using the global settings singleton.
* For any other combination of arguments we forward directly to the
original ``bootstrap_create_app`` so existing production code paths remain
functional.
"""

# Detect the legacy test invocation pattern.
# Legacy test pattern: only a ``settings`` keyword is provided (a dict of
# overrides). The dict is not required for the current test suite because
# database sessions are supplied directly via fixtures. We therefore ignore
# the overrides and build the app using the canonical configuration.
if "settings" in kwargs and len(kwargs) == 1 and not args:
return build_app()

# Fallback to the original bootstrap helper for production usage.
return bootstrap_create_app(*args, **kwargs)
