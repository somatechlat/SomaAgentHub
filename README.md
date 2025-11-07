# SomaAgentHub

[![CI](https://github.com/somatechlat/somaAgentHub/actions/workflows/ci.yml/badge.svg)](https://github.com/somatechlat/somaAgentHub/actions/workflows/ci.yml)

**Production‑ready orchestration platform for autonomous agents**


## Overview
SomaAgentHub is the coordination layer that powers the Soma platform. It provides a gateway, orchestrator (Temporal), identity service, memory gateway, policy engine, observability, and Helm chart for Kubernetes. **All placeholder code, stubs, and demo‑only implementations are being removed** in a series of focused sprints. The current development plan is captured in the **canonical sprint roadmap**.


## Quick Start (Local Development)

> **Note**: The **Memory Gateway** and **Policy Engine** services are now **enabled by default** in the Helm chart and Docker‑Compose configuration. They listen internally on port `8000` (Memory Gateway) and `10020` (Policy Engine) and are exposed externally via the canonical ports `10021` and `10020` respectively.

### Running All Tests Locally

The repository now includes a convenient Make target to run the full test suite across all services:

```bash
make test-all

### Deploying with Helm

The platform can be installed into a Kubernetes cluster using the provided Helm chart.

```bash
# Ensure you have a cluster (e.g., Kind) and Helm installed
make start-cluster   # creates a Kind cluster and sets up namespaces

# Install/upgrade the SomaAgentHub release
make helm-upgrade    # uses the current Git commit SHA as the image tag
```

The chart respects the `global` and `services` sections in `k8s/helm/soma-agent/values.yaml`.  By default the **Memory Gateway** and **Policy Engine** are enabled (see the `services` block).  To disable them, set `enabled: false` for the corresponding service and re‑run `make helm-upgrade`.

You can also lint the chart locally before deployment:

```bash
make helm-lint
```
```

This target installs any service‑specific dependencies and executes `pytest` for each service's test directory.
```bash
```bash
# Deploy the full stack using the canonical Helm chart (includes Qdrant, Redis, Memory‑Gateway, etc.)
make dev-up   # creates a Kind cluster and installs the helm chart
```
This creates a Kind cluster, builds all images, generates an optional mTLS secret, and installs the Helm chart.

---

## Documentation
- **DEPLOYMENT.md** – Full step‑by‑step deployment guide.
- **Sprint Roadmap** – Detailed sprint‑by‑sprint plan for removing stubs and delivering real functionality. See `docs/sprint-roadmap.md`.
- **Roadmap (Canonical Index)** – See `docs/roadmap-somagenthub.md` for links to the current sprint roadmap and production plan.
- **CONTRIBUTING.md** – Development workflow, testing, and PR process.
- **docs/helm-values.md** – Complete Helm values reference.
- **docs/ci-cd.md** – CI pipeline overview.
- **docs/troubleshooting.md** – Common issues and fixes.
- **docs/release.md** – Release and versioning process.
- **docs/glossary.md** – Glossary of terms.

---

## License
Apache License 2.0

---

*Happy hacking!*# 🚀 SomaAgentHub

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
- **Health Probes & Metrics** – Every critical service exposes health endpoints (`/health` and `/ready`); Gateway exposes `/healthz`; all services export `/metrics`.

### 🚄 Rapid Development
- **3-Day Sprint Cadence** – Roadmaps and runbooks in `docs/` map repeatable sprint waves across the stack.
- **Auto-Documentation** – Handbooks in `docs/` pair with service READMEs to eliminate drift between code and operations.
- **Zero Configuration Drift** – Terraform, Helm, and Make-based workflows ensure environments stay in sync.
- **Integrated Testing** – Smoke, integration, and e2e harnesses in `scripts/` and `tests/` validate every change.

---

## 🏗️ Architecture

### Core Services

| Service | Host Port | Purpose |
| --- | --- | --- |
| **Gateway API** | 10000 | Public ingress for UI, CLI, and partner integrations. Handles wizard flows and session fan-out. |
| **Orchestrator** | 10001 | Coordinates multi-agent workflows, talks to Temporal, identity, and policy services. |
| **Identity Service** | 10002 | Issues access tokens and validates identities for every agent-facing request. |
| **Memory Gateway** | (container 8000) | Stores and retrieves long-term context via Qdrant for agent recall. Enabled by default. |
| **Policy Engine** | 10020 | Provides rule-based guardrails when deployed alongside orchestrator. Enabled by default. |

### System Components

```
┌─────────────────────────────────────────┐
│             SomaAgentHub                │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐  ┌──────────────┐     │
│  │ Gateway API  │  │ Policy Engine│     │
│  │   (10000)    │  │   (10020)    │     │
│  └──────┬───────┘  └──────┬───────┘     │
│         │                 │              │
│  ┌──────────────────────────────────┐    │
│  │       Orchestrator (10001)       │    │
│  │   Temporal Workflows & Sessions  │    │
│  └──────────────────────────────────┘    │
│                │                          │
│  ┌──────────────────────────────────┐    │
│  │      Memory Gateway            │    │
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
make port-forward-gateway LOCAL=8080 REMOTE=10000
```

**Run End-to-End Smoke Tests**
```bash
make k8s-smoke
```

---

## 📚 Documentation

| Document | Purpose |
| --- | --- |
| `docs/development-manual/index.md` | Development workflows, local setup, and sprint notes. |
| `docs/technical-manual/index.md` | Architecture, deployment, monitoring, and runbook index. |
| `docs/onboarding-manual/index.md` | Context and ramp-up material for new contributors. |
| `docs/user-manual/index.md` | End-user capabilities and feature walkthroughs. |
| `docs/style-guide.md` | Source of truth for documentation tone, formatting, and terminology. |
| `PORT_REFERENCE.md` | Verified mapping between host/container ports and documentation references. |

Service-specific READMEs live beside the code under `services/`, and infra playbooks are captured in `infra/` and `k8s/` directories.

---

## 🎯 Project Status

- **Core Services** – Gateway, orchestrator, and identity ship with production manifests; policy engine and memory gateway are optional and disabled in the default docker-compose stack.
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

1. Fork the repository and create a feature branch from `main`.
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

Questions, bug reports, or feature requests? Open an issue or start a discussion in this repository. For deployment assistance, follow the runbooks under `docs/technical-manual/runbooks/` (start with `service-is-down.md`) and the deployment guide in `docs/technical-manual/deployment.md`.

---

**SomaAgentHub: Where Development Velocity Meets Production Excellence.**
