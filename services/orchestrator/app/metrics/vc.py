"""Prometheus metrics for the Solver‑Verifier‑Corrector (VC) reasoning workflow.

The VC loop is a core reinforcement‑learning data source. These metrics provide
visibility into episode throughput, step counts, reward distribution, and overall
episode latency. They are deliberately simple – a counter for episodes, a counter
for steps (tagged by role), a histogram for step rewards, and a histogram for
episode duration.

All metrics are defined with the ``prometheus_client`` library, which is a
runtime dependency of the orchestrator service. The counters are labelled with
``tenant`` and ``role`` where appropriate so that downstream monitoring can slice
by tenant or agent role.
"""

from __future__ import annotations

from prometheus_client import Counter, Histogram

# ---------------------------------------------------------------------------
# Episode counters
# ---------------------------------------------------------------------------

vc_episode_total = Counter(
    "orchestrator_vc_episode_total",
    "Total number of VC reasoning episodes started",
    ["tenant"],
    )

# ---------------------------------------------------------------------------
# Step counters – one per role (solver, verifier, corrector)
# ---------------------------------------------------------------------------

    vc_step_total = Counter(
    "orchestrator_vc_step_total",
    "Total number of VC steps executed",
    ["tenant", "role"],
    )

# ---------------------------------------------------------------------------
# Reward histogram – records the numeric reward for each step
# ---------------------------------------------------------------------------

    vc_step_reward = Histogram(
    "orchestrator_vc_step_reward",
    "Distribution of rewards emitted by VC steps",
    ["tenant", "role"],
    buckets=[0.0, 0.25, 0.5, 0.75, 1.0],
    )

# ---------------------------------------------------------------------------
# Episode duration – measures how long an episode takes from creation to
# completion. The histogram buckets are expressed in seconds.
# ---------------------------------------------------------------------------

    vc_episode_duration_seconds = Histogram(
    "orchestrator_vc_episode_duration_seconds",
    "Duration of VC episodes (seconds)",
    ["tenant"],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],
    )