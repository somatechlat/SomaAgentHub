# SomaAgentHub – Roadmap & Feature Catalog

**Version:** 0.1.0 (initial canonical document)

---

## 📋 Overview

SomaAgentHub is designed as a **central orchestration hub** (the “control‑tower”) for a heterogeneous fleet of autonomous agents, human operators, and external services.  It provides a single entry point, policy enforcement, persistent memory, and full observability.  The hub can handle normal airport‑day traffic, holiday surges, maintenance windows, and emergency situations while guaranteeing “no‑crash” safety.

---

## 🗂️ Feature Catalog

| Feature | Status | Description |
|---------|--------|-------------|
| **Gateway API** | ✅ Implemented | FastAPI façade (`/v1/wizards/*`, health, metrics). Handles authentication, routing, and wizard session management. |
| **Orchestrator** | ✅ Implemented | Temporal‑based workflow engine. Translates high‑level intents into durable workflows, supports retries, compensation, and activity tracing. |
| **Memory Service (MaaS)** | ✅ Implemented (Qdrant + Redis) | **Memory‑as‑a‑Service** architecture: Qdrant runs on host port **${QDRANT_PORT:-10005}** (container 6333) and Redis runs on host port **${REDIS_PORT:-10003}** (container 6379). Both are independent pods, exposed via the unified Memory‑Gateway façade on **port 9595**. Provides vector storage, KV session state, OpenAPI (`/memories`, `/search`, `/stats`), and Prometheus metrics (`soma_fractal_memory_*`). |
| **Identity Service** | ❌ Missing (stub) | Issues JWTs, validates tokens for every inbound request. |
| **Policy Engine** | ❌ Missing (stub) | OPA‑style guardrails (e.g., weight limits, runway occupancy, emergency overrides). |
| **Human‑in‑the‑Loop (HITL)** | ✅ Partial | UI task‑card system that can pause workflows and wait for human approval. Metrics `human_approval_*` are emitted. |
| **Agent Contract** | ✅ Defined | Standard `POST /run` / `GET /run/{id}` JSON API. All agents (robots, AI services, external partners, humans) implement this contract. |
| **Agent Registry** | ✅ Partial | ConfigMap‑based lookup of `agent_type → service DNS`. Allows dynamic addition of new agents without hub code changes. |
| **Observability Stack** | ✅ Implemented | Prometheus metrics (`gateway_http_requests_total`, `temporal_*`, `agent_run_*`), OpenTelemetry traces, Loki logs. All exposed on `/metrics` (port 9595). |
| **Metrics‑Driven Autoscaling** | ✅ Partial | HPA on Gateway, Orchestrator workers, and each agent based on request rate, queue length, and latency. |
| **Failure Isolation / Chaos** | ✅ Implemented | Health probes, retry policies, compensation activities, chaos‑engine scripts (`scripts/tests/temporal_failover.sh`). |
| **Documentation Sync** | ✅ Updated | All docs now reference the correct Memory Service ports (Qdrant 10005, Redis 10003) and metric names. |
| **CI/CD Pipeline** | ❌ Missing | Lint, unit/integration tests, Docker image build, SBOM generation, Trivy scan, Helm chart release. |
| **Helm Chart** | ✅ Implemented | Deploys all core services, independent Qdrant and Redis pods, Identity, Policy, and agents. Values for `agentRegistry`, `policyRules`, and `memoryBackend` are configurable. |

---

## 📅 Roadmap (Phased Implementation)

| Phase | Goal | Key Deliverables | Approx. Effort |
|-------|------|-------------------|----------------|
| **0 – Baseline** | Verify current stack health | Health checks, metrics visible, docs synced | 1 day |
| **1 – Agent Contract & Registry** | Formalize `run` API, add ConfigMap registry | OpenAPI spec, registry helper library, dummy agent | 2 days |
| **2 – Policy Engine** | Add OPA service, basic rules (weight, runway occupancy) | Policy service, integration tests | 2 days |
| **3 – Identity Service** | JWT issuance & validation | Minimal IdP, middleware in Gateway | 2 days |
| **4 – Human‑in‑the‑Loop UI** | Task‑card UI (Slack/Web) + pause‑resume workflow | UI service, webhook integration | 3 days |
| **5 – Scaling & Autoscaling** | HPA for agents, queue buffering (Redis streams) | Autoscale manifests, load‑test scripts | 3 days |
| **6 – CI/CD Pipeline** | Automated lint, test, build, SBOM, image scan | GitHub Actions workflow, Helm release automation | 2 days |
| **7 – Production‑Ready Release** | Version bump, Helm chart release, docs finalization | Tag `vX.Y.Z`, update changelog, release notes | 1 day |

*Total estimated effort: ~15 person‑days.*

---

## 🛠️ Operational Checklist (Day‑to‑Day)

1. **Start infra** – `make dev-up` (Temporal + Redis + Qdrant).  
2. **Launch services** – `make dev-start-services`.  
3. **Verify health** – `curl http://localhost:9595/healthz`.  
4. **Check metrics** – `curl http://localhost:9595/metrics | grep agent_run_total`.  
5. **Run a demo wizard** – `python examples/marketing_campaign_wizard.py --approve --poll-orchestrator`.  
6. **Monitor dashboard** – Grafana dashboards (pre‑built in `infra/monitoring/`).  
7. **Scale if needed** – HPA will auto‑scale; monitor `agent_run_pending`.  
8. **Handle incidents** – Use `/events` endpoint to trigger emergency workflows (evacuation, fire, runway closure).  
9. **Audit** – All decisions stored in Memory Gateway; retrieve with `GET /memories/{coord}`.  
10. **Shutdown / upgrade** – Drain pods via `kubectl rollout pause` and `kubectl rollout resume` after new image rollout.

---

## 📚 Documentation Locations

- **User Manual** – `docs/user-manual/` (wizard usage, API reference).  
- **Technical Manual** – `docs/technical-manual/` (architecture, deployment, monitoring).  
- **Development Manual** – `docs/development-manual/` (local setup, testing, contribution guide).  
- **Roadmap** – this file `docs/roadmap-somagenthub.md`.  
- **Changelog** – `changelog.md` (kept up‑to‑date with each release).

---

## 🎯 Success Criteria

- **Zero unhandled crashes** during normal operation and holiday spikes.  
- **All requests** (human or automated) are logged, traced, and stored in Memory Gateway.  
- **Policy violations** are blocked and reported via alerts.  
- **Human approvals** complete within defined SLA (e.g., < 2 min for safety‑critical steps).  
- **Metrics** show < 5 % error rate across all services.  
- **CI pipeline** passes on every pull request.

---

*Document created by the AI‑architect assistant on 2025‑11‑03.*
