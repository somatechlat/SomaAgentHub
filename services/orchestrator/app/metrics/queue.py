"""Prometheus metrics for orchestrator queue depth.

The orchestrator runs Temporal workflows on a configurable task queue
(``settings.temporal_task_queue``).  This module provides a gauge metric that
exposes the current number of pending workflow executions for that queue.  The
metric name follows the existing naming convention used across the repo:

    orchestrator_queue_length{task_queue="<queue>"}

The gauge is updated by a background coroutine started from the Temporal worker
process (see ``services/orchestrator/temporal_worker.py``).
"""

from __future__ import annotations

from prometheus_client import Gauge

# Gauge with a ``task_queue`` label so multiple queues can be tracked if needed.
ORCHESTRATOR_QUEUE_GAUGE = Gauge(
    "orchestrator_queue_length",
    "Current number of pending Temporal workflow executions for the orchestrator's queue",
    ["task_queue"],
)


def set_queue_length(queue_name: str, length: int) -> None:
    """Set the gauge to ``length`` for the given ``queue_name``.

    The function is deliberately tiny – it is safe to call from any async
    context.  ``length`` should be a non‑negative integer; negative values are
    coerced to ``0`` to avoid Prometheus validation errors.
    """
    if length < 0:
        length = 0
    ORCHESTRATOR_QUEUE_GAUGE.labels(task_queue=queue_name).set(length)
