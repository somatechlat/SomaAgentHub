# Memory Gateway Service

**Durable context store for SomaAgentHub agents**

> Provides vector and key/value memory APIs backed by Qdrant or in-memory fallbacks, exposing health and metrics endpoints for observability.

---

## 📋 Overview

The Memory Gateway centralizes long-term context for agents. It supports semantic recall via Qdrant, simple key/value retrieval for low-latency lookups, and retrieval-augmented generation (RAG) queries. Downstream services (orchestrator, task capsules) interface with the gateway for storing and recalling conversational or project state.

---

## ⚡ Capabilities

- **Remember/Recall API** – Store arbitrary JSON payloads by key and fetch them later.
- **Vector Storage** – When Qdrant is available, vectors are generated via the SomaLanguage Model (SLM) provider and stored for semantic search.
- **RAG Retrieval** – Retrieves top matches for a query and composes a summary response.
- **Metrics** – Counts requests via Prometheus counter `somabrain_requests_total`.

---

## 🏗️ Architecture

```
Agents / Orchestrator → Memory Gateway → Qdrant (vector DB)
                                    ↘ Redis (fallback with in-memory dict)
                                    ↘ SomaLanguage Model (SLM) Provider
```

Key modules:
- `app/main.py` – FastAPI app, routes, and startup hooks.
- `services/common/qdrant_client.py` – Client factory for Qdrant (shared component).
- `requirements.txt` / `pyproject.toml` – Define dependencies for embedding and HTTP clients (migration to pyproject pending).

---

## 🚀 Running Locally

### Minimal Mode (No Qdrant)
```bash
cd services/memory-gateway
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
This mode uses the in-memory store and is suitable for basic development.

### Full Mode (Qdrant + SomaLanguage Model)
1. Start Qdrant (`docker run -p 6333:6333 qdrant/qdrant`).
2. Ensure the SomaLanguage Model provider is reachable (`SOMALLM_PROVIDER_URL`).
3. Run the service:
   ```bash
   export QDRANT_URL="http://localhost:6333"
   export SOMALLM_PROVIDER_URL="http://localhost:8003"
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

---

## 🔌 Configuration

| Variable | Description | Default |
| --- | --- | --- |
| `QDRANT_URL` | Base URL for Qdrant service | Derived from shared config |
| `SOMALLM_PROVIDER_URL` | Embedding provider endpoint (SomaLanguage Model) | `http://somallm-provider:1001` |
| `SLM_SERVICE_URL` | Alternate embedding endpoint (legacy variable name) | `http://localhost:8003` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Optional telemetry endpoint | unset |

> **Note:** Environment variables retain the historical `SOMALLM_*` prefix even though the service is branded as the SomaLanguage Model (SLM) provider.

If Qdrant is unavailable the service logs a warning and falls back to in-memory storage.

---

## 📡 API Surface

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/v1/remember` | Persist a memory entry (vectorized when Qdrant enabled) |
| `GET` | `/v1/recall/{key}` | Retrieve stored memory by key |
| `POST` | `/v1/rag/retrieve` | Perform semantic search over stored memories |
| `GET` | `/metrics` | Prometheus metrics |
| `GET` | `/health` | Liveness probe |

Example remember request:
```json
{
  "key": "project:alpha:note1",
  "value": {
    "summary": "Completed sprint retrofit",
    "owner": "ravi"
  }
}
```

---

## 📈 Observability

- Metrics increment `somabrain_requests_total` per scrape.
- Add traces by configuring OpenTelemetry exporter environment variables.
- Include the service in monitoring by applying ServiceMonitor definitions (see TODO in Helm chart).

---

## 📦 Deployment

- Dockerfile installs dependencies from `requirements.txt` (pyproject migration tracked in backlog).
- Exposed port 1003 in container; uvicorn serves on 8000 (ingress remapped via Service).
- Add deployment manifest under `infra/k8s/` (pending); track progress in roadmap.

---

## 🧪 Testing Checklist

| Test | Command | Notes |
| --- | --- | --- |
| Linting | `ruff check services/memory-gateway` | After pyproject migration |
| Unit Tests | `pytest services/memory-gateway` | TODO |
| Integration | `scripts/tests/memory_gateway_smoke.py` (planned) | Validate Qdrant integration |

---

## 📚 Related Docs

- `docs/development-manual/index.md` (tracks backlog items for optional services).
- `docs/technical-manual/architecture.md` (describes memory flows alongside orchestrator/gateway).
- `docs/technical-manual/runbooks/service-is-down.md` (extend with memory-specific recovery steps when the service is enabled).

---

**Maintainers**: Data Layer Guild (`#soma-data`).
