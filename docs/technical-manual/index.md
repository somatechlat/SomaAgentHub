# Technical Manual

**Operations, deployment, and system administration guide for SomaAgentHub.**

Welcome to the Technical Manual. This guide is for **SREs, DevOps Engineers, and System Administrators** who deploy, operate, and maintain SomaAgentHub in production environments.

---

## 📚 Quick Navigation

### Core Documentation

| Section | Purpose | Audience |
|---------|---------|----------|
| **[Architecture](./architecture.md)** | System design, components, data flow | All technical staff |
| **[Deployment](./deployment.md)** | Docker Compose & Kubernetes setup | DevOps/SRE |
| **[Monitoring](./monitoring.md)** | Observability, dashboards, alerts | SRE/Ops |
| **[Security](./security/)** | Access control, secrets, hardening | Security/SRE |
| **[Runbooks](./runbooks/)** | Operational procedures, incident response | All operators |
| **[Volcano Scheduler](./volcano-scheduler.md)** | Batch scheduler deployment and operations | Platform/SRE |

---

## 🎯 Getting Started

### For New Operators (First Time Setup)

**Follow this path:**

1. **[Architecture Overview](./architecture.md)** (30 min)
   - Understand the system design
   - Learn component responsibilities
   - Review data flow patterns

2. **[Local Deployment Setup](./deployment.md#quick-start-docker-compose)** (15 min)
   - Get docker-compose running locally
   - Verify all services boot successfully
   - Understand port mappings

3. **[Monitoring Setup](./monitoring.md)** (20 min)
   - Access Grafana dashboards
   - Configure alerts
   - Set up log aggregation

4. **[Security Configuration](./security/)** (45 min)
   - Review RBAC matrix
   - Set up secrets management (Vault)
   - Configure network policies

### For Kubernetes Deployment

**For production Kubernetes deployment:**

1. Read **[Deployment > Kubernetes Deployment](./deployment.md#kubernetes-deployment)** (full section)
2. Follow **[Deployment > Production Configuration](./deployment.md#production-configuration)** (HA, scaling, storage)
3. Review **[Runbooks > Incident Response](./runbooks/incident-response.md)** (troubleshooting)

### For Incident Response

**When issues occur:**

1. Check **[Monitoring](./monitoring.md)** to understand what's failing
2. Review **[Runbooks](./runbooks/)** for specific service procedures
3. Use troubleshooting steps in **[Deployment > Troubleshooting](./deployment.md#troubleshooting)**

---

## 📋 Complete File Structure

```
technical-manual/
├─ index.md                          # You are here
├─ architecture.md                   # System design & components
├─ deployment.md                     # Installation & configuration
├─ monitoring.md                     # Observability & dashboards
├─ security/
│  ├─ index.md                       # Security overview
│  ├─ secrets-policy.md              # Secrets management (Vault)
│  └─ rbac-matrix.md                 # Access control matrix
├─ volcano-scheduler.md              # Volcano scheduler integration guide
├─ runbooks/
│  ├─ index.md                       # Runbook overview
│  ├─ gateway-api.md                 # Gateway API procedures
│  ├─ orchestrator.md                # Orchestrator procedures
│  ├─ postgres-database.md           # Database management
│  ├─ incident-response.md           # Emergency procedures
│  ├─ scaling-procedures.md          # Scaling operations
│  └─ volcano-operations.md          # Volcano scheduler runbook
└─ backup-and-recovery.md            # Disaster recovery
```

---

## 🔑 Key Concepts

### Service Responsibilities

**Application Services** (user-facing APIs):
- **Gateway API** (10000): Ingress, authentication, rate limiting
- **Orchestrator** (10001): Multi-agent workflows, state management
- **Identity Service** (10002): Tenants, roles, JWT issuance

**Infrastructure Services** (supporting backend):
- **PostgreSQL**: Persistent state, Temporal metadata
- **Redis**: Caching, sessions, real-time data
- **Qdrant**: Vector search, semantic memory
- **Temporal**: Workflow engine, task queues
- **Kafka**: Event streaming, audit logs

**Observability Stack**:
- **Prometheus**: Metrics collection & storage
- **Grafana**: Metrics visualization & dashboards
- **Loki**: Log aggregation
- **Tempo**: Distributed tracing
- **OTEL Collector**: Trace/metric receiver

**Security & Secrets**:
- **Vault**: Secrets management, key rotation
- **OPA/Gatekeeper**: Policy enforcement
- **Istio**: mTLS, service mesh

---

## 📊 Standard Operating Procedures

### Daily Operations

```bash
# 1. Check service health (every morning)
curl http://localhost:10000/health          # Gateway
curl http://localhost:10001/ready           # Orchestrator
curl http://localhost:10002/health          # Identity

# 2. Monitor resource usage
docker stats --no-stream

# 3. Check logs for errors
docker-compose logs --tail=100 | grep -i error

# 4. Verify database connectivity
docker-compose exec app-postgres pg_isready

# 5. Monitor alerting
open http://localhost:10011  # Grafana
open http://localhost:10010  # Prometheus
```

### Weekly Maintenance

- ✅ Review backup status (`backup-and-recovery.md`)
- ✅ Check certificate expiry (Vault, TLS)
- ✅ Audit security policy compliance
- ✅ Review application logs for warnings
- ✅ Validate metrics collection is running

### Monthly Audit

- ✅ Security posture assessment
- ✅ Capacity planning review
- ✅ Disaster recovery drill
- ✅ Documentation updates
- ✅ Dependency vulnerability scanning

---

## 🚨 Emergency Procedures

### Service is Down

**Quick response:**

```bash
# 1. Check service status
docker-compose ps <service>
kubectl get pod -n soma-agent-hub

# 2. Check logs
docker-compose logs -f <service>
kubectl logs -f deployment/<service> -n soma-agent-hub

# 3. Restart service
docker-compose restart <service>
kubectl rollout restart deployment/<service> -n soma-agent-hub

# 4. If restart fails → See Runbooks
open docs/technical-manual/runbooks/<service>.md
```

### Database Connection Failures

**Quick response:**

```bash
# 1. Check PostgreSQL health
docker-compose exec app-postgres pg_isready

# 2. Check database size
docker-compose exec app-postgres psql -U somaagent -d somaagent -c \
  "SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database;"

# 3. Check active connections
docker-compose exec app-postgres psql -U somaagent -d somaagent -c \
  "SELECT datname, count(*) as connections FROM pg_stat_activity GROUP BY datname;"

# 4. Full troubleshooting → See Runbooks
open docs/technical-manual/runbooks/postgres-database.md
```

### Out of Memory

**Quick response:**

```bash
# 1. Check memory usage
docker stats --no-stream
df -h /var/lib/docker/

# 2. Identify heavy consumers
docker system df

# 3. Free up space
docker system prune -a  # Remove unused images/containers
docker volume prune     # Remove unused volumes

# 4. Increase Docker memory
# → Open Docker Desktop → Preferences → Resources
# → Increase Memory to 16+ GB
```

### Data Corruption / Inconsistency

**Recovery procedure:**

```bash
# 1. Stop all services
docker-compose down

# 2. Backup current volumes
docker run --rm -v somaagenthub-app-postgres-data:/data \
  -v $(pwd):/backup alpine tar czf /backup/backup-corrupted.tar.gz /data

# 3. Restore from backup (if available)
docker volume rm somaagenthub-app-postgres-data
docker run --rm -v somaagenthub-app-postgres-data:/data \
  -v /path/to/backup:/backup alpine tar xzf /backup/postgres-backup.tar.gz

# 4. Restart services
docker-compose up -d

# 5. Verify integrity
docker-compose exec app-postgres pg_dump -U somaagent --verbose | head -100
```

---

## 📞 Support & Escalation

### Getting Help

| Issue Type | First Steps | Escalation |
|-----------|------------|-----------|
| Service down | Check logs, restart, see runbooks | Page on-call engineer |
| Performance issue | Check metrics in Grafana, review runbooks | Contact SRE lead |
| Database problem | Run diagnostics, check runbooks | Contact database specialist |
| Security concern | Isolate service, disable user access, page security team | Activate incident response |

### Contacts

- **Tech Lead**: `@tech-lead` (architecture questions)
- **DevOps Lead**: `@devops-lead` (deployment, infrastructure)
- **On-Call SRE**: Check PagerDuty rotation
- **Security Team**: `@security-team` (security incidents)

### Slack Channels

- `#somagenthub-alerts` - System alerts & incidents
- `#somagenthub-dev` - Development & ops discussion
- `#somagenthub-general` - General announcements

---

## 🔗 Related Documentation

**For other audiences:**

- **[User Manual](../user-manual/)** - End-user features & workflows
- **[Development Manual](../development-manual/)** - Code contribution & architecture
- **[Onboarding Manual](../onboarding-manual/)** - Team member onboarding

---

## 📋 Operations Checklist

### Pre-Production Deployment

- [ ] Architecture reviewed by tech lead
- [ ] Security assessment completed
- [ ] Capacity planning verified
- [ ] Backup procedures tested
- [ ] Monitoring configured & verified
- [ ] Runbooks written & tested
- [ ] Incident response plan created
- [ ] Team trained on procedures

### Post-Deployment Verification

- [ ] All services healthy (15+ running)
- [ ] Metrics flowing to Prometheus
- [ ] Logs flowing to Loki
- [ ] Traces flowing to Tempo
- [ ] Vault unsealed & operational
- [ ] Backups running on schedule
- [ ] Alerts triggering correctly
- [ ] Documentation up-to-date

---

## 🎯 Common Tasks Reference

### View Service Logs

```bash
# Last 50 lines
docker-compose logs --tail=50 gateway-api

# Follow in real-time
docker-compose logs -f gateway-api

# Kubernetes
kubectl logs -f deployment/gateway-api -n soma-agent-hub
```

### Scale Services

```bash
# Docker Compose
docker-compose up -d --scale orchestrator=3

# Kubernetes
kubectl scale deployment gateway-api --replicas=5 -n soma-agent-hub
```

### Update Service Configuration

```bash
# Edit .env
nano .env

# Restart affected service
docker-compose restart gateway-api

# Or Kubernetes
kubectl set env deployment/gateway-api KEY=value -n soma-agent-hub
kubectl rollout restart deployment/gateway-api -n soma-agent-hub
```

### Database Backup

```bash
# PostgreSQL dump
docker-compose exec app-postgres pg_dump -U somaagent -d somaagent > backup.sql

# Restore
cat backup.sql | docker-compose exec -T app-postgres psql -U somaagent -d somaagent
```

---

## 📊 Performance Baselines

**Expected healthy state metrics:**

| Metric | Threshold | Alert Level |
|--------|-----------|-------------|
| **API p95 latency** | < 1000ms | 2000ms |
| **API error rate** | < 0.1% | > 1% |
| **Throughput** | > 100 req/sec | < 50 req/sec |
| **PostgreSQL connections** | < 150/200 | > 180/200 |
| **Redis memory** | < 400MB/512MB | > 480MB/512MB |
| **Disk usage** | < 70% | > 85% |
| **CPU usage** | < 70% | > 85% |
| **Memory usage** | < 70% | > 85% |

---

## ✅ You're Ready!

**Next steps:**

1. **Read [Architecture](./architecture.md)** to understand the system
2. **Follow [Deployment](./deployment.md)** to get services running
3. **Set up [Monitoring](./monitoring.md)** to observe the system
4. **Review [Runbooks](./runbooks/)** for operational procedures
5. **Read [Security](./security/)** for hardening procedures

---

**Questions? Check the [Onboarding Manual](../onboarding-manual/) or reach out in #somagenthub-dev!** 🚀
|---------|-------------|
| **[Operational Runbooks](runbooks/)** | Step-by-step procedures for common operations |
| **[Backup & Recovery](backup-and-recovery.md)** | Data protection and disaster recovery procedures |
| **[Security Configuration](security/)** | Security hardening, access controls, and compliance |

---

## 🏗️ Architecture Overview

SomaAgentHub is built as a **cloud-native, microservices architecture** designed for enterprise scale and reliability:

### Core Services (Production Deployment)
```
┌─────────────────────────────────────────────────────────┐
│                   SOMA AGENT HUB                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   │
│  │ Gateway API │   │Orchestrator │   │Identity Svc │   │
│  │  (Port 10000)│───│ (Port 10001) │───│ (Port 10002) │   │
│  └─────────────┘   └─────────────┘   └─────────────┘   │
│         │                 │                 │           │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   │
│  │ SLM Service │   │Memory Gateway│   │Policy Engine│   │
│  │ (Port 10005) │   │ (Port 10004) │   │ (Port 10003) │   │
│  └─────────────┘   └─────────────┘   └─────────────┘   │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                 INFRASTRUCTURE LAYER                    │
│                                                         │
│ ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│ │PostgreSQL│ │  Redis  │ │ Temporal│ │ Qdrant  │     │
│ │   DB    │ │ Cache   │ │Workflows│ │ Vector  │     │
│ └─────────┘  └─────────┘  └─────────┘  └─────────┘     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Key Architecture Principles

- **Microservices** - Independent, scalable service components
- **Event-Driven** - Asynchronous communication via Temporal and message queues
- **Cloud-Native** - Kubernetes-first design with 12-factor app principles
- **Observable** - Comprehensive metrics, logging, and tracing
- **Secure** - Multi-layer security with RBAC, TLS, and audit logging

---

## 🚀 Quick Start for Operators

### Production Deployment Checklist

```bash
# 1. Verify prerequisites
kubectl version --client
helm version
docker version

# 2. Clone repository and configure
git clone https://github.com/somatechlat/somaAgentHub.git
cd somaAgentHub
cp config/production.yaml.example config/production.yaml

# 3. Deploy infrastructure dependencies
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack

# 4. Deploy SomaAgentHub
helm install soma-agent-hub ./k8s/helm/soma-agent \
  --namespace soma-agent-hub \
  --create-namespace \
  --values config/production.yaml

# 5. Verify deployment
kubectl get pods -n soma-agent-hub
make k8s-smoke
```

### Essential Operations Commands

```bash
# Health monitoring
kubectl get pods -n soma-agent-hub -w
kubectl top nodes
kubectl top pods -n soma-agent-hub

# Log collection
kubectl logs -n soma-agent-hub deployment/gateway-api -f
kubectl logs -n soma-agent-hub deployment/orchestrator -f

# Service management
kubectl scale deployment gateway-api --replicas=3 -n soma-agent-hub
kubectl rollout restart deployment/orchestrator -n soma-agent-hub

# Resource monitoring
kubectl describe nodes
kubectl describe pods -n soma-agent-hub
```

---

## 📊 System Requirements

### Production Environment Specifications

#### Minimum Production Cluster
- **Nodes**: 3 worker nodes (high availability)
- **CPU**: 8 cores total (2.5+ cores per node) 
- **RAM**: 24GB total (8GB+ per node)
- **Storage**: 100GB persistent storage (SSD recommended)
- **Network**: 1Gbps+ bandwidth, low latency between nodes

#### Recommended Production Cluster  
- **Nodes**: 5+ worker nodes (fault tolerance)
- **CPU**: 16+ cores total (4+ cores per node)
- **RAM**: 64GB+ total (16GB+ per node)
- **Storage**: 500GB+ persistent storage (NVMe SSD)
- **Network**: 10Gbps+ bandwidth, multi-AZ deployment

#### Scaling Guidelines
| Concurrent Users | Workflows/Hour | CPU Cores | RAM | Storage |
|------------------|---------------|-----------|-----|---------|
| 1-50 | <100 | 8 | 24GB | 100GB |
| 50-200 | 100-500 | 16 | 64GB | 250GB |
| 200-1000 | 500-2000 | 32 | 128GB | 500GB |
| 1000+ | 2000+ | 64+ | 256GB+ | 1TB+ |

### Supported Platforms

#### Kubernetes Distributions
- **Amazon EKS** - 1.24+ (recommended: 1.27+)
- **Google GKE** - 1.24+ (recommended: 1.27+)  
- **Azure AKS** - 1.24+ (recommended: 1.27+)
- **Red Hat OpenShift** - 4.10+ (Kubernetes 1.23+)
- **VMware Tanzu** - 1.24+
- **On-Premises Kubernetes** - 1.24+ (kubeadm, RKE, etc.)

#### Operating Systems (Node OS)
- **Ubuntu** 20.04+ LTS
- **CentOS/RHEL** 8+
- **Amazon Linux** 2
- **Container-Optimized OS** (Google)
- **Bottlerocket** (Amazon)

---

## 🔗 Related Documentation

### For Different Audiences
- **[User Manual](../user-manual/)** - End-user guides and API usage
- **[Development Manual](../development-manual/)** - Code contribution and customization
- **[Onboarding Manual](../onboarding-manual/)** - Quick team member orientation

### External Dependencies Documentation
- **[Kubernetes Documentation](https://kubernetes.io/docs/)**
- **[Helm Documentation](https://helm.sh/docs/)**
- **[Temporal Documentation](https://docs.temporal.io/)**
- **[Prometheus Monitoring](https://prometheus.io/docs/)**

---

## 🛠️ Operations Workflow

### Daily Operations
1. **Health Monitoring** - Check dashboards and alerts
2. **Performance Review** - Monitor resource usage and scaling needs
3. **Log Analysis** - Review error logs and audit trails
4. **Backup Verification** - Ensure backups are running successfully

### Weekly Operations
1. **Security Updates** - Apply security patches and updates
2. **Capacity Planning** - Review growth trends and resource needs
3. **Performance Optimization** - Tune configurations based on usage patterns
4. **Disaster Recovery Testing** - Test backup and recovery procedures

### Monthly Operations
1. **Infrastructure Review** - Assess overall system health and optimization opportunities
2. **Security Audit** - Review access controls, certificates, and compliance
3. **Documentation Updates** - Update runbooks and procedures based on operational learnings
4. **Cost Optimization** - Review resource usage and optimize for cost efficiency

---

## 📞 Support Escalation

### Issue Severity Levels

| Severity | Description | Response Time | Escalation |
|----------|-------------|---------------|------------|
| **P0 - Critical** | System down, data loss | 15 minutes | Immediate on-call |
| **P1 - High** | Major feature failure | 1 hour | Senior SRE |
| **P2 - Medium** | Minor feature issues | 4 hours | Regular support |
| **P3 - Low** | Documentation, enhancement | 24 hours | Standard queue |

### Contact Information
- **On-Call Engineer**: [PagerDuty/AlertManager integration]
- **SRE Team**: sre@somatech.lat
- **Platform Team**: platform@somatech.lat
- **Security Team**: security@somatech.lat

---

## 🎯 Next Steps

Ready to deploy and operate SomaAgentHub? Follow this path:

1. **[Read Architecture Guide](architecture.md)** - Understand the system design
2. **[Follow Deployment Guide](deployment.md)** - Set up production environment
3. **[Configure Monitoring](monitoring.md)** - Set up observability and alerting
4. **[Review Runbooks](runbooks/)** - Familiarize yourself with operational procedures
5. **[Configure Security](security/)** - Implement security hardening

---

**SomaAgentHub Technical Manual: Your complete guide to enterprise-grade agent orchestration operations.**
