# Wave D: Production Hardening & Scale
**Phase**: Post-MVP → Production Ready  
**Timeline**: 4-6 weeks  
**Start Date**: October 2024

## Overview

Wave C delivered core infrastructure (observability, workflows, analytics). Wave D focuses on **hardening, security, and multi-region scale** to prepare for production launch.

---

## 🎯 Wave D Objectives

1. **Security Hardening** - Zero-trust, secrets management, audit compliance
2. **Multi-Region Scale** - Geographic distribution, data residency
3. **Advanced Features** - Marketplace, capsule sandboxing, billing integration

---

## 📋 Three Parallel Sprints

### **Sprint-8: Security & Compliance** 🔒
**Owner**: Security Squad  
**Duration**: 4 weeks  
**Dependencies**: Wave C infrastructure

#### Deliverables

**1. Zero-Trust mTLS (SPIRE)**
- Deploy SPIRE server + agents in Kubernetes
- Configure SPIFFE identities for all 6 services
- Implement mTLS for inter-service communication
- Migrate from plaintext HTTP to HTTPS internally

**Files to Create:**
```
infra/k8s/spire/
  ├── spire-server.yaml
  ├── spire-agent.yaml
  └── trust-bundle.yaml
services/common/spiffe_auth.py
services/*/app/spiffe_config.py
```

**2. Secrets Management (Vault)**
- Deploy HashiCorp Vault in Kubernetes
- Migrate secrets from K8s Secrets to Vault
- Implement dynamic secret rotation
- Configure service authentication via SPIFFE

**Files to Create:**
```
infra/k8s/vault/
  ├── vault-server.yaml
  ├── vault-unsealer.yaml
  └── vault-policies/
services/common/vault_client.py
scripts/rotate-secrets.sh
```

**3. Audit Logging**
- Implement structured audit logs (who/what/when/where)
- Send audit events to ClickHouse
- Create audit dashboards in Grafana
- Compliance reporting endpoints

**Files to Create:**
```
services/common/audit_logger.py
infra/clickhouse/migrations/002_audit_tables.sql
scripts/audit-report.py
tests/integration/test_audit.py
```

**4. Security Scanning**
- Container vulnerability scanning (Trivy)
- SBOM generation for all images
- Secrets scanning in CI/CD
- Dependency vulnerability checks

**Files to Create:**
```
.github/workflows/security-scan.yml
scripts/scan-vulnerabilities.sh
scripts/generate-sbom.sh
```

**Success Metrics:**
- ✅ All services communicate via mTLS
- ✅ Zero plaintext secrets in codebase
- ✅ 100% audit coverage for write operations
- ✅ Security scan passing in CI/CD

---

### **Sprint-9: Multi-Region Deployment** 🌍
**Owner**: Platform Squad  
**Duration**: 4 weeks  
**Dependencies**: Wave C Kubernetes manifests

#### Deliverables

**1. Multi-Region Infrastructure**
- Terraform modules for AWS (us-west-2, eu-west-1)
- Kubernetes cluster per region
- Cross-region network peering
- Global load balancer (Route53 + health checks)

**Files to Create:**
```
infra/terraform/
  ├── modules/
  │   ├── eks-cluster/
  │   ├── vpc-peering/
  │   └── global-lb/
  ├── us-west-2/
  │   └── main.tf
  └── eu-west-1/
      └── main.tf
scripts/deploy-region.sh
```

**2. Data Residency**
- Regional ClickHouse clusters (no cross-region replication)
- Regional Redis caches
- Region-aware routing in gateway-api
- Data locality enforcement

**Files to Create:**
```
services/gateway-api/app/region_router.py
services/analytics-service/app/regional_writer.py
infra/k8s/region-config/
  ├── us-west-2.yaml
  └── eu-west-1.yaml
```

**3. Cross-Region Observability**
- Centralized Prometheus federation
- Multi-region Grafana dashboards
- Cross-region alerting
- SLO tracking per region

**Files to Create:**
```
infra/k8s/observability/prometheus-federation.yaml
infra/grafana/dashboards/multi-region-overview.json
scripts/check-regional-slos.sh
```

**4. Disaster Recovery**
- Automated failover procedures
- DR drill automation
- RTO/RPO measurement
- Runbooks for regional failures

**Files to Create:**
```
docs/runbooks/regional-failover.md
scripts/dr-drill.sh
tests/integration/test_failover.py
services/orchestrator/workflows/dr_workflow.py
```

**Success Metrics:**
- ✅ 2 regions deployed (US + EU)
- ✅ < 100ms cross-region latency for metadata
- ✅ 99.9% uptime per region
- ✅ DR drill completes in < 15 minutes

---

### **Sprint-10: Marketplace & Billing** 💰
**Owner**: Product Squad  
**Duration**: 4 weeks  
**Dependencies**: Wave C analytics, Sprint-8 security

#### Deliverables

**1. Capsule Marketplace Backend**
- PostgreSQL schema for capsule catalog
- Capsule publishing API with signature verification
- Search and discovery endpoints
- Performance ranking system

