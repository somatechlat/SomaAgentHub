"""Prometheus metrics for the tool service."""

from __future__ import annotations

from prometheus_client import Counter, Histogram

TOOL_EXECUTIONS = Counter(
    "tool_adapter_executions_total",
    "Total tool adapter executions by status",
    ("adapter", "tenant", "status"),
)

TOOL_EXECUTION_LATENCY = Histogram(
    "tool_adapter_execution_latency_seconds",
    "Latency of sandboxed tool executions",
    ("adapter", "tenant"),
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
)

TOOL_RATE_LIMIT_HITS = Counter(
    "tool_adapter_rate_limit_hits_total",
    "Number of rate limit rejections per adapter",
    ("adapter", "tenant"),
)


def record_execution(adapter_id: str, tenant_id: str, status: str, duration_seconds: float) -> None:
    """Record execution counters and histograms."""

    TOOL_EXECUTIONS.labels(adapter=adapter_id, tenant=tenant_id, status=status).inc()
    TOOL_EXECUTION_LATENCY.labels(adapter=adapter_id, tenant=tenant_id).observe(max(duration_seconds, 0.0))


def record_rate_limit(adapter_id: str, tenant_id: str) -> None:
    """Increment rate-limit counter."""

    TOOL_RATE_LIMIT_HITS.labels(adapter=adapter_id, tenant=tenant_id).inc()
