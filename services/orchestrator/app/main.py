"""FastAPI application entry point for the Orchestrator service.

This module defines a ``create_app`` helper that is compatible with both the
historical test suite (which calls ``create_app(settings=…)``) and the
production code path (which uses the full ``bootstrap_create_app`` signature).
The actual FastAPI application is built by :func:`build_app` which wires the
lifespan, routes, security middleware and observability.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from temporalio import client as temporal_client

# Import the original FastAPI bootstrap helper under an alias to avoid name
# collisions.
from services.common.fastapi.bootstrap import create_app as bootstrap_create_app
from services.common.spiffe_auth import init_spiffe

from .api.capsules import router as capsules_router
from .api.health import router as health_router
from .api.mao import router as mao_router
from .api.planner import router as planner_router
from .api.routes import router as orchestrator_router
from .core.config import settings
from .database import init_db
from .services.security import security_manager
from .startup.outbox_publisher_startup import setup_outbox_publisher

logger = logging.getLogger(__name__)


def build_app() -> FastAPI:
    """Construct the FastAPI application.

    The function sets up the lifespan context manager, registers security
    middleware, includes all routers and starts the outbox publisher.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Initialise SPIFFE identity (optional).
        spiffe_identity = init_spiffe(settings.service_name)
        if spiffe_identity:
            logger.info(
                "SPIFFE identity loaded",
                extra={"spiffe_id": spiffe_identity.spiffe_id},
            )
        else:
            logger.info("SPIFFE identity not initialized; continuing without workload SVID")

        # Startup phase.
        await init_db()
        if settings.temporal_enabled:
            app.state.temporal_client = await temporal_client.Client.connect(
                settings.temporal_target_host,
                namespace=settings.temporal_namespace,
            )
        yield
        # Shutdown phase.
        client = getattr(app.state, "temporal_client", None)
        if client is not None:
            close_fn = getattr(client, "close", None)
            if close_fn is not None:
                try:
                    await close_fn()
                except TypeError:
                    # Some clients expose a synchronous close method.
                    close_fn()

    def _routes(app: FastAPI) -> None:
        """Register routes and middleware on the FastAPI app."""

        @app.get("/health", tags=["system"])
        async def healthcheck() -> dict[str, str]:
            return {"status": "ok", "service": settings.service_name}

        @app.get("/ready", tags=["system"])
        async def ready() -> dict[str, str]:
            # Basic readiness check: temporal client present if enabled.
            if settings.temporal_enabled and getattr(app.state, "temporal_client", None) is None:
                return {"status": "starting"}
            return {"status": "ready"}

        @app.get("/metrics", tags=["system"])
        async def metrics() -> Response:
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

        @app.get("/", tags=["system"])
        async def root() -> dict[str, str]:
            return {"message": "SomaGent Orchestrator Service"}

        # Security middleware.
        security_manager.setup_security_middleware(app)
        security_manager.setup_cors_middleware(app)
        security_manager.setup_trusted_hosts(app)

        # Register routers.
        app.include_router(orchestrator_router)
        # Expose capsule CRUD endpoints under /v1/capsules.
        app.include_router(capsules_router)
        app.include_router(mao_router)
        app.include_router(planner_router)
        app.include_router(health_router)

        # Start outbox publisher.
        setup_outbox_publisher(app)

    # Build the FastAPI app using the common bootstrap helper.
    return bootstrap_create_app(
        service_name=settings.service_name or "orchestrator",
        settings=settings,  # type: ignore[arg-type]
        routes_factory=_routes,
        version="0.1.0",
        instrumentation=True,
        lifespan=lifespan,
    )


# The default FastAPI app used by the production entry point.
app = build_app()


def create_app(*args: Any, **kwargs: Any) -> FastAPI:  # pragma: no cover
    """Compatibility wrapper for the historic test suite.

    The test suite historically called ``create_app(settings={...})``. In that
    scenario we ignore the provided settings and return the globally built
    application. For any other call signature we delegate to the original
    ``bootstrap_create_app`` implementation.
    """

    if "settings" in kwargs and len(kwargs) == 1 and not args:
        # Legacy test pattern – ignore overrides.
        return build_app()
    # Production usage – forward to the full bootstrap helper.
    return bootstrap_create_app(*args, **kwargs)