**Files to Create:**
```
services/marketplace-service/
  ├── Dockerfile
  ├── requirements.txt
  ├── app/
  │   ├── main.py
  │   ├── models.py
  │   ├── routes/
  │   │   ├── publish.py
  │   │   ├── search.py
  │   │   └── install.py
  │   └── ranking.py
infra/postgres/marketplace_schema.sql
tests/integration/test_marketplace.py
```

**2. Capsule Sandboxing**
- Docker-based sandbox runtime
- Resource limits (CPU, memory, network)
- Execution time limits
- Output capture and streaming

**Files to Create:**
```
services/capsule-runner/
  ├── Dockerfile
  ├── requirements.txt
  ├── app/
  │   ├── sandbox.py
  │   ├── resource_limiter.py
  │   └── output_streamer.py
infra/k8s/capsule-runner.yaml
tests/integration/test_sandbox.py
```

**3. Billing Integration**
- Usage tracking (tokens, compute minutes, storage)
- Billing events to ClickHouse
- Invoice generation API
- Stripe/payment integration

**Files to Create:**
```
services/billing-service/app/usage_tracker.py
services/billing-service/app/invoice_generator.py
services/billing-service/app/stripe_client.py
infra/clickhouse/migrations/003_billing_views.sql
tests/integration/test_billing.py
```

**4. Marketplace UI**
- Capsule gallery with search/filters
- Capsule detail pages
- Install/uninstall flows
- Usage analytics per capsule

**Files to Create:**
```
apps/marketplace-ui/
  ├── src/
  │   ├── pages/
  │   │   ├── Gallery.tsx
  │   │   ├── CapsuleDetail.tsx
  │   │   └── MyInstallations.tsx
  │   ├── components/
  │   │   ├── CapsuleCard.tsx
  │   │   ├── SearchBar.tsx
  │   │   └── RankingBadge.tsx
  │   └── api/marketplace.ts
tests/e2e/test_marketplace_ui.py
```

**Success Metrics:**
- ✅ 10+ demo capsules published
- ✅ Sandbox execution < 5s overhead
- ✅ Billing events 100% accurate
- ✅ Marketplace UI functional

---

## 🔄 Parallel Execution Strategy

```
Week 1-2:
  Sprint-8: SPIRE setup + Vault deployment
  Sprint-9: Terraform modules + first region
  Sprint-10: Marketplace schema + API scaffolding

Week 2-3:
  Sprint-8: mTLS migration + secret rotation
  Sprint-9: Second region + data residency
  Sprint-10: Sandbox runtime + billing tracker

Week 3-4:
  Sprint-8: Audit logging + security scanning
  Sprint-9: Cross-region observability + DR
  Sprint-10: Stripe integration + marketplace UI

Week 4:
  All Sprints: Integration testing + documentation
```

---

## 📊 Implementation Files Count

| Sprint | Services | Scripts | Tests | Infra | Total |
|--------|----------|---------|-------|-------|-------|
| Sprint-8 | 2 modules | 4 | 3 | 8 manifests | ~17 |
| Sprint-9 | 3 modules | 5 | 4 | 12 TF files | ~24 |
| Sprint-10 | 3 services | 2 | 5 | 4 schemas | ~14 |
| **Total** | **8** | **11** | **12** | **24** | **~55** |

---

## 🎓 Learning Resources

**Sprint-8:**
- [SPIRE Documentation](https://spiffe.io/docs/)
- [Vault on Kubernetes](https://developer.hashicorp.com/vault/tutorials/kubernetes)
- [NIST Audit Guidelines](https://www.nist.gov/publications)

**Sprint-9:**
- [Terraform AWS EKS](https://registry.terraform.io/modules/terraform-aws-modules/eks/aws/latest)
- [Prometheus Federation](https://prometheus.io/docs/prometheus/latest/federation/)
- [AWS Route53 Health Checks](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover.html)

**Sprint-10:**
- [Docker Sandboxing](https://docs.docker.com/engine/security/)
- [Stripe API](https://stripe.com/docs/api)
- [Cosign for Container Signing](https://docs.sigstore.dev/cosign/overview/)

---

## ✅ Readiness Checklist

**Before Starting:**
- [ ] Wave C fully deployed and tested
- [ ] All services have health endpoints
- [ ] ClickHouse analytics working
- [ ] Temporal workflows executing
- [ ] Team assignments confirmed

**After Completion:**
- [ ] Security scan passing
- [ ] Multi-region deployment tested
- [ ] Marketplace has 10+ capsules
- [ ] DR drill successful
- [ ] Documentation complete
- [ ] Ready for production launch

---

## 🚀 Next Steps

After Wave D completion:
1. **Beta Launch** - Invite first customers
2. **Load Testing** - Chaos engineering, stress tests
3. **Performance Tuning** - Optimize hot paths
4. **Feature Iteration** - Based on beta feedback
5. **General Availability** - Public launch

---

*Wave D transforms SomaAgent from infrastructure prototype to production-ready platform.*
