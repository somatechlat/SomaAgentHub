"""Runtime-aware helpers for environment-specific service defaults."""

from __future__ import annotations

import os
from functools import lru_cache

_RUNTIME_ENV_VARS = (
    "SOMASTACK_RUNTIME_TARGET",
    "SOMAGENT_RUNTIME_TARGET",
    "RUNTIME_TARGET",
)


@lru_cache(maxsize=1)
def runtime_flavor() -> str:
    """Return the active runtime flavour (``docker`` by default)."""

    for name in _RUNTIME_ENV_VARS:
        value = os.getenv(name)
        if value:
            return value.strip().lower()
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        return "kubernetes"
    return "docker"


def is_kubernetes() -> bool:
    """True when running inside a Kubernetes pod."""

    return runtime_flavor() in {"kubernetes", "k8s"}


def is_docker() -> bool:
    """True when running via docker-compose or similar local runtime."""

    return not is_kubernetes()


def runtime_default(docker_value: str, kubernetes_value: str | None = None) -> str:
    """Pick the appropriate default value for the current runtime."""

    if is_kubernetes():
        return kubernetes_value or docker_value
    return docker_value


def default_otlp_grpc_endpoint() -> str:
    """Return the OTLP gRPC endpoint for the active runtime."""

    return runtime_default(
        docker_value="http://otel-collector:4317",
        kubernetes_value="http://tempo.observability:4317",
    )
