from __future__ import annotations

import logging
from typing import Callable

from fastapi import FastAPI

from services.common.config.base_settings import BaseServiceSettings, apply_log_level
from services.common.observability import setup_observability
from services.common.config.base_settings import resolve_env


def create_app(
service_name: str,
settings: BaseServiceSettings,
routes_factory: Callable[[FastAPI], None] | None = None,
version: str = "0.1.0",
instrumentation: bool = True,
lifespan: Callable | None = None,
) -> FastAPI:
"""Create a FastAPI app with unified logging and observability.

- Applies log level (fallback to INFO if attribute missing)
- Initializes OpenTelemetry (metrics + tracing) if enabled
- Calls an optional `routes_factory` to attach routes/routers
"""
log_level_name = getattr(settings, "log_level", "INFO")
logging.basicConfig(
level=getattr(logging, str(log_level_name).upper(), logging.INFO),
format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
title=service_name.replace("-", " ").title(),
version=version,
lifespan=lifespan,
)

enable_tracing = getattr(settings, "enable_tracing", True)
enable_metrics = getattr(settings, "enable_metrics", True)
environment = getattr(settings, "environment", "development")

if instrumentation and (enable_tracing or enable_metrics):
setup_observability(
service_name=service_name,
app=app,
service_version=version,
environment=environment,
)

if routes_factory:
routes_factory(app)

return app
