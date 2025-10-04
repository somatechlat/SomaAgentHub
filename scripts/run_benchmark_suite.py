#!/usr/bin/env python3
"""Execute SomaGent benchmark scenarios and push results to the analytics service.

The harness issues concurrent HTTP requests against a target service endpoint,
computes latency/throughput/error metrics, and records the run via the
`/v1/benchmarks/run` analytics API.
"""

from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
import sys
import time
from typing import Dict, List

import httpx

DEFAULT_ANALYTICS_URL = "http://localhost:8008"


@dataclass
class BenchmarkResult:
    started_at: datetime
    completed_at: datetime
    latencies_ms: List[float]
    status_counts: Counter
    errors: int

    @property
    def total_requests(self) -> int:
        return len(self.latencies_ms) + self.errors

    @property
    def duration_seconds(self) -> float:
        return max((self.completed_at - self.started_at).total_seconds(), 1e-6)

    def metrics(self) -> Dict[str, float]:
        if not self.latencies_ms:
            p95 = 0.0
            p50 = 0.0
        else:
            ordered = sorted(self.latencies_ms)
            index_95 = max(math.ceil(0.95 * len(ordered)) - 1, 0)
            index_50 = max(math.ceil(0.50 * len(ordered)) - 1, 0)
            p95 = ordered[index_95]
            p50 = ordered[index_50]
        total = self.total_requests or 1
        errors = self.errors
        successes = max(total - errors, 0)
        success_rate = successes / total
        error_rate = errors / total
        throughput = total / self.duration_seconds
        return {
            "latency_p95_ms": round(p95, 3),
            "latency_p50_ms": round(p50, 3),
            "requests_per_second": round(throughput, 3),
            "error_rate": round(error_rate, 5),
            "success_rate": round(success_rate, 5),
        }

    def metadata(self) -> Dict[str, str]:
        distribution = {str(code): count for code, count in self.status_counts.items()}
        return {"status_distribution": json.dumps(distribution)}


async def _fire_request(
    client: httpx.AsyncClient,
    method: str,
    endpoint: str,
    semaphore: asyncio.Semaphore,
    status_counts: Counter,
    latencies_ms: List[float],
) -> bool:
    async with semaphore:
        start = time.perf_counter()
        try:
            response = await client.request(method, endpoint)
            elapsed_ms = (time.perf_counter() - start) * 1000
            latencies_ms.append(elapsed_ms)
            status_counts[response.status_code] += 1
            return response.status_code < 400
        except Exception:
            status_counts[-1] += 1
            return False


async def execute_benchmark(args: argparse.Namespace) -> BenchmarkResult:
    endpoint = args.endpoint
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint

    status_counts: Counter = Counter()
    latencies_ms: List[float] = []
    semaphore = asyncio.Semaphore(args.concurrency)
    started_at = datetime.now(timezone.utc)

    async with httpx.AsyncClient(base_url=args.target, timeout=args.timeout) as client:
        tasks = [
            _fire_request(client, args.method.upper(), endpoint, semaphore, status_counts, latencies_ms)
            for _ in range(args.requests)
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=False)

    completed_at = datetime.now(timezone.utc)
    errors = sum(1 for ok in responses if not ok)
    return BenchmarkResult(
        started_at=started_at,
        completed_at=completed_at,
        latencies_ms=latencies_ms,
        status_counts=status_counts,
        errors=errors,
    )


def parse_metadata(pairs: List[str]) -> Dict[str, str]:
    metadata: Dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Invalid metadata entry '{pair}', expected key=value")
        key, value = pair.split("=", 1)
        metadata[key] = value
    return metadata


async def main_async(args: argparse.Namespace) -> int:
    result = await execute_benchmark(args)
    metrics = result.metrics()
    metadata = result.metadata()
    metadata.update(parse_metadata(args.metadata))

    summary = {
        "suite": args.suite,
        "scenario": args.scenario,
        "service": args.service,
        "target": args.target,
        "requests": result.total_requests,
        "errors": result.errors,
        "metrics": metrics,
        "metadata": metadata,
        "status_counts": metadata.get("status_distribution"),
        "duration_seconds": round(result.duration_seconds, 3),
    }
    print(json.dumps(summary, indent=2))

    if args.dry_run:
        return 0

    payload = {
        "suite": args.suite,
        "scenario": args.scenario,
        "service": args.service,
        "target": args.target,
        "started_at": result.started_at.isoformat(),
        "completed_at": result.completed_at.isoformat(),
        "metrics": metrics,
        "metadata": metadata,
    }
    if args.tenant_id:
        payload["tenant_id"] = args.tenant_id

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(f"{args.analytics_url.rstrip('/')}/v1/benchmarks/run", json=payload)
        response.raise_for_status()
        print("Analytics response:", response.json())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run SomaGent benchmark harness")
    parser.add_argument("--suite", required=True, help="Logical benchmark suite name (e.g. sessions)")
    parser.add_argument("--scenario", required=True, help="Scenario identifier (e.g. fast_path)")
    parser.add_argument("--service", required=True, help="Service under test (e.g. orchestrator)")
    parser.add_argument("--target", required=True, help="Base URL for the service under test")
    parser.add_argument("--endpoint", default="/health", help="Endpoint path relative to the target base URL")
    parser.add_argument("--method", default="GET", help="HTTP method to execute")
    parser.add_argument("--requests", type=int, default=50, help="Number of HTTP requests to send")
    parser.add_argument("--concurrency", type=int, default=5, help="Concurrent requests to issue")
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout seconds per request")
    parser.add_argument(
        "--analytics-url",
        default=DEFAULT_ANALYTICS_URL,
        help="Analytics service base URL (defaults to http://localhost:8008)",
    )
    parser.add_argument("--tenant-id", default=None, help="Optional tenant identifier to annotate the run")
    parser.add_argument(
        "--metadata",
        action="append",
        default=[],
        help="Additional key=value metadata pairs to associate with the benchmark run",
    )
    parser.add_argument("--dry-run", action="store_true", help="Compute metrics but skip publishing to analytics")
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return asyncio.run(main_async(args))
    except KeyboardInterrupt:
        return 130
    except Exception as exc:  # noqa: BLE001
        print(f"Benchmark harness failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
