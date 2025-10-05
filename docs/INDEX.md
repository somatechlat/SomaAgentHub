# 📚 SomaAgent Documentation Index

**Last Updated:** October 5, 2025  
**Purpose:** Single source of truth for navigating all SomaAgent documentation

---

## 🚀 Quick Start (Start Here!)

| Document | Purpose | Audience | Time to Read |
|----------|---------|----------|--------------|
| **[README.md](README.md)** | Project overview and quick setup | Everyone | 5 min |
| **[Quickstart.md](Quickstart.md)** | Fast local deployment guide | Developers | 10 min |
| **[Kubernetes-Setup.md](Kubernetes-Setup.md)** | Production deployment on K8s | DevOps, SRE | 20 min |

---

## 📊 Current Status & Roadmap

### Platform Status
| Document | Purpose | Update Frequency | Audience |
|----------|---------|------------------|----------|
| **[PRODUCTION_READY_STATUS.md](PRODUCTION_READY_STATUS.md)** | ⭐ **Current implementation status & metrics** | Weekly | All |
| **[CANONICAL_ROADMAP.md](CANONICAL_ROADMAP.md)** | Development roadmap & sprint history | Bi-weekly | Product, Engineering |

> 💡 **Start with PRODUCTION_READY_STATUS.md** for the most current platform state

---

## 🏗️ Architecture & Design

### Core Architecture
| Document | Purpose | Last Updated | Audience |
|----------|---------|--------------|----------|
| **[SomaGent_Platform_Architecture.md](SomaGent_Platform_Architecture.md)** | Complete technical architecture | Oct 5, 2025 | Architects, Senior Eng |
| **[KAMACHIQ_Mode_Blueprint.md](KAMACHIQ_Mode_Blueprint.md)** | Autonomous mode design & workflows | Oct 5, 2025 | Product, Architects |
| **[SomaGent_Security.md](SomaGent_Security.md)** | Security architecture & policies | Oct 5, 2025 | Security, Compliance |
| **[SomaGent_SLM_Strategy.md](SomaGent_SLM_Strategy.md)** | LLM integration strategy | Oct 5, 2025 | ML Engineers |

### Subsystem Designs
Located in `design/` folder:
- `Agent_State_Machine.md` - Persona lifecycle and state transitions
- `Constitutional_AI_Design.md` - Policy enforcement architecture
- `Memory_Architecture.md` - SomaBrain fractal memory design
- `Observability_Stack.md` - Prometheus, Tempo, Loki setup

---

## 🔧 Development Guides

### Getting Started
| Document | Purpose | Audience | Time to Read |
|----------|---------|----------|--------------|
| **[DEVELOPMENT_GUIDELINES.md](DEVELOPMENT_GUIDELINES.md)** | Coding standards & best practices | All Developers | 15 min |
| **[PROMPT.md](PROMPT.md)** | Context prompt for AI assistants | AI-assisted devs | 5 min |

### Implementation Guides
Located in `development/` folder:
- `run_local_dev.md` - Local development setup
- `Testing_Strategy.md` - Testing approach & frameworks
- `Integration_Patterns.md` - Service integration guidelines
- `Database_Migrations.md` - Schema evolution guide

### API Documentation
Located in `development/api/` folder:
- Service-specific OpenAPI specs
- gRPC proto files
- Webhook schemas

---

## 📋 Sprint Documentation

### Active Sprints
Located in `sprints/` folder:

| Sprint | Focus | Status | Document |
|--------|-------|--------|----------|
| **Sprint-1** | Keycloak Integration | ✅ Complete | [Sprint-1.md](sprints/Sprint-1.md) |
| **Sprint-2** | OPA Integration | ✅ Complete | [Sprint-2.md](sprints/Sprint-2.md) |
| **Sprint-3** | Kafka Integration | ✅ Complete | [Sprint-3.md](sprints/Sprint-3.md) |
| **Sprint-4** | OpenAI Provider | ✅ Complete | [Sprint-4.md](sprints/Sprint-4.md) |
| **Sprint-5** | Redis Locks | ✅ Complete | [Sprint-5.md](sprints/Sprint-5.md) |
| **Sprint-6** | Qdrant Vector DB | ✅ Complete | [Sprint-6.md](sprints/Sprint-6.md) |
| **Sprint-7** | Analytics Integration | ✅ Complete | [Sprint-7.md](sprints/Sprint-7.md) |

