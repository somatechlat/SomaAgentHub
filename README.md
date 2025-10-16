# 🚀 SomaAgentHub

**The Next Generation Agent Orchestration Platform**

> Enterprise-grade infrastructure for autonomous agent systems with parallel execution, real-time orchestration, and production-ready deployment

---

## 📋 Overview

SomaAgentHub is the coordination layer that powers the Soma platform. The hub connects specialized services—gateway, orchestrator, policy enforcement, memory, model access, and tooling—into a unified runtime for autonomous agent programs. The project ships with hardened infrastructure manifests, repeatable developer workflows, and documentation that keeps code and operations in lockstep.

---

## ⚡ Core Capabilities

### 🧠 Intelligent Orchestration
- **Multi-Agent Coordination** – Orchestrator and MAO services drive structured work across specialized agents and workflows.
- **Parallel Execution** – Temporal-backed job queues keep long-running tasks resilient and horizontally scalable.
- **Task Capsule System** – `services/task-capsule-repo` holds reusable execution capsules that bundle tools, prompts, and policies.
- **Autonomous Project Execution** – Wizard flows in `services/gateway-api` launch complex delivery tracks from a single request.

### 🔄 Conversation & Memory
- **Memory Gateway** – Vector and key/value storage with Qdrant integrations for durable context recall.
- **Real-Time Context Sharing** – Shared Redis, policy, and identity services broadcast state across parallel agents.
- **Conversation Engine** – Gateway wizard engine plus orchestrator sessions manage multi-turn dialogue and approvals.

### ⚙️ Production Infrastructure
- **Kubernetes Native** – `infra/k8s` and `k8s/helm/soma-agent` provide production manifests with probes, resources, and tolerations.
- **Helm Deployment** – One chart installs the entire hub with environment-aware overrides and metrics wiring.
- **Automated CI/CD Hooks** – Make targets and scripts build, scan, push, and verify every service image.
- **Health Probes & Metrics** – Every critical service exposes `/health`, `/ready`, and `/metrics` endpoints out of the box.

### 🚄 Rapid Development
- **3-Day Sprint Cadence** – Roadmaps and runbooks in `docs/` map repeatable sprint waves across the stack.
- **Auto-Documentation** – Handbooks in `docs/` pair with service READMEs to eliminate drift between code and operations.
- **Zero Configuration Drift** – Terraform, Helm, and Make-based workflows ensure environments stay in sync.
- **Integrated Testing** – Smoke, integration, and e2e harnesses in `scripts/` and `tests/` validate every change.

---

## 🏗️ Architecture

### Core Services

| Service | Default Port | Purpose |
| --- | --- | --- |
| **Gateway API** | 10000 | Public ingress for UI, CLI, and partner integrations. Handles wizard flows and session fan-out. |
| **Orchestrator** | 10001 | Coordinates multi-agent workflows, talks to Temporal, identity, and policy services. |
| **Identity Service** | 10002 | Issues access tokens and validates identities for every agent-facing request. |
| **Memory Gateway** | 8000 | Stores and retrieves long-term context via Qdrant for agent recall. |
| **Policy Engine** | (custom) | Enforces constitutional rules with Redis-backed caching and constitution service integration. |
| **Memory Gateway** | 8000 | Stores and retrieves long-term context via Qdrant or in-memory fallback for development. |

### System Components

```
┌─────────────────────────────────────────┐
│             SomaAgentHub                │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐  ┌──────────────┐     │
│  │ Gateway API  │  │ Policy Engine│     │
│  │    (8080)    │  │    (1002)    │     │
│  └──────┬───────┘  └──────┬───────┘     │
│         │                 │              │
│  ┌──────────────────────────────────┐    │
│  │        Orchestrator (1004)       │    │
│  │   Temporal Workflows & Sessions  │    │
│  └──────────────────────────────────┘    │
│                │                          │
│  ┌──────────────────────────────────┐    │
│  │       Memory Gateway (8000)      │    │
│  │   Vector + KV Recall for Agents  │    │
│  └──────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
         ↓
    Kubernetes Cluster
    Helm-managed deployment
```

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local tooling)
- Kind or Kubernetes 1.24+
- Helm 3+
- `kubectl`

