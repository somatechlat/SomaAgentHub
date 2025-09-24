# Chaos Testing Plan

- Use `tests/perf/k6_smoke.js` for baseline load.
- Introduce failure scenarios (with tools like `toxiproxy` or `chaos-mesh`):
  - Kill SLM service pods; ensure queue replay works.
  - Drop Kafka topic connectivity; notification orchestrator should retry.
  - Induce SomaBrain latency spikes; validate back-pressure metrics.
- Document outcomes in `docs/runbooks/` and update alert thresholds.
