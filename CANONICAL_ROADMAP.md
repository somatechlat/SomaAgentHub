# 🚀 SomaAgentHub Production Roadmap - Canonical Implementation

## 📋 Executive Summary

Production-ready taxi-service builder with PostgreSQL-backed capsule registry, Kubernetes-native agent spawning, and complete payment integration. Built for scale, security, and observability.

## 🗺️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (OAuth2 + OPA)               │
├─────────────────────────────────────────────────────────────┤
│                   Orchestrator (Temporal)                   │
├─────────────────────────────────────────────────────────────┤
│  Agent-Spawner  │  Pricing Service │  Stripe Integration    │
├─────────────────────────────────────────────────────────────┤
│          PostgreSQL │ MinIO │ Linkerd mTLS │ Vault          │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 Sprint Planning (12-Week Cycle)

### **Sprint 1: Foundation (Week 1-2)** 
**Focus: PostgreSQL Migration & Core Models**

**User Story**: "As a developer, I can persist capsule manifests in PostgreSQL instead of memory"

**Deliverables**:
- ✅ PostgreSQL-backed Capsule ORM model
- ✅ AgentInstance model with k8s tracking
- ✅ Database migrations
- ✅ Registry API endpoints

**Acceptance Criteria**:
- [ ] All capsule operations use PostgreSQL
- [ ] UUID-based primary keys
- [ ] Version tracking enabled
- [ ] 100% API compatibility

### **Sprint 2: Agent Management (Week 3-4)**
**Focus: Kubernetes-Native Agent Spawning**

**User Story**: "As a platform admin, I can spawn agent pods"

**Deliverables**:
- ✅ Agent-Spawner FastAPI service
- ✅ Kubernetes Python client integration
- ✅ Pod lifecycle management
- ✅ Auto-cleanup policies

**Acceptance Criteria**:
- [ ] Agents spawn as k8s Jobs/Deployments
- [ ] Namespace isolation per tenant
- [ ] Resource limits enforced
- [ ] Automatic pod termination

### **Sprint 3: Payment Integration (Week 5-6)**
**Focus: Stripe Integration & Budget Management**

**User Story**: "As a customer, I can pay for taxi builds with Stripe and get receipts"

**Deliverables**:
- ✅ Stripe SDK integration
- ✅ Webhook handling
- ✅ Budget policies in OPA
- ✅ Receipt storage

**Acceptance Criteria**:
- [ ] Stripe payment flows working
- [ ] Webhooks processed reliably
- [ ] Budget enforcement active
- [ ] Receipts stored in PostgreSQL

### **Sprint 4: Security & Observability (Week 7-8)**
**Focus: mTLS, Tracing, Vault**

**User Story**: "As a security engineer, all services communicate with mTLS and are monitored"

**Deliverables**:
- ✅ Linkerd mesh with mTLS
- ✅ OpenTelemetry tracing
- ✅ Vault secrets management
- ✅ Prometheus metrics dashboards

**Acceptance Criteria**:
- [ ] All inter-service mTLS
- [ ] End-to-end tracing visible
- [ ] Secrets in Vault only
- [ ] Key metrics monitored

### **Sprint 5: Taxi-Specific Features (Week 9-10)**
**Focus: Taxi Service Templates & Automation**

**User Story**: "As a taxi company, I can generate complete taxi apps with one command"

**Deliverables**:
- ✅ Taxi-specific Jinja2 templates
- ✅ FastAPI + React stack
- ✅ Database migrations included
- ✅ Payment gateway templates

**Acceptance Criteria**:
- [ ] Taxi app generates end-to-end
- [ ] Includes driver & customer apps
- [ ] Stripe payment integration
- [ ] Real-time tracking enabled

### **Sprint 6: Testing & Production (Week 11-12)**
**Focus: E2E Testing & Production Readiness**

**User Story**: "As a QA engineer, I can run complete end-to-end tests"

**Deliverables**:
- ✅ Pytest test suite
- ✅ Playwright UI tests
- ✅ Chaos engineering tests
- ✅ Production deployment guide

**Acceptance Criteria**:
- [ ] 90% test coverage
- [ ] Chaos tests passing
- [ ] Load tests completed
- [ ] Production runbook ready

## 🔧 Technical Implementation

### **Vibe Coding Rules**
1. **Type Safety**: Use Pydantic models everywhere
2. **Async First**: All services async/await
3. **Database First**: PostgreSQL with SQLModel
4. **K8s Native**: All services containerized
5. **Observability**: OpenTelemetry + Prometheus
6. **Security**: mTLS + Vault + OPA

### **Technology Stack**
- **Backend**: FastAPI + SQLModel + PostgreSQL
- **Orchestration**: Kubernetes + Temporal
- **Payments**: Stripe Python SDK
- **Security**: Linkerd + Vault + OPA
- **Observability**: OpenTelemetry + Prometheus
- **Storage**: MinIO for artifacts, PostgreSQL for metadata

### **Database Schema**
```sql
-- Capsule Registry
CREATE TABLE capsules (
    id UUID PRIMARY KEY,
    version VARCHAR(50) NOT NULL,
    type ENUM('static', 'workflow', 'external_service', 'analytic'),
    manifest_yaml TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Agent Instances
CREATE TABLE agent_instances (
    id UUID PRIMARY KEY,
    agent_type VARCHAR(100) NOT NULL,
    capsule_id UUID,
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    status VARCHAR(20) NOT NULL,
    k8s_namespace VARCHAR(100) NOT NULL,
    k8s_job_name VARCHAR(100),
    k8s_deployment_name VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 🎯 Success Metrics

### **Performance Targets**
- Build time < 5 minutes (minimal app)
- 99.9% uptime
- < 2 second API response times
- Support 1000+ concurrent builds

### **Security Requirements**
- All services with mTLS
- Secrets in Vault only
- SBOM scanning for all images
- CVE < 7 threshold

### **Observability Standards**
- 100% service tracing
- Key metrics in Prometheus
- Prometheus metrics dashboards for all services
- Alerting on SLO breaches

## 🚀 Getting Started

```bash
# Quick start
git clone https://github.com/somatechlat/SomaAgentHub.git
cd SomaAgentHub
make dev-up

# Run first sprint
make sprint-1-init
make test
```

## 📈 Progress Tracking

- [ ] Sprint 1: Foundation (Week 1-2)
- [ ] Sprint 2: Agent Management (Week 3-4)
- [ ] Sprint 3: Payment Integration (Week 5-6)
- [ ] Sprint 4: Security (Week 7-8)
- [ ] Sprint 5: Taxi Features (Week 9-10)
- [ ] Sprint 6: Production (Week 11-12)

---

*Last Updated: November 14, 2025*  
*Next Review: Weekly Sprint Planning*