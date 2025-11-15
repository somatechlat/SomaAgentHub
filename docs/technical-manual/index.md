# Technical Manual

![Version](https://img.shields.io/badge/version-1.0.0-blue)

## Overview

This manual provides comprehensive technical documentation for SomaAgentHub deployment, architecture, monitoring, and operations.

## Contents

- [Architecture](architecture.md) - System design and component interactions
- [Deployment](deployment.md) - Production deployment guide
- [Monitoring](monitoring.md) - Observability and alerting setup
- [Runbooks](runbooks/) - Operational procedures and troubleshooting
- [Security](security/) - Security policies and RBAC configuration
- [Backup & Recovery](backup-and-recovery.md) - Data protection procedures

## System Architecture

SomaAgentHub is built as a microservices architecture on Kubernetes with the following core components:

### Core Services
| Service | Port | Purpose | Dependencies |
|---------|------|---------|--------------|
| Gateway API | 10000 | Public ingress, wizard flows | Redis, Orchestrator, Identity |
| Orchestrator | 10001 | Workflow coordination | Temporal, Policy, Identity |
| Identity Service | 10002 | Authentication, token management | PostgreSQL |
| Memory Gateway | 10021 | Vector/KV storage | Qdrant, Redis |
| Policy Engine | 10020 | Rule enforcement | OPA, Constitution Service |

### Supporting Services
| Service | Purpose | Technology |
|---------|---------|------------|
| Analytics Service | Metrics collection | ClickHouse, Kafka |
| Billing Service | Usage tracking | PostgreSQL |
| Tool Service | External integrations | FastAPI, Adapters |
| Notification Service | Alerts and messaging | SMTP, Webhooks |

### Infrastructure Components
| Component | Purpose | Configuration |
|-----------|---------|---------------|
| Temporal | Workflow orchestration | `infra/temporal/` |
| Redis | Session state, caching | Helm chart values |
| PostgreSQL | Transactional data | External or in-cluster |
| Qdrant | Vector database | Memory Gateway integration |
| Prometheus | Metrics collection | `k8s/monitoring/` |
| Prometheus | Metrics Collection | Time-series data storage and querying |

## Deployment Patterns

### Local Development
```bash
make start-cluster  # Kind + Helm deployment
make dev-up        # Docker Compose dependencies
```

### Production Kubernetes
```bash
helm upgrade --install soma-agent-hub ./k8s/helm/soma-agent \
  --namespace soma-agent-hub \
  --values values-production.yaml
```

### Multi-Environment
- **Development**: Kind clusters with local images
- **Staging**: Kubernetes with external databases
- **Production**: Multi-node clusters with HA configuration

## Network Architecture

```
Internet → Ingress Controller → Gateway API (10000)
                                     ↓
                              Orchestrator (10001) ← → Temporal
                                     ↓
                    ┌────────────────┼────────────────┐
                    ↓                ↓                ↓
            Identity Service    Policy Engine    Memory Gateway
               (10002)           (10020)          (10021)
                    ↓                ↓                ↓
               PostgreSQL           OPA            Qdrant
```

## Data Flow

### Request Processing
1. **Ingress**: External requests hit Gateway API
2. **Authentication**: Identity Service validates tokens
3. **Policy Check**: Policy Engine evaluates permissions
4. **Orchestration**: Orchestrator starts Temporal workflows
5. **Execution**: Agents execute tasks with tool integrations
6. **Memory**: Context stored in Memory Gateway
7. **Analytics**: Events sent to Analytics Service

### Event Streaming
```
Agent Actions → Kafka → Analytics Service → ClickHouse
                   ↓
              Flink Processing → Real-time Metrics
                   ↓
              Redis Streams → WebSocket Updates
```

## Configuration Management

### Helm Values Structure
```yaml
global:
  imageRegistry: "ghcr.io/somatechlat"
  imageTag: "v1.0.0"
  namespace: "soma-agent-hub"

services:
  gateway:
    enabled: true
    replicas: 3
    resources:
      requests:
        cpu: 500m
        memory: 512Mi
```

### Environment Variables
- **Development**: `.env` files per service
- **Kubernetes**: ConfigMaps and Secrets
- **Helm**: Values files with environment overrides

### Service Discovery
- **Internal**: Kubernetes DNS (`service-name.namespace.svc.cluster.local`)
- **External**: Ingress controllers with TLS termination
- **Health Checks**: `/health` and `/ready` endpoints

## Observability Stack

### Metrics (Prometheus)
- Service-level metrics from `/metrics` endpoints
- Custom business metrics via pushgateway
- Resource utilization from kubelet
- Alert rules for SLA monitoring

### Logging (Loki)
- Structured JSON logs from all services
- Log aggregation via promtail
- Correlation with trace IDs
- Log-based alerting

### Tracing (OpenTelemetry)
- Distributed traces across service boundaries
- Temporal workflow tracing
- Database query tracing
- Performance bottleneck identification

### Dashboards (Prometheus)
- Service overview dashboards
- Infrastructure monitoring
- Business metrics visualization
- Alert management interface

## Security Architecture

### Authentication & Authorization
- **Service-to-Service**: Kubernetes ServiceAccounts
- **External Access**: JWT tokens from Identity Service
- **Admin Access**: RBAC with least privilege
- **Optional**: SPIFFE/SPIRE for zero-trust

### Network Security
- **Network Policies**: Restrict pod-to-pod communication
- **TLS**: End-to-end encryption for external traffic
- **Secrets Management**: Kubernetes Secrets or Vault
- **Image Security**: Trivy scanning in CI/CD

### Policy Enforcement
- **OPA Integration**: Policy-as-code with Rego
- **Constitution Service**: Governance framework
- **Audit Logging**: All policy decisions logged
- **Compliance**: SOC2, GDPR considerations

## Operational Procedures

### Deployment
1. **Pre-deployment**: Run smoke tests, validate configuration
2. **Rolling Update**: Helm upgrade with zero downtime
3. **Post-deployment**: Health checks, smoke tests
4. **Rollback**: Automated rollback on failure

### Monitoring
1. **Health Monitoring**: Continuous health endpoint checks
2. **Performance**: SLA monitoring with alerting
3. **Capacity**: Resource utilization tracking
4. **Business Metrics**: Agent success rates, workflow completion

### Incident Response
1. **Detection**: Automated alerting via Prometheus
2. **Triage**: Runbook-driven response procedures
3. **Resolution**: Service restart, scaling, or rollback
4. **Post-mortem**: Root cause analysis and prevention

## Scaling Considerations

### Horizontal Scaling
- **Stateless Services**: Gateway, Orchestrator, Policy Engine
- **Database Scaling**: Read replicas, connection pooling
- **Cache Scaling**: Redis clustering
- **Queue Scaling**: Kafka partition scaling

### Vertical Scaling
- **Memory**: Increase for agent context storage
- **CPU**: Scale for compute-intensive workflows
- **Storage**: Expand for vector database growth
- **Network**: Bandwidth for real-time propagation

### Performance Optimization
- **Connection Pooling**: Database and Redis connections
- **Caching**: Aggressive caching of policy decisions
- **Batch Processing**: Bulk operations where possible
- **Async Processing**: Non-blocking I/O throughout

## Disaster Recovery

### Backup Strategy
- **Database Backups**: Automated daily snapshots
- **Configuration Backup**: Helm values and secrets
- **Code Backup**: Git repository with tags
- **Infrastructure**: Terraform state backup

### Recovery Procedures
- **Service Recovery**: Pod restart and health validation
- **Data Recovery**: Point-in-time database restore
- **Full Recovery**: Complete cluster rebuild
- **Testing**: Regular DR drills and validation

## Compliance & Governance

### Documentation Standards
- **ISO/IEC 26514**: User documentation requirements
- **ISO/IEC 26515**: Online documentation delivery
- **ISO/IEC 26512**: Documentation processes
- **Change Control**: Version-controlled documentation

### Audit Requirements
- **Access Logging**: All administrative actions
- **Policy Decisions**: Complete audit trail
- **Data Handling**: GDPR compliance measures
- **Security Events**: Comprehensive security logging