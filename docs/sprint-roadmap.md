# Sprint‑Based Roadmap – SomaAgentHub (Canonical)

> **Version:** 0.1.0 (generated 2025‑11‑03)

---

## 📅  Sprint 1 – Foundations & Memory‑as‑a‑Service (MaaS)
**Duration:** 2 weeks (10 working days) – single‑developer sprint (you) with me acting as product‑owner/architect.

### 🎯 Goal
Deploy a **stable, reproducible Helm‑based stack** where **Qdrant** (vector store) and **Redis** (KV store) run as **independent pods** and are accessed through the existing **Memory‑Gateway façade** on port **9595**. All services expose health checks and Prometheus metrics, and a minimal CI pipeline validates the build.

### ✅ Deliverables (Definition of Done)
| Deliverable | Acceptance Criteria |
|-------------|----------------------|
| **Helm chart** for the whole stack | `helm install soma-agent-hub ./k8s/helm/soma-agent` succeeds on a fresh Kind cluster; all pods reach **Ready** state. |
| **Memory‑Gateway façade** updated to read `QDRANT_URL` & `REDIS_URL` env‑vars | `curl http://localhost:9595/healthz` returns `{kv_store:true, vector_store:true}`; `GET /memories` works after storing a test vector. |
| **Prometheus metrics** for all core services + Qdrant + Redis exported on `/metrics` (port 9595) | `curl http://localhost:9595/metrics` contains `gateway_http_requests_total`, `soma_fractal_memory_*`, `redis_up`, `qdrant_up`. |
| **Health/Readiness probes** for every container | `kubectl get pods` shows no `CrashLoopBackOff`; probes succeed. |
| **Basic CI workflow** (GitHub Actions) that runs lint, tests, Docker build, Helm lint | CI runs on every push to `main` and passes all steps (no failures). |
| **Documentation updates** (README & `docs/roadmap-somagenthub.md`) reflecting the new port mapping and independent memory pods. | Repo README shows how to start the cluster with `make dev-up` (which now calls `helm install`), and the roadmap file lists the new Memory‑as‑a‑Service architecture. |

---

### 🗂️  Backlog – Sprint 1 Stories (with rough story points)
| ID | Title | Description | Points |
|----|-------|-------------|--------|
| **F‑01** | Create Helm chart skeleton | Add `Chart.yaml`, `values.yaml`, and `templates/` folder for all services. Include K8s `Deployment`, `Service`, `ConfigMap` for env‑vars. | 5 |
| **F‑02** | Add Qdrant deployment | Deploy Qdrant as a StatefulSet (or Deployment) exposing `${QDRANT_PORT:-10005}` → container port 6333, with PVC `qdrant-data`. | 4 |
| **F‑03** | Add Redis deployment | Deploy Redis with persistence (AOF enabled) on `${REDIS_PORT:-10003}` → container port 6379, PVC `redis-data`. | 4 |
| **F‑04** | Refactor Memory‑Gateway | Update entry point to read `QDRANT_URL` and `REDIS_URL` from environment; remove hard‑coded localhost ports. | 5 |
| **F‑05** | Expose health & metrics | Ensure Qdrant and Redis expose `/healthz` (via side‑car or built‑in), add Prometheus `ServiceMonitor` definitions. | 3 |
| **F‑06** | Update Docker‑Compose (dev) | Keep `docker-compose.yml` for local dev but point its `memory-gateway` service to the new Qdrant/Redis containers (via network aliases). | 2 |
| **F‑07** | Add Prometheus exporter for Qdrant & Redis | Use existing exporters (`redis_exporter`, `qdrant-exporter`) or expose built‑in metrics; ensure they are scraped. | 3 |
| **F‑08** | Create basic CI pipeline | `.github/workflows/ci.yml` with steps: checkout, setup python, `ruff check`, `pytest`, `docker build`, `helm lint`. | 4 |
| **F‑09** | Write integration test | Small pytest that starts the helm chart (Kind) and performs a `POST /memories` → `GET /memories` round‑trip. | 4 |
| **F‑10** | Documentation sync | Update `README.md` with new start‑up steps, add a “Memory‑as‑a‑Service” section to `docs/roadmap-somagenthub.md`, and reference the new ports. | 2 |
| **Total** | | | **36 points** (fits comfortably within a 2‑dev sprint – you’ll have ~32 pts capacity, the extra 4 pts act as buffer). |

