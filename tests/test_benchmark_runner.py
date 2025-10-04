from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone

import pytest

from scripts.run_benchmark_suite import BenchmarkResult, parse_metadata


def test_benchmark_result_metrics_compute_expected_values() -> None:
    started = datetime.now(timezone.utc)
    completed = started + timedelta(seconds=2)
    result = BenchmarkResult(
        started_at=started,
        completed_at=completed,
        latencies_ms=[100.0, 200.0, 300.0, 400.0, 500.0],
        status_counts=Counter({200: 5}),
        errors=0,
    )

    metrics = result.metrics()
    assert metrics["latency_p95_ms"] == pytest.approx(500.0)
    assert metrics["latency_p50_ms"] == pytest.approx(300.0)
    assert metrics["requests_per_second"] == pytest.approx(2.5)
    assert metrics["error_rate"] == 0.0
    assert metrics["success_rate"] == 1.0


def test_parse_metadata_handles_pairs() -> None:
    metadata = parse_metadata(["region=us-east-1", "run=smoke"])
    assert metadata == {"region": "us-east-1", "run": "smoke"}

    with pytest.raises(ValueError):
        parse_metadata(["invalid-entry"])
