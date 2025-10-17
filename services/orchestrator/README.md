# Orchestrator Service

**Central coordinator for multi-agent workflows**

> Connects Gateway requests to Temporal workflows, enforces policy decisions, and manages session lifecycle across agents.

---

## 📋 Overview

The Orchestrator is responsible for translating high-level user intents into Temporal workflows, coordinating task capsules, and synchronizing state across supporting services (memory, policy, identity). It exposes a FastAPI interface for gateway traffic, internal admin endpoints, and metrics for observability.

---

## ⚡ Capabilities

- **Workflow Orchestration** – Launches and tracks Temporal workflows via `temporal_client.Client`.
- **Session State Management** – Maintains in-memory/session caches and communicates with memory gateway when configured.
- **Policy & Identity Integration** – Calls policy engine for guardrails and identity service for token validation.
- **Observability** – Ships OpenTelemetry traces and Prometheus metrics; readiness gate ensures Temporal connectivity.

---

## 🏗️ Architecture

```
Gateway → Orchestrator FastAPI → Temporal Workflows → Agents & Capsules
                     ↘ Policy Engine
                     ↘ Identity Service
                     ↘ Memory Gateway
```

Key components:
- `app/main.py` – FastAPI application factory, lifecycle hooks for Temporal client.
- `app/api/routes.py` – REST endpoints for orchestrating sessions and workflows.
- `app/core/config.py` – Pydantic settings with Temporal, policy, identity toggles.
- `app/workflows/` – Temporal workflow and activity implementations.
- `app/workflows/volcano_launcher.py` – Feature-flagged helper to submit jobs to Volcano via kubectl.

---

## 🚀 Running Locally

### Prerequisites
- Python 3.11+
- Temporal server (use `make dev-up` to start docker-compose stack)

### Setup
```bash
cd services/orchestrator
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
export TEMPORAL_HOST="localhost:7233"
export TEMPORAL_NAMESPACE="default"
uvicorn app.main:app --reload --host 0.0.0.0 --port 10001
```

Launch workers (if defined):
```bash
python -m app.worker --task-queue somagent.session.workflows
```

---

## 🔌 Configuration

| Variable | Description | Default |
| --- | --- | --- |
| `TEMPORAL_HOST` | Temporal frontend host:port | `localhost:7233` (append `:7233` for remote clusters) |
| `TEMPORAL_NAMESPACE` | Temporal namespace | `default` |
| `TEMPORAL_TASK_QUEUE` | Queue for workflows | `somagent.session.workflows` |
| `POLICY_ENGINE_URL` | Policy engine base URL | `http://policy-engine:10020` (the service appends `/v1/evaluate`) |
| `IDENTITY_SERVICE_URL` | Identity service base URL | `http://identity-service:10002` (the service appends `/v1/tokens/issue`) |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Optional OTEL exporter | unset |
| `ENABLE_VOLCANO_SCHEDULER` | Enable Volcano-backed job submission for sessions | `false` |
| `VOLCANO_NAMESPACE` | Namespace where PodGroups/Jobs are created | `soma-agent-hub` |
| `VOLCANO_DEFAULT_QUEUE` | Volcano queue used for session workloads | `interactive` |
| `VOLCANO_SESSION_IMAGE` | Container image scheduled for session jobs | `python:3.11-slim` |
| `VOLCANO_SESSION_CPU` | CPU request/limit for session jobs | `500m` |
| `VOLCANO_SESSION_MEMORY` | Memory request/limit for session jobs | `512Mi` |
| `VOLCANO_JOB_TIMEOUT_SECONDS` | Wait timeout when tracking a session job | `300` |
| `KUBECTL_BINARY` | Path to kubectl binary inside the worker | `kubectl` |

> When Volcano integration is enabled, session metadata keys such as `volcano_queue`, `volcano_command`, `volcano_image`, and `volcano_wait` can override the defaults per request.

---

## 📡 API Surface

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Liveness probe |
| `GET` | `/ready` | Readiness probe (ensures Temporal client available) |
| `GET` | `/metrics` | Prometheus metrics |
| `POST` | `/v1/sessions` | Start new orchestration sessions (example) |
| `GET` | `/v1/sessions/{session_id}` | Retrieve workflow status |
| `POST` | `/v1/sessions/{session_id}/actions/{action}` | Trigger workflow actions |

Refer to `app/api/routes.py` for the latest endpoint list.

---

## 📈 Observability

- Metrics exported via `/metrics`.
- Tracing configured through `setup_observability` in `app/main.py`.
- ServiceMonitor present in Helm chart for automated scraping.

---

## 🛡️ Security

- Accepts requests only from Gateway in production; enforce via network policies and service mesh.
- Validates policy decisions before executing state-changing actions.
- JWTs verified by calling Identity service.

---

## 📦 Deployment

- Docker build context: `services/orchestrator`.
- Kubernetes manifest: `infra/k8s/orchestrator.yaml` (includes probes, volumes, affinity rules).
- Helm chart integrates orchestrator deployment with shared labels and metrics.

---

## 🧪 Testing Checklist

| Test | Command | Notes |
| --- | --- | --- |
| Linting | `ruff check services/orchestrator` | CI enforced |
| Unit Tests | `pytest services/orchestrator` | Add more coverage as workflows grow |
| Integration | `make test-e2e` | Exercises gateway→orchestrator pipeline |
| Chaos | `scripts/tests/temporal_failover.sh` | Validates Temporal retry strategy |

---

## 📚 Related Docs

- `docs/technical-manual/deployment.md` for deployment and upgrade steps.
- `docs/development-manual/local-setup.md` for local environment expectations.
- `docs/technical-manual/runbooks/service-is-down.md` for the baseline recovery checklist.

---

**Maintainers**: Workflow Engineering Guild (`#soma-workflows`).
