"""Prometheus metrics for analytics service."""

from __future__ import annotations

from prometheus_client import Counter

KAMACHIQ_RUNS_TOTAL = Counter(
    "kamachiq_runs_total",
    "Total number of KAMACHIQ mode runs recorded",
    ("tenant",),
)
