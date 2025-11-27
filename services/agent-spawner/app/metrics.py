"""Prometheus metrics for the Agent‑Spawner service.

All metrics follow the VIBE rule **Observability** – they are exported via the
standard ``/metrics`` endpoint provided by the shared FastAPI bootstrap
helper (see ``services.common.fastapi.bootstrap``). The counters and gauges are
registered at import time so they are ready to be used from any request handler
or background task.
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge

# ---------------------------------------------------------------------------
# Counters
# ---------------------------------------------------------------------------
agents_spawned_total = Counter(
    "agents_spawned_total",
    "Total number of agent spawn requests processed",
    ["agent_type"],
)

agents_terminated_total = Counter(
    "agents_terminated_total",
    "Total number of agent termination requests processed",
    ["agent_type"],
)

agents_status_updates_total = Counter(
    "agents_status_updates_total",
    "Total number of status transitions recorded for agents",
    ["from_status", "to_status"],
)

# ---------------------------------------------------------------------------
# Gauges – represent the current number of agents in each status.
# ---------------------------------------------------------------------------
agents_by_status = Gauge(
    "agents_by_status",
    "Current number of agents per status",
    ["status"],
)

# Helper to update the gauge safely.
def set_agent_status_gauge(status: str, value: int) -> None:
    """Set the ``agents_by_status`` gauge for *status* to *value*.

    The gauge is labelled by the status string (e.g., ``RUNNING``). This helper
    abstracts the direct ``Gauge`` call and makes it easy to mock in tests.
    """
    agents_by_status.labels(status=status).set(value)
