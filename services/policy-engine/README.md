# Policy Engine Service

**Constitution-aware guardrails for SomaAgentHub**

> Evaluates prompts and actions against tenant-specific policies, caches constitution hashes, and exports decision telemetry.

---

## 📋 Overview

The Policy Engine enforces governance across all agent interactions. It evaluates requests using constitution rule packs, emits metrics for decision tracking, and keeps rule caches synchronized via Kafka notifications and Redis storage.

---

## ⚡ Capabilities

- **Policy Evaluation** – Evaluates prompts using weighted rules and severity scoring (`/v1/evaluate`).
- **Multi-Tenant Support** – Loads tenant-specific rule packs and caches constitution hashes in Redis.
- **Event-Driven Cache Invalidation** – Listens to `constitution.updated` Kafka topic to refresh caches automatically.
- **Observability** – Publishes Prometheus counters/histograms for decision outcomes and latency.

---

## 🏗️ Architecture

```
Gateway / Orchestrator → Policy Engine → Constitution Cache (Redis)
                                         ↘ Constitution Service
                                         ↘ Kafka (cache invalidation)
```

Key modules:
- `app/policy_app.py` – FastAPI application, lifespan management, background tasks.
- `app/core/engine.py` – Policy evaluation logic and severity computation.
- `app/constitution_cache.py` – Redis-based caching helpers.
- `app/policy_rules.py` – Rule definitions and tenant management.
- `app/observability.py` – OpenTelemetry setup.

---

## 🚀 Running Locally

### Prerequisites
- Python 3.11+
- Redis instance (local container or cloud)
- Optional: Kafka for cache invalidation tests

### Setup
```bash
cd services/policy-engine
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
export REDIS_HOST=localhost
export REDIS_PORT=6379
uvicorn app.main:app --reload --host 0.0.0.0 --port 1002
```

To simulate Kafka updates in development, run the `scripts/mock_constitution_events.py` helper (planned).

---

## 🔌 Configuration

| Variable | Description | Default |
| --- | --- | --- |
| `REDIS_HOST` | Redis hostname | `redis.somaagent` |
| `REDIS_PORT` | Redis port | `6379` |
| `REDIS_DB` | Redis database index | `0` |
| `CONSTITUTION_SERVICE_URL` | Source of canonical constitution documents | `http://constitution-service:1008` |
| `KAFKA_BOOTSTRAP_SERVERS` | Optional Kafka brokers for cache invalidation | unset |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Observability exporter endpoint | `http://prometheus-prometheus.observability:9090` |

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
- Tracing uses OpenTelemetry instrumentation configured during app startup.
- ServiceMonitor defined in Helm chart ensures scraping.

---

## 🛡️ Security & Compliance

- Enforces constitution-based rules to prevent unsafe agent actions.
- Logs evaluation results for auditing (ship to Loki/ELK via standard logging pipeline).
- Supports tenant isolation by tagging Redis keys with tenant identifiers.

---

## 📦 Deployment

- Dockerfile inherits base python image; ensures deterministic builds.
- Kubernetes manifest: `infra/k8s/policy-engine.yaml` (includes resources, probes, security context).
- Helm chart config: `k8s/helm/soma-agent` (`policyEngine` values block).

---

## 🧪 Testing Checklist

| Test | Command | Notes |
| --- | --- | --- |
| Linting | `ruff check services/policy-engine` | CI enforced |
| Unit tests | `pytest services/policy-engine` | Add tests for rule evaluation and cache layers |
| Integration | `make test-e2e` | Validates gateway→policy→orchestrator flow |
| Load | `scripts/tests/policy_load_test.py` (planned) | Ensures histogram coverage |

---

## 📚 Related Docs

- `docs/CRITICAL_FIXES_REPORT.md` for policy-related remediations.
- `docs/runbook.md` for secret rotation and incident procedures.
- Roadmap item: Tenant override tooling (Sprint 3).

---

**Maintainers**: Governance Engineering Team (`#soma-governance`).
