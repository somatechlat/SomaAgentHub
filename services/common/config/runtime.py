"""Runtime configuration helpers.

This module provides helpers for selecting configuration values based on the
runtime environment (e.g. Docker vs Kubernetes vs Local).
"""

from __future__ import annotations

import os
from typing import TypeVar

T = TypeVar("T")


def runtime_default(primary: T, secondary: T) -> T:
    """
    Selects a default value based on runtime availability.

    If the primary value is truthy (or explicitly set if it was an env var resolution),
    it is returned. Otherwise, the secondary (fallback) value is returned.

    This is often used to provide a local/docker default as primary, and a K8s/prod
    default as secondary, or vice versa depending on strategy.

    In current usage: runtime_default(resolve_env(...), "k8s-url") implies:
    try env var first (or its local default), else use hardcoded k8s default.
    Since resolve_env handles the defaulting for the env var, this function
    might just be a simple pass-through or a check for None?

    However, mostly used like:
    runtime_default(resolve_env("VAR", "local-default"), "prod-default")

    If we are in "production" mode, maybe we prefer secondary?
    For now, we implement a simple coalescing logic.
    """
    if primary is not None:
        return primary
    return secondary


def default_otlp_grpc_endpoint() -> str:
    """Returns the default OTLP GRPC endpoint based on environment."""
    # Use standard OTLP port 4317
    host = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT_HOST", "tempo")
    port = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT_PORT", "4317")
    return f"http://{host}:{port}"
