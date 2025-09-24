# SomaGent Developer Setup

This guide captures default URLs/ports, quick-start commands, and tips for running the full SomaGent stack locally.

## 1. Prerequisites
- Docker / Docker Compose
- Python 3.11+
- Node.js 18+ (for admin console prototypes)
- Make (optional but convenient)

## 2. Core Services & Default Ports
| Service | Default URL | Notes |
|---------|-------------|-------|
| SomaBrain | http://localhost:9696 | Memory/RAG backend. Exposes `/docs` and `/metrics`. |
| SLM HTTP fallback | http://localhost:9697 | Sync inference & embeddings (`/infer_sync`, `/embedding`, `/health`). |
| Gateway API | http://localhost:8080 | Entry point for clients (after implementation). |
| Orchestrator | http://localhost:8100 | Conversation loop + policy enforcement. |
| Multi-Agent Orchestrator | http://localhost:8200 | Temporal/Argo workflows. |
| Constitution Service | http://localhost:8300 | Fetch/validate signed constitutions. |
| Policy Engine | http://localhost:8400 | Scores actions against constraints. |
| Settings Service | http://localhost:8500 | Tenant configs, model profiles, notification prefs. |
| Identity Service | http://localhost:8600 | Auth/capability claims, training locks. |
| SLM Service | http://localhost:8700 | Async workers + HTTP fallback integration. |
| Memory Gateway | http://localhost:8800 | Wraps SomaBrain memory APIs. |
| Tool Service | http://localhost:8900 | Tool adapters (Plane, GitHub, etc.). |
| Task Capsule Repo | http://localhost:8910 | Stores capsule templates. |
| Notification Orchestrator | http://localhost:8920 | WebSocket hub consuming Kafka notifications. |
| Admin Console (dev) | http://localhost:3000 | React/Vite dev server. |
| Benchmark Service | http://localhost:8925 | Triggers SLM benchmarks, stores results. |

Adjust ports via environment variables if needed; ensure no conflicts on your machine.

## 3. Running SomaBrain & SLM Skeleton
```
# SomaBrain (Docker)
docker run --rm -p 9696:8000 ghcr.io/somatechlat/somabrain:latest

# SLM fallback (local script or container)
# Assuming a FastAPI skeleton listening on 9697
```

Verify:
- http://localhost:9696/docs
- http://localhost:9696/metrics
- http://localhost:9697/openapi.json

### Compose bundle

To launch Kafka, Postgres, Redis, SomaBrain, Prometheus, and Grafana together:

```
docker compose -f docker-compose.stack.yml up -d
```

Endpoints:
- Kafka: `PLAINTEXT://localhost:9092`
- Postgres: `postgresql://somagent:somagent@localhost:5432/somagent`
- Redis: `redis://localhost:6379/0`
- SomaBrain: `http://localhost:9696`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (admin/admin)

Stop the stack with `docker compose -f docker-compose.stack.yml down -v`.

Run benchmark service (requires Postgres running):

```bash
cd services/benchmark-service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8925
```

## 4. SomaGent Services (local)
```
# Example: run constitution service (requires virtualenv)
cd services/constitution-service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8300
```
Repeat for other services, matching the ports above. A full docker-compose stack will be added later.

## 5. Environment Variables (common)
- `SOMAGENT_DEPLOYMENT_MODE`: developer-light | developer-full | test | test-debug | production | production-debug
- `SOMAGENT_GATEWAY_ORCHESTRATOR_URL`, etc., to point services to one another.
- `X-Tenant-ID` header expected by SomaBrain (configurable via `TENANT_HEADER`).
- SLM provider keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.).

## 6. Sample Workflow
1. Start SomaBrain and SLM fallback.
2. Launch gateway, orchestrator, constitution service, policy engine.
3. Hit `POST http://localhost:8100/v1/sessions/start` with a test payload.
4. Confirm metrics via Prometheus if available.

## 7. Observability
- Prometheus: http://localhost:9090 (if using provided docker-compose).
- Grafana: http://localhost:3000 (default login admin/admin). Import dashboards for SomaBrain metrics and Agent One Sight.
- Logs: use `uvicorn --reload --log-level info` to see structured logs during dev.

## 8. Developer Tips
- Use `scripts/dev/bootstrap_local_env.sh <service-path>` to create venvs quickly.
- Add `/etc/hosts` entries if you prefer service aliases (e.g., `somabrain.local`).
- When tests land, run `pytest` in each service. Linting (ruff/mypy) to be added per service.

## 9. Troubleshooting
- Port conflict? Adjust `--port` arguments or env vars; stop conflicting processes.
- SomaBrain 422 errors: check payload schema (`text`, `query`) and tenant header.
- SLM fallback 422: ensure payload includes required fields (prompt/model when defined).
- Constitution fetch fails: verify SomaBrain is up and `SOMAGENT_CONSTITUTION_*` env vars point to the correct URL.

Keep this document updated as ports or configurations change.

## Kubernetes / Helm
- Helm scaffold available at `infra/k8s/charts/somagent`.
- Example: `helm install somagent infra/k8s/charts/somagent --set image.repository=<repo> --set image.tag=<tag>`.
- Extend with secrets, ingress, autoscaling before production use.

## Load & Chaos Testing
- Run `k6 run tests/perf/k6_smoke.js` for smoke tests; `k6 run tests/perf/k6_full.js` for heavier mixed traffic.
- Explore chaos scenarios documented in `tests/chaos/README.md`; use `tests/chaos/inject_faults.sh` to pause services locally.

## Secrets
- Use `somagent-secrets` helper to load values via env (`SOMAGENT_*_KEY`) or files (`SOMAGENT_*_KEY_FILE`).
- For local testing, create `.env` or simple text files and export appropriate env vars.
