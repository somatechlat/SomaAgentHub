# Benchmark Suite

Last Updated: October 9, 2025

## Goals
- Provide reproducible performance baselines and pass/fail thresholds.
- Catch regressions in latency and error rate early in CI.

## Scenarios
- SLM Inference (sync): varied prompts, token limits, temperatures.
- Embeddings: batch inputs sizes [1, 8, 32].

## Workloads
- Warmup: 30s
- Duration: 2m
- RPS targets: 5/10/20 for smoke; higher in dedicated runs.

## Metrics & SLOs
- P95 latency: < 500ms (smoke gate)
- Error rate: < 1%
- CPU/memory: within requests; no throttling

## Pass/Fail
- Fail if either SLO breached in smoke.

## Usage (scripts)
- Use scripts/run_benchmark_suite.py with profiles.
- Report to stdout + artifacts under artifacts/benchmarks.

## Future
- Add long-run soak test and concurrency sweeps.
