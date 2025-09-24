# Performance Tests

- `k6_smoke.js` – light traffic hitting gateway status endpoint.
- `k6_full.js` – mixed gateway + SLM load. Run with `k6 run tests/perf/k6_full.js`. Ensure local services are up (`docker-compose.stack.yml`).
