"""Prometheus metrics specific to the Planner service.

The FastAPI router for the planner imports these counters and increments them
inside each endpoint. Keeping them in a dedicated module makes the metrics
definition easy to discover and reuse across services.
"""

from __future__ import annotations

from prometheus_client import Counter, Histogram

# Total number of plan generation requests (including batch calls – each item
# counts as a separate generation).
planner_generate_requests = Counter(
    "orchestrator_planner_generate_requests_total",
    "Number of planner generate requests received",
    ["method"],  # "single" or "batch"
)

# Total number of plan refinement requests.
planner_refine_requests = Counter(
    "orchestrator_planner_refine_requests_total",
    "Number of planner refine requests received",
)

# Histogram of request latency (seconds) for generate and refine.
planner_latency_seconds = Histogram(
    "orchestrator_planner_latency_seconds",
    "Latency of planner endpoints",
    ["endpoint"],
)

# Counter for list requests
planner_list_requests = Counter(
    "orchestrator_planner_list_requests_total",
    "Number of planner list requests received",
)

# Counter for batch refine requests (counts total items processed)
planner_batch_refine_requests = Counter(
    "orchestrator_planner_batch_refine_requests_total",
    "Number of planner batch refine requests processed",
    ["method"],
)

# Counter for get requests
planner_get_requests = Counter(
    "orchestrator_planner_get_requests_total",
    "Number of planner get requests received",
)

# Counter for delete requests
planner_delete_requests = Counter(
    "orchestrator_planner_delete_requests_total",
    "Number of planner delete requests received",
)