### Sprint Reports
- **[WAVE_2_SPRINT_COMPLETION_REPORT.md](sprints/WAVE_2_SPRINT_COMPLETION_REPORT.md)** - Wave 2 sprints (OpenAI, Redis, Qdrant, Analytics)
- **[WAVE_2_FOLLOWUP_COMPLETION_REPORT.md](sprints/WAVE_2_FOLLOWUP_COMPLETION_REPORT.md)** - Follow-up integrations

### Archived Sprints
Historical sprint documentation in `sprints/archive/`

---

## 🛠️ Operational Runbooks

### Production Operations
Located in `runbooks/` folder:

#### Core Runbooks (Required)
| Runbook | Purpose | Audience | Scenario |
|---------|---------|----------|----------|
| **[incident_response.md](runbooks/incident_response.md)** | Incident handling, escalation, postmortems | SRE, On-call | Production incidents |
| **[tool_health_monitoring.md](runbooks/tool_health_monitoring.md)** | Adapter health checks, failure recovery | DevOps, SRE | Tool adapter failures |
| **[scaling_procedures.md](runbooks/scaling_procedures.md)** | Horizontal/vertical scaling playbooks | DevOps | High load scenarios |
| **[disaster_recovery.md](runbooks/disaster_recovery.md)** | Backup, restore, failover procedures | SRE | Data loss, region failure |

#### Advanced Runbooks (Recommended)
| Runbook | Purpose | Audience | Scenario |
|---------|---------|----------|----------|
| **[regional-failover.md](runbooks/regional-failover.md)** | Multi-region DR orchestration | SRE | Regional outage |
| **[kill_switch.md](runbooks/kill_switch.md)** | Emergency shutdown procedures | Leadership, SRE | Security breach, abuse |
| **[kamachiq_operations.md](runbooks/kamachiq_operations.md)** | Autonomous mode monitoring & control | Platform Team | KAMACHIQ operations |
| **[security.md](runbooks/security.md)** | Security procedures, compliance | Security Team | Security incidents |
| **[constitution_update.md](runbooks/constitution_update.md)** | Policy update workflow | Governance | Policy changes |

---

## 🚢 Deployment & Infrastructure

### Deployment Guides
Located in `deployment/` folder:

| Guide | Purpose | Audience | Environment |
|-------|---------|----------|-------------|
| **[Local_Development.md](deployment/Local_Development.md)** | Docker Compose setup | Developers | Local |
| **[Kubernetes_Production.md](deployment/Kubernetes_Production.md)** | K8s production deployment | DevOps | Production |
| **[Helm_Charts.md](deployment/Helm_Charts.md)** | Helm chart usage & customization | DevOps | K8s |
| **[Multi_Region.md](deployment/Multi_Region.md)** | Multi-region deployment | SRE | Global production |

### Infrastructure as Code
Located in `../infra/` folder:
- `terraform/` - Terraform modules for cloud resources
- `helm/` - Helm charts for all services
- `k8s/` - Raw Kubernetes manifests
- `monitoring/` - Prometheus, Grafana, Tempo configs

---

## 📈 Observability & Monitoring

### Observability Guides
Located in `observability/` folder:

