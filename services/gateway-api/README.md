# Gateway API Service

**Public entry point for SomaAgentHub**

> Handles user, CLI, and partner traffic; orchestrates wizard flows; exposes health and observability endpoints.

---

## 📋 Overview

The Gateway API fronts all external access to SomaAgentHub. It exposes REST endpoints for wizard-driven workflows, relays requests to orchestrator, policy, identity, and memory services, and serves as the primary ingress for web and CLI clients.

---

## ⚡ Capabilities

- **Wizard Engine** – Launches and manages multi-step agent workflows via `/v1/wizards/*` endpoints.
- **Session Context Propagation** – Injects request metadata via `ContextMiddleware` and Redis-based session state.
- **Policy & Identity Enforcement** – Validates tokens, checks policy decisions before invoking downstream services.
- **Observability** – Emits Prometheus metrics and integrates with OpenTelemetry through `services/common/observability`.

---

## 🏗️ Architecture

```
Client → Gateway API → Orchestrator → Temporal / Downstream Services
                   ↘ Policy Engine
                   ↘ Identity Service
                   ↘ Memory Gateway
```

Key modules:
- `app/main.py` – FastAPI entry point, health endpoints, router includes.
- `app/api/routes.py` – REST routes for wizard sessions and supporting APIs.
- `app/core/redis.py` – Redis client lifecycle management.
- `app/config.py` – Settings facade over common gateway configuration.

---

## 🚀 Running Locally

### Prerequisites
- Python 3.11+
- Redis (local or container)
- Temporal (if orchestrator integration required)

### Setup
```bash
cd services/gateway-api
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
export SOMAGENT_GATEWAY_REDIS_URL="redis://localhost:6379/0"
export SOMAGENT_GATEWAY_ORCHESTRATOR_URL="http://localhost:10001"
uvicorn app.main:app --reload --host 0.0.0.0 --port 10000
```

### Useful Commands
- `make dev-start-services` (repo root) prints gateway + orchestrator startup commands.
- `ruff check .` ensures lint compliance.
- `pytest` (pending test suite) for unit coverage.

---

## 🔌 Configuration

Environment variables (see `app/core/config.py`):

| Variable | Description | Default |
| --- | --- | --- |
| `SOMAGENT_GATEWAY_REDIS_URL` | Redis connection string for session state | `redis://redis:6379/0` |
| `SOMAGENT_GATEWAY_ORCHESTRATOR_URL` | Base URL for orchestrator service | `http://orchestrator:10001` |
| `AUTH_URL` / `IDENTITY_SERVICE_URL` | Identity service base URL | `http://identity-service:10002` |
| `KAFKA_BOOTSTRAP_SERVERS` | Optional connection for stream integrations | unset |

---

## 📡 API Surface

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/healthz` | Aggregate health check (Redis, Kafka, identity) |
| `GET` | `/ready` | Readiness probe, mirrors health at present |
| `GET` | `/metrics` | Prometheus metrics |
| `GET` | `/v1/wizards` | List available wizard definitions |
| `POST` | `/v1/wizards/start` | Start a wizard session |
| `GET` | `/v1/wizards/{session_id}` | Retrieve session status |
| `POST` | `/v1/wizards/{session_id}/answer` | Submit user input |
| `POST` | `/v1/wizards/{session_id}/approve` | Approve execution when required |

Authentication flows rely on Identity Service tokens passed in headers; see platform README for details.

---

## 📈 Observability

- Metrics endpoint: `/metrics` (Prometheus format).
- Tracing: OpenTelemetry exporter configured via `OTEL_EXPORTER_OTLP_ENDPOINT`.
- Logs: Structured JSON recommended (configure via `LOG_LEVEL`, `LOG_FORMAT`).
- ServiceMonitor: defined in `k8s/monitoring/servicemonitors.yaml`.

---

## 🛡️ Security & Policy

- Policy enforcement is handled downstream by the orchestrator; direct policy hooks in the gateway are future work.
- Identity tokens validated before orchestrator calls.
- Rate limiting handled upstream (API Gateway / Ingress); future work tracked in roadmap.

---

## 📦 Deployment

- Dockerfile uses multi-stage build? (current file installs from `pyproject.toml`).
- Kubernetes manifest: `infra/k8s/gateway-api.yaml` (LoadBalancer, probes, resources).
- Helm chart values: `k8s/helm/soma-agent/values.yaml` (`gateway` section toggles image/tag/env vars).

---

## 🧪 Testing Checklist

| Test | Command | Notes |
| --- | --- | --- |
| Linting | `ruff check services/gateway-api` | Enforced in CI |
| Unit tests | `pytest services/gateway-api` | TODO: add coverage |
| Integration | `make test-int` | Hits gateway endpoints against local orchestrator |
| E2E | `make test-e2e` | Validates gateway → orchestrator pipeline |

---

## 📚 Related Docs

- Root `README.md` for platform overview.
- `docs/development-manual/local-setup.md` for local environment bootstrapping.
- `docs/technical-manual/deployment.md` for deployment instructions.

---

**Maintainers**: Platform Engineering Team (`#soma-platform`).