### Deploy the Hub Locally

**1. Bootstrap Local Control Plane**
```bash
kind create cluster --name soma-agent-hub || true
```

**2. Build and Install Services**
```bash
make start-cluster
```

**3. Verify Pods and Services**
```bash
kubectl get pods -n soma-agent-hub
kubectl get svc -n soma-agent-hub
```

### Local Development Loop

**Start Temporal & Redis Dependencies**
```bash
make dev-up
```

**Run Gateway and Orchestrator Locally**
```bash
make dev-start-services
```

**Port-Forward the Gateway**
```bash
make port-forward-gateway LOCAL=8080 REMOTE=8080
```

**Run End-to-End Smoke Tests**
```bash
make k8s-smoke
```

---

## 📚 Documentation

| Document | Purpose |
| --- | --- |
| `docs/INDEX.md` | Master index for architecture, operations, and roadmap content. |
| `docs/CANONICAL_ROADMAP.md` | Sequenced delivery plan with sprint-ready milestones. |
| `docs/runbook.md` | Operational runbook covering deployments, recovery, and observability. |
| `docs/Kubernetes-Setup.md` | Step-by-step guide for installing the hub on Kubernetes clusters. |
| `docs/CRITICAL_FIXES_REPORT.md` | Traceability for infrastructure fixes and resilience improvements. |

Service-specific READMEs live beside the code under `services/`, and infra playbooks are captured in `infra/` and `k8s/` directories.

---

## 🎯 Project Status

- **Core Services** – Gateway, orchestrator, policy, identity, and memory services ship with production manifests and health checks.
- **Infrastructure** – Helm chart, Kind bootstrap, and Terraform modules (see `infra/terraform/`) keep environments reproducible.
- **Observability** – Prometheus, Grafana, Loki, and alert routing are wired through `k8s/monitoring/` and Make targets.
- **Compliance & Policy** – Constitution and policy artifacts live under `services/constitution-service` and integrate with the policy engine.
- **Roadmaps & Playbooks** – Every sprint deliverable is mirrored in `docs/` for zero documentation drift.

---

## 🌟 What Sets SomaAgentHub Apart

| Capability | SomaAgentHub | Traditional Agent Frameworks |
| --- | --- | --- |
| **Production Infrastructure** | ✅ Full Kubernetes, Helm, and Terraform stack included | ❌ Usually left to the adopter |
| **Governance & Policy** | ✅ Dedicated policy engine with constitution service | ❌ Custom build required |
| **Memory Architecture** | ✅ Pluggable Qdrant/Redis memory gateway | ⚠️ Basic in-memory or third-party |
| **CI/CD Automation** | ✅ Make-driven builds, scans, and deploys | ⚠️ Manual scripts |
| **Observability** | ✅ Metrics, probes, and Grafana dashboards out of the box | ❌ Minimal logging |

---

## 🛠️ Technology Stack

- **Languages**: Python (services), TypeScript/React (admin console), Bash (operations)
- **Core Services**: FastAPI, Temporal, Redis, PostgreSQL, Qdrant
- **Infrastructure**: Kubernetes, Helm, Kind, Terraform
- **CI/CD & Automation**: GitHub Actions, Make, Docker, Syft, Trivy
- **Observability**: Prometheus, Grafana, Loki, OpenTelemetry

---

## 🤝 Contributing

1. Fork the repository and create a feature branch from `soma_integration`.
2. Enable the repo virtual environment and install dev tooling:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```
3. Run linting and tests before submitting a pull request:
   ```bash
   ruff check .
   make k8s-smoke
   ```
4. Open a PR with a summary, testing evidence, and linked documentation updates.

---

## 📞 Support & Next Steps

Questions, bug reports, or feature requests? Open an issue or start a discussion in this repository. For deployment assistance, follow the runbook in `docs/runbook.md` and the Kubernetes guide in `docs/Kubernetes-Setup.md`.

---

**SomaAgentHub: Where Development Velocity Meets Production Excellence.**