| Guide | Purpose | Audience |
|-------|---------|----------|
| **[Metrics_Reference.md](observability/Metrics_Reference.md)** | Prometheus metrics catalog | SRE, DevOps |
| **[Distributed_Tracing.md](observability/Distributed_Tracing.md)** | Tempo/Jaeger trace analysis | Backend Devs |
| **[Log_Analysis.md](observability/Log_Analysis.md)** | Loki query patterns | SRE, Support |
| **[Alerting_Rules.md](observability/Alerting_Rules.md)** | Alert definitions & thresholds | SRE |
| **[Dashboard_Guide.md](observability/Dashboard_Guide.md)** | Grafana dashboard usage | All |

---

## 🧪 Testing & Quality

### Testing Documentation
Located in `../tests/` folder:

- **Unit Tests:** `tests/unit/` - Service-level unit tests
- **Integration Tests:** `tests/integration/` - Cross-service integration tests
- **E2E Tests:** `tests/e2e/` - End-to-end user scenarios
- **Performance Tests:** `tests/performance/` - Load & stress tests
- **Chaos Tests:** `tests/chaos/` - Chaos engineering scenarios

### Testing Guides
- `Testing_Strategy.md` - Overall testing approach
- `Integration_Testing.md` - Integration test patterns
- `Performance_Benchmarks.md` - Expected performance baselines

---

## 📜 Legal & Compliance

Located in `legal/` folder:

| Document | Purpose | Audience |
|----------|---------|----------|
| **[LICENSE](../LICENSE)** | Software license | Legal, Open Source Contributors |
| **[Privacy_Policy.md](legal/Privacy_Policy.md)** | User data handling | Product, Legal |
| **[Terms_of_Service.md](legal/Terms_of_Service.md)** | Service usage terms | Product, Legal |
| **[Security_Disclosure.md](legal/Security_Disclosure.md)** | Vulnerability reporting | Security Researchers |
| **[Compliance_Requirements.md](legal/Compliance_Requirements.md)** | GDPR, SOC2, HIPAA compliance | Compliance, Legal |

---

## 🎨 Diagrams & Visuals

Located in `diagrams/` folder:

### Architecture Diagrams
- `System_Overview.png` - High-level system architecture
- `Service_Mesh.png` - Microservice topology
- `Data_Flow.png` - Event and data flow
- `Deployment_Topology.png` - K8s deployment layout

### Sequence Diagrams
- `Session_Lifecycle.mmd` - User session flow
- `KAMACHIQ_Execution.mmd` - Autonomous mode workflow
- `Tool_Adapter_Flow.mmd` - Tool execution pattern

### State Diagrams
- `Agent_States.mmd` - Persona state machine
- `Capsule_States.mmd` - Task capsule lifecycle

All diagrams use Mermaid.js format (`.mmd`) for easy editing.

---

## 📚 Reference Materials

### Configuration Reference
| File | Purpose | Location |
|------|---------|----------|
| **[slm_profiles.yaml](slm_profiles.yaml)** | SLM model configurations | `docs/` |
| **Environment Variables** | Service configuration guide | `deployment/Environment_Variables.md` |
| **Port Assignments** | Service port reference | `deployment/Port_Reference.md` |

### Templates
Located in `templates/` folder:
- `Sprint_Template.md` - Sprint planning template
- `ADR_Template.md` - Architecture decision record template
- `Runbook_Template.md` - Operational runbook template
- `Service_README_Template.md` - Service documentation template

---

## 🔍 Finding Information

### By Role

**New Developer:**
1. Start with [README.md](README.md)
2. Follow [Quickstart.md](Quickstart.md)
3. Read [DEVELOPMENT_GUIDELINES.md](DEVELOPMENT_GUIDELINES.md)
4. Check `development/run_local_dev.md`

**DevOps Engineer:**
1. Read [Kubernetes-Setup.md](Kubernetes-Setup.md)
2. Review `deployment/Kubernetes_Production.md`
3. Study `runbooks/scaling_procedures.md`
4. Check `observability/Metrics_Reference.md`

