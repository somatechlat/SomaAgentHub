# SomaGent Benchmark Service

Runs benchmark capsules against configured SLM providers, stores results in Postgres, and exposes aggregate scores. Used by model scoring and Agent One Sight dashboard.

## Endpoints
- `POST /v1/run` – Execute benchmarks defined in config.
- `GET /v1/scores` – List aggregated scores per provider/model/role.
- `GET /health` – Service status.

Configure providers and database via `SOMAGENT_BENCH_*` env vars.
