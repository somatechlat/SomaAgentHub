# Multi-Agent Orchestration

**Agent coordination through SomaAgentHub services**

> SomaAgentHub provides orchestration capabilities through Temporal workflows, wizard engines, and service coordination.

---

## 🎯 Overview

SomaAgentHub orchestrates agents through:

- **Gateway API** (port 10000) - Entry point and wizard engine
- **Orchestrator** (port 10001) - Temporal workflow coordination  
- **Identity Service** (port 10002) - Authentication
- **MAO Service** - Multi-Agent Orchestrator workflows

### Core Services

**Gateway API:**
- FastAPI application with wizard engine
- Session management via Redis
- HTTP endpoints for UI and CLI integration

**Orchestrator:**
- Temporal client for durable workflows
- SPIFFE/SPIRE security integration
- OpenTelemetry observability

**Supporting Services:**
- Policy Engine (optional, port 10020)
- Memory Gateway (optional, container port 8000)
- Various specialized services in `services/` directory

---

## 🚀 Getting Started

### Available Examples

**Marketing Campaign Wizard (Python CLI):**
```bash
source .venv/bin/activate
python examples/marketing_campaign_wizard.py --approve --poll-orchestrator \
  --plan-output plans/marketing-campaign.json
```
Use this to gather inputs, render the execution plan, and trigger MAO in one go. Requires the orchestrator container (`somaagenthub_orchestrator`) plus Temporal to be running.

**Monitor a Running Workflow:**
```bash
source .venv/bin/activate
python examples/monitor_mao_workflow.py mao-mao-<workflow-id> --show-history-length
```
Copy the `workflow_id` returned by the wizard CLI and watch it progress to `completed`, `failed`, or `cancelled`.

**Legacy HTTP Wizard Walkthrough:**
```bash
./examples/wizard-demo.sh
```

**MAO Project Creation Script:**
```bash
cd examples/mao-project/
python create_project.py
```

**Kamachiq Autonomous Demo:**
```bash
cd examples/kamachiq-demo/
python autonomous_project_demo.py
```

### CLI Usage

The CLI at `cli/soma` provides commands for:
- `soma login` - Authentication
- `soma chat` - Interactive conversations
- `soma capsule list` - Browse available capsules
- `soma agent create` - Create new agents
- `soma workflow start` - Launch workflows

---

## 🔧 Technical Architecture

### Service Configuration

**Gateway API Configuration:**
- FastAPI application with wizard engine
- Handles HTTP requests and wizard sessions
- Integrates with Redis for session state
- Provides health, ready, and metrics endpoints

**Orchestrator Configuration:**
- Temporal client for workflow execution
- Configurable via environment variables
- SPIFFE/SPIRE integration for security
- Observability with OpenTelemetry

**Deployment Configuration:**
- Kubernetes manifests in `k8s/` directory
- Helm charts for templated deployment
- Docker Compose for local development
- Environment-specific configuration files

---

## 📊 Monitoring & Observability

### Service Endpoints

**Health Monitoring:**
- `/health` or `/healthz` - Service health status (Gateway exposes `/healthz`)
- `/ready` - Readiness check for dependencies
- `/metrics` - Prometheus metrics endpoint

**Available Metrics:**
- HTTP request metrics via OpenTelemetry
- Service-specific performance counters
- Resource utilization (CPU, memory)
- Temporal workflow execution metrics

### Observability Stack

**Monitoring Infrastructure:**
- Prometheus for metrics collection
- Grafana for visualization (configured in `infra/monitoring/`)
- Loki for log aggregation
- OpenTelemetry for distributed tracing

---

## 🛠️ Development

### Local Setup

**Start Infrastructure:**
```bash
make dev-up  # Start Temporal + Redis
```

**Run Services:**
```bash
make dev-start-services  # Gateway + Orchestrator
```

**Port Forward:**
```bash
make port-forward-gateway LOCAL=8080 REMOTE=10000
```

### Testing

**Smoke Tests:**
```bash
make k8s-smoke
```

**Integration Tests:**
```bash
pytest testing-workbench/integration/
```

---

## 📚 More Information

For detailed deployment and configuration:
- **[Technical Manual](../../technical-manual/index.md)** - Architecture and deployment
- **[Development Manual](../../development-manual/index.md)** - Local setup and development
- **Service READMEs** - Individual service documentation in `services/` directories

> **Heads-up:** The downstream agent runtime (`somaAgent01_*` services from the `somaagent01` project) is still stabilising. Until those worker containers stay healthy, MAO workflows will remain in a `running` state and tool execution will be deferred. Use `examples/monitor_mao_workflow.py` to observe progress and rerun end-to-end validation once the agent stack is marked ready.

---

**Ready to start orchestrating? Try the [Quick Start Tutorial](../quick-start-tutorial.md) or explore the examples in the `examples/` directory.**