**Architect:**
1. Start with [SomaGent_Platform_Architecture.md](SomaGent_Platform_Architecture.md)
2. Review [KAMACHIQ_Mode_Blueprint.md](KAMACHIQ_Mode_Blueprint.md)
3. Study `design/` folder contents
4. Check [CANONICAL_ROADMAP.md](CANONICAL_ROADMAP.md)

**Product Manager:**
1. Read [PRODUCTION_READY_STATUS.md](PRODUCTION_READY_STATUS.md)
2. Review [CANONICAL_ROADMAP.md](CANONICAL_ROADMAP.md)
3. Check sprint reports in `sprints/`
4. Review user-facing features in [README.md](README.md)

**Security Engineer:**
1. Start with [SomaGent_Security.md](SomaGent_Security.md)
2. Review `runbooks/security.md`
3. Check `legal/Security_Disclosure.md`
4. Study `legal/Compliance_Requirements.md`

### By Topic

**Authentication & Authorization:**
- `SomaGent_Security.md`
- `services/common/keycloak_client.py` (code)
- `services/common/opa_client.py` (code)
- Sprint-1, Sprint-2 docs

**Event Streaming:**
- `SomaGent_Platform_Architecture.md` (Section 3.3)
- `services/common/kafka_client.py` (code)
- Sprint-3 docs

**Vector Search & RAG:**
- `design/Memory_Architecture.md`
- `services/common/qdrant_client.py` (code)
- Sprint-6 docs

**LLM Integration:**
- `SomaGent_SLM_Strategy.md`
- `services/common/openai_provider.py` (code)
- Sprint-4 docs

**Autonomous Mode:**
- `KAMACHIQ_Mode_Blueprint.md`
- `services/orchestrator/workflows/kamachiq_workflow.py` (code)
- `runbooks/kamachiq_operations.md`

---

## 🔄 Document Lifecycle

### Update Frequencies

| Document Type | Update Frequency | Owner |
|---------------|------------------|-------|
| PRODUCTION_READY_STATUS.md | Weekly | Platform Team |
| CANONICAL_ROADMAP.md | Bi-weekly | Product Team |
| Architecture docs | Per major change | Architects |
| Runbooks | As needed | SRE Team |
| Sprint docs | Per sprint | Sprint Leads |

### Deprecation Process

Outdated documents are moved to `archive/deprecated/` with a deprecation notice at the top:

```markdown
⚠️ **DEPRECATED:** This document is superseded by [NEW_DOC.md](NEW_DOC.md)
```

---

## 📞 Getting Help

**Questions about documentation:**
- Open an issue on GitHub
- Contact Platform Team via Slack #somagent-platform

**Missing documentation:**
- Create an issue with label `documentation`
- Use templates in `templates/` folder

**Contribute documentation:**
- Follow [DEVELOPMENT_GUIDELINES.md](DEVELOPMENT_GUIDELINES.md)
- Submit PR with clear description
- Tag Platform Team for review

---

## 📝 Quick Reference Card

### Most Important Documents (Top 5)

1. **[PRODUCTION_READY_STATUS.md](PRODUCTION_READY_STATUS.md)** - Current platform status
2. **[SomaGent_Platform_Architecture.md](SomaGent_Platform_Architecture.md)** - Technical architecture
3. **[Kubernetes-Setup.md](Kubernetes-Setup.md)** - Deployment guide
4. **[runbooks/incident_response.md](runbooks/incident_response.md)** - Emergency procedures
5. **[CANONICAL_ROADMAP.md](CANONICAL_ROADMAP.md)** - Development roadmap

### Most Used Commands

```bash
# Start local development
./scripts/rapid-deploy-all.sh

# Run integration tests
pytest tests/integration/

# Build all images
./scripts/build-images.sh

# Deploy to K8s
kubectl apply -k infra/k8s/

# Check service health
./scripts/comprehensive-test-report.py
```

---

**Index Last Updated:** October 5, 2025  
**Maintained By:** Platform Documentation Team  
**Next Review:** October 12, 2025
