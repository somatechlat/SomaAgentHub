"""Prometheus metrics helpers for the gateway service."""

from __future__ import annotations

from prometheus_client import Counter, Histogram

MODERATION_DECISIONS = Counter(
    "gateway_moderation_decisions_total",
    "Number of moderation decisions taken before orchestration",
    ("tenant", "outcome"),
)

MODERATION_STRIKES = Counter(
    "gateway_moderation_strikes_total",
    "Total strike increments applied during moderation",
    ("tenant",),
)

ORCHESTRATOR_LATENCY = Histogram(
    "gateway_orchestrator_forward_latency_seconds",
    "Latency for forwarding moderated payloads to the orchestrator",
    ("tenant",),
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
)


def record_moderation_decision(tenant: str, outcome: str, flagged: bool, strikes: int) -> None:
    """Increment counters for moderation outcomes."""

    MODERATION_DECISIONS.labels(tenant=tenant, outcome=outcome).inc()
    if flagged and strikes:
        MODERATION_STRIKES.labels(tenant=tenant).inc(strikes)


def observe_forward_latency(tenant: str, elapsed_seconds: float) -> None:
    """Track latency when forwarding to the orchestrator."""

    ORCHESTRATOR_LATENCY.labels(tenant=tenant).observe(max(elapsed_seconds, 0.0))
