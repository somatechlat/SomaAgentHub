from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = PROJECT_ROOT / "services" / "analytics-service"
sys.path.insert(0, str(SERVICE_ROOT))

from app.main import app  # type: ignore  # noqa: E402
from app.core.store import store  # type: ignore  # noqa: E402

client = TestClient(app)


def setup_function() -> None:
    store.benchmarks.clear()
    store.runs.clear()
    store.notifications.clear()
    store.billing_events.clear()
    store.kamachiq_runs.clear()
    store.drills.clear()
    store.regressions.clear()


def test_record_benchmark_run_and_scoreboard() -> None:
    started = datetime.now(timezone.utc) - timedelta(seconds=10)
    completed = datetime.now(timezone.utc)
    payload = {
        "suite": "session",
        "scenario": "fast_path",
        "service": "orchestrator",
        "target": "http://localhost:8002",
        "started_at": started.isoformat(),
        "completed_at": completed.isoformat(),
        "metrics": {
            "latency_p95_ms": 950,
            "requests_per_second": 120,
            "error_rate": 0.005,
        },
        "metadata": {"notes": "smoke"},
    }

    response = client.post("/v1/benchmarks/run", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["score"] > 1.0
    assert data["metrics"]["latency_p95_ms"] == pytest.approx(950)

    latest = client.get("/v1/benchmarks/latest")
    assert latest.status_code == 200
    results = latest.json()["results"]
    assert len(results) == 1
    assert results[0]["benchmark_id"] == data["benchmark_id"]

    board = client.get("/v1/benchmarks/scoreboard")
    assert board.status_code == 200
    scoreboard = board.json()["scoreboard"]
    assert scoreboard
    assert scoreboard[0]["best_benchmark_id"] == data["benchmark_id"]


def test_rejects_non_numeric_metrics() -> None:
    payload = {
        "suite": "session",
        "scenario": "bad_metric",
        "service": "orchestrator",
        "target": "http://localhost:8002",
    "started_at": datetime.now(timezone.utc).isoformat(),
    "completed_at": datetime.now(timezone.utc).isoformat(),
        "metrics": {"latency_p95_ms": "unknown"},
    }

    response = client.post("/v1/benchmarks/run", json=payload)
    assert response.status_code == 400
    assert "Metric" in response.json()["detail"]


def test_agent_one_sight_dashboard_combines_sections() -> None:
    started = datetime.now(timezone.utc) - timedelta(seconds=5)
    completed = datetime.now(timezone.utc)
    benchmark_payload = {
        "suite": "session",
        "scenario": "overview",
        "service": "orchestrator",
        "target": "http://localhost:8002",
        "started_at": started.isoformat(),
        "completed_at": completed.isoformat(),
        "metrics": {"latency_p95_ms": 800, "requests_per_second": 90, "error_rate": 0.01},
    }
    assert client.post("/v1/benchmarks/run", json=benchmark_payload).status_code == 201

    run_payload = {
        "capsule_id": "capsule-1",
        "tenant_id": "tenant-1",
        "persona": "alpha",
        "success": True,
        "tokens": 1200,
        "revisions": 1,
        "duration_seconds": 12.3,
    }
    assert client.post("/v1/capsule-runs", json=run_payload).status_code == 202

    billing_payload = {
        "tenant_id": "tenant-1",
        "service": "orchestrator",
        "cost": 42.5,
        "currency": "USD",
        "tokens": 5000,
    }
    assert client.post("/v1/billing/events", json=billing_payload).status_code == 202

    kamachiq_payload = {
        "tenant_id": "tenant-1",
        "name": "weekly",
        "deliverable_count": 3,
    }
    assert client.post("/v1/kamachiq/runs", json=kamachiq_payload).status_code == 201

    drill_payload = {
        "primary_region": "us-east-1",
        "failover_region": "us-west-2",
        "started_at": started.isoformat(),
        "ended_at": completed.isoformat(),
        "rpo_seconds": 30.0,
        "succeeded": True,
    }
    assert client.post("/v1/drills/disaster", json=drill_payload).status_code == 201

    dashboard = client.get("/v1/dashboards/agent-one-sight")
    assert dashboard.status_code == 200
    payload = dashboard.json()
    assert payload["benchmark_scoreboard"]
    assert payload["capsule_dashboard"]["aggregates"]
    assert payload["billing_ledger"]["entries"]
