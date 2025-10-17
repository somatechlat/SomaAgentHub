# Policy Engine Service

**Status:** Optional guardrail service (not enabled in the default docker-compose stack).

Evaluates prompts against tenant rule packs defined in `app/data/rules.json`, exports Prometheus metrics, and can cache rules in Redis when `REDIS_URL` is provided.

---

## 📋 Overview

The Policy Engine provides synchronous policy checks used by the orchestrator before executing high-impact actions. At runtime it loads rule packs from the local repository (`app/data/rules.json`) and, when available, persists merged packs to Redis under the `policy:rules` namespace. Kafka cache invalidation and constitution service integration are planned but not yet implemented in code.

---

## ⚡ Capabilities

- **Prompt Evaluation** – Scores requests with weighted rules and returns allow/deny decisions via `/v1/evaluate`.
- **Tenant Rule Packs** – Supports separate rule definitions per tenant with deterministic caching.
- **Optional Redis Backing** – Uses Redis only when `REDIS_URL` is configured; otherwise falls back to in-process cache.
- **Prometheus Metrics** – Exposes counters and histograms for evaluation volume, latency, and scores at `/metrics`.

---

## 🏗️ Architecture

```
Gateway / Orchestrator → Policy Engine → (optional) Redis cache
```

Key modules:
- `app/policy_app.py` – FastAPI application with lifespan tasks for warming caches.
- `app/core/engine.py` – Policy evaluation and severity calculation.
- `app/policy_rules.py` – Rule pack loading, tenant utilities, and evaluation helpers.
- `app/redis_client.py` – Lazy Redis client wiring via shared `services.common` helper.
- `app/observability.py` – Prometheus and OpenTelemetry configuration.

---

## 🚀 Running Locally

### Prerequisites
- Python 3.11+
- Optional: Redis instance for shared rule caching (falls back to in-process cache when absent)

### Setup
```bash
cd services/policy-engine
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
# Optional but recommended when testing cache behaviour
export REDIS_URL="redis://localhost:6379/0"
uvicorn app.main:app --reload --host 0.0.0.0 --port 10020
```

The service is not yet wired into `docker-compose.yml`; run it manually or deploy it to Kubernetes when policy checks are required.

---

## 🔌 Configuration

| Variable | Description | Default |
| --- | --- | --- |
| `REDIS_URL` | Redis connection string (optional) | unset |
| `KAFKA_BOOTSTRAP_SERVERS` | Placeholder for future invalidation events | unset |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry exporter endpoint | unset |
| `OTEL_SERVICE_NAME` | Service name override for OTEL | `policy-engine` |

---

## 📡 API Surface

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/v1/evaluate` | Evaluate prompt/action request and return allowed flag plus severity |
| `GET` | `/health` | Liveness probe |
| `GET` | `/metrics` | Prometheus metrics |

Example evaluation request:
```json
{
  "session_id": "abc123",
  "tenant": "global",
  "user": "demo",
  "prompt": "Generate code for external API",
  "role": "developer",
  "metadata": {}
}
```

---

## 📈 Observability

- Metrics:
  - `policy_evaluations_total` (counter, labeled by tenant/decision/severity)
  - `policy_evaluation_latency_seconds` (histogram)
  - `policy_evaluation_score` (histogram)
- Tracing hooks are prepared via `setup_observability` and emit only when `OTEL_EXPORTER_OTLP_ENDPOINT` is set.
- A ServiceMonitor is **not** currently provided; add one when deploying to Kubernetes to scrape metrics.

---

## 🛡️ Security & Compliance

- Applies deterministic substring checks according to rule pack weights.
- Emits structured logs for allow/deny decisions; forward them to Loki/ELK using the shared logging configuration.
- When Redis is enabled, tenant keys are stored under `policy:rules:<tenant>` to keep isolation boundaries clear.

---

## 📦 Deployment

- Dockerfile (`services/policy-engine/Dockerfile`) exposes port `10020` and runs `uvicorn` directly.
- Kubernetes manifest: `infra/k8s/policy-engine.yaml` is the authoritative deployment spec; the Helm chart currently does **not** template this service.
- The service is omitted from `docker-compose.yml`; add a compose service entry if you need it locally.

---

## 🧪 Testing Checklist

| Test | Command | Notes |
| --- | --- | --- |
| Linting | `ruff check services/policy-engine` | Uses shared repo configuration |
| Unit tests | `pytest services/policy-engine/tests` | Covers rule engine and cache helpers |
| Integration | _(not yet implemented)_ | Wire through gateway/orchestrator once the service is enabled |

---

## 📚 Related Docs

- `docs/technical-manual/architecture.md` – overall service topology and call flow.
- `docs/development-manual/volcano-integration-roadmap.md` – tracking for scheduler adoption and policy rollout sequencing.
- `docs/technical-manual/runbooks/service-is-down.md` – generic recovery checklist to adapt for the policy engine when deployed.

---

**Maintainers**: Governance Engineering Team (`#soma-governance`).
