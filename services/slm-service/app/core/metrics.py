"""Prometheus metrics for SLM service."""

from __future__ import annotations

from prometheus_client import Counter, Histogram

from .config import get_settings

settings = get_settings()
_namespace = settings.metrics_namespace

INFER_REQUESTS = Counter(
    "infer_sync_requests_total",
    "Number of synchronous inference requests",
    labelnames=("provider", "model"),
    namespace=_namespace,
)

INFER_LATENCY = Histogram(
    "infer_sync_latency_seconds",
    "Latency of synchronous inference",
    labelnames=("provider", "model"),
    namespace=_namespace,
)

EMBED_REQUESTS = Counter(
    "embedding_requests_total",
    "Number of embedding requests",
    labelnames=("provider", "model"),
    namespace=_namespace,
)

EMBED_LATENCY = Histogram(
    "embedding_latency_seconds",
    "Latency of embedding generation",
    labelnames=("provider", "model"),
    namespace=_namespace,
)