---

### 📅  Sprint Calendar (Day‑by‑Day)
| Day | Focus |
|-----|-------|
| **Day 1** | Set up a fresh **Kind** cluster; scaffold the Helm chart (`helm create soma-agent`). Add basic `Chart.yaml` and `values.yaml`. |
| **Day 2** | Add **gateway‑api**, **orchestrator**, **identity‑service** deployments (use existing Dockerfiles). Verify `helm install` works for these three. |
| **Day 3** | Add **Qdrant** deployment (StatefulSet) + PVC. Test `kubectl port-forward` to ensure the vector API is reachable. |
| **Day 4** | Add **Redis** deployment + PVC. Enable AOF persistence (`appendonly yes`). |
| **Day 5** | Implement **Memory‑Gateway** ConfigMap with `QDRANT_URL` & `REDIS_URL`; modify its entry‑point to read those vars. Deploy and test `curl http://<svc>:9595/healthz`. |
| **Day 6** | Add **Prometheus ServiceMonitors** for Qdrant, Redis, and Memory‑Gateway. Run `helm upgrade` and verify metrics appear via `curl http://localhost:9595/metrics`. |
| **Day 7** | Write **helm lint** script, add to CI config. Create a **GitHub Actions** workflow file (`ci.yml`). |
| **Day 8** | Add **integration test** (pytest + `kind` cluster) that stores a dummy vector and retrieves it. |
| **Day 9** | Update **README** and **roadmap** docs with new start‑up instructions, port mapping, and a diagram of the MaaS architecture. |
| **Day 10** | Polish, run a full end‑to‑end verification, fix any failing CI jobs, and tag the commit as `sprint1-foundation`. |

---

## 📦  Technical Specs (Helm values snippets)
```yaml
# values.yaml (excerpt)
gatewayApi:
  image: somaagent/gateway-api:latest
  port: 10000
orchestrator:
  image: somaagent/orchestrator:latest
  port: 10001
identity:
  image: somaagent/identity-service:latest
  port: 10002
qdrant:
  image: qdrant/qdrant:v1.11.0
  port: 10005   # maps to container 6333
redis:
  image: redis:7-alpine
  port: 10003   # maps to container 6379
memoryGateway:
  image: somaagent/memory-gateway:latest
  port: 9595
```

**Environment variables for Memory‑Gateway (ConfigMap):**
```yaml
QDRANT_URL: "http://qdrant:6333"
REDIS_URL:  "redis://redis:6379/0"
```

**Health probes (template snippet):**
```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: http
  initialDelaySeconds: 5
  periodSeconds: 10
readinessProbe:
  httpGet:
    path: /ready
    port: http
  initialDelaySeconds: 5
  periodSeconds: 10
```

**Prometheus ServiceMonitor (memory‑gateway):**
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: memory-gateway
spec:
  selector:
    matchLabels:
      app: memory-gateway
  endpoints:
    - port: http
      path: /metrics
      interval: 15s
```
---

## ✅  Definition of Done (Sprint 1) – Checklist
- [ ] `helm install soma-agent-hub ./k8s/helm/soma-agent` runs clean on a fresh Kind cluster.  
- [ ] `curl http://localhost:9595/healthz` returns `{kv_store:true, vector_store:true}`.  
- [ ] `curl http://localhost:9595/metrics` contains `gateway_http_requests_total`, `soma_fractal_memory_*`, `redis_up`, `qdrant_up`.  
- [ ] CI pipeline (`GitHub Actions`) passes all steps on `main`.  
- [ ] Documentation (README & roadmap) reflects the new architecture and start‑up command (`make dev-up`).  
- [ ] Git tag `sprint1-foundation` created and pushed.

---

*This file is the canonical sprint‑based roadmap for SomaAgentHub.  Subsequent sprints (Identity & Policy, Agent Framework, Autoscaling, Full CI/CD) will be added in later versions.*
