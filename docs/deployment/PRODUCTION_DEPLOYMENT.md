# SomaAgent Production Deployment Guide

**Real Production Deployment - No Mocks, No Bypasses**

This guide covers deploying SomaAgent to a real Kubernetes cluster with full observability, security, and production-grade infrastructure.

## Prerequisites

### Required Tools
```bash
# Kubernetes CLI
kubectl version --client

# Helm package manager
helm version

# Docker (for building images)
docker --version

# Optional: k9s for cluster monitoring
k9s version
```

### Cluster Requirements
- **Kubernetes**: v1.24+
- **CPU**: 16+ cores
- **Memory**: 32+ GB RAM
- **Storage**: 200+ GB
- **Load Balancer**: Cloud provider or MetalLB
- **Ingress**: nginx-ingress or Traefik

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                        │
│                   (gateway-api:8080)                    │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────┼────────────────────────────────────────┐
│  SomaAgent     │  Namespace                             │
│                ▼                                         │
│  ┌───────────────────┐      ┌──────────────────┐       │
│  │   Gateway API     │──────│  Identity Svc    │       │
│  │   (Port 8080)     │      │  (Port 8002)     │       │
│  └─────────┬─────────┘      └──────────────────┘       │
│            │                                             │
│  ┌─────────┼───────────────────────────────────┐       │
│  │         ▼                                    │       │
│  │  ┌──────────────┐      ┌───────────────┐   │       │
│  │  │ Orchestrator │──────│ Policy Engine │   │       │
│  │  │ (Port 8000)  │      │ (Port 8001)   │   │       │
│  │  └──────┬───────┘      └───────┬───────┘   │       │
│  │         │                       │           │       │
│  │         ▼                       ▼           │       │
│  │  ┌──────────────┐      ┌───────────────┐   │       │
│  │  │  SLM Service │      │     Redis     │   │       │
│  │  │ (Port 8003)  │      │  (Cache)      │   │       │
│  │  └──────────────┘      └───────────────┘   │       │
│  │                                             │       │
│  │  ┌──────────────┐      ┌───────────────┐   │       │
│  │  │  Analytics   │──────│  ClickHouse   │   │       │
│  │  │ (Port 8005)  │      │  (Database)   │   │       │
│  │  └──────────────┘      └───────────────┘   │       │
│  │                                             │       │
│  │  ┌──────────────────────────────────────┐  │       │
│  │  │         Temporal Workflows            │  │       │
│  │  │      (KAMACHIQ Orchestration)         │  │       │
│  │  └──────────────────────────────────────┘  │       │
│  └─────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Observability Namespace                                │
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │ Prometheus │  │  Grafana   │  │   Alerts   │        │
│  │ (Metrics)  │  │ (Dashboards)│  │  (PagerDuty)│       │
│  └────────────┘  └────────────┘  └────────────┘        │
│                                                          │
│  11 ServiceMonitors → Real-time metrics collection      │
│  4 Dashboards → System, Policy, SLM, KAMACHIQ          │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Build Docker Images

```bash
# Build all service images
cd services

# Policy Engine
docker build -t somaagent/policy-engine:latest policy-engine/

# Identity Service
docker build -t somaagent/identity-service:latest identity-service/

# SLM Service
docker build -t somaagent/slm-service:latest slm-service/

# Orchestrator
docker build -t somaagent/orchestrator:latest orchestrator/

# Analytics Service
docker build -t somaagent/analytics-service:latest analytics-service/

# Gateway API
docker build -t somaagent/gateway-api:latest gateway-api/

# Push to registry (replace with your registry)
docker tag somaagent/policy-engine:latest your-registry.com/somaagent/policy-engine:latest
docker push your-registry.com/somaagent/policy-engine:latest
# ... repeat for all services
```

### 2. Configure Secrets

**⚠️ CRITICAL: Change all default passwords in production!**

```bash
# Create real secrets file (DO NOT commit!)
cat > secrets.env << EOF
IDENTITY_DB_URL=postgresql://somaagent:$(openssl rand -hex 32)@postgres:5432/identity
JWT_SECRET=$(openssl rand -hex 64)
CLICKHOUSE_USER=analytics_ingest
CLICKHOUSE_PASSWORD=$(openssl rand -hex 32)
EOF

# Apply secrets
kubectl create namespace somaagent
kubectl create secret generic somaagent-secrets \
  --namespace=somaagent \
  --from-env-file=secrets.env

# Delete local copy
rm secrets.env
```

### 3. Deploy with Script

```bash
# Run automated deployment
./scripts/deploy.sh

# Monitor progress
watch kubectl get pods -n somaagent
```

### 4. Manual Deployment (Alternative)

```bash
# Create namespaces
kubectl create namespace somaagent
kubectl create namespace observability

# Deploy observability stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace observability \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false

# Deploy infrastructure
kubectl apply -f infra/k8s/redis.yaml
kubectl apply -f infra/k8s/clickhouse.yaml

# Initialize ClickHouse schema
kubectl exec -n somaagent clickhouse-0 -- \
  clickhouse-client --multiquery < infra/clickhouse/schema.sql

# Deploy Temporal
helm repo add temporalio https://go.temporal.io/helm-charts
helm install temporal temporalio/temporal --namespace somaagent

# Deploy services
kubectl apply -f infra/k8s/policy-engine.yaml
kubectl apply -f infra/k8s/identity-service.yaml
kubectl apply -f infra/k8s/slm-service.yaml
kubectl apply -f infra/k8s/orchestrator.yaml
kubectl apply -f infra/k8s/analytics-service.yaml
kubectl apply -f infra/k8s/gateway-api.yaml

# Deploy ServiceMonitors
kubectl apply -f infra/k8s/servicemonitors/
```

## Verification

### Check Pod Status
```bash
# All pods should be Running
kubectl get pods -n somaagent

# Expected output:
# NAME                                READY   STATUS    RESTARTS
# gateway-api-xxx                     1/1     Running   0
# orchestrator-xxx                    1/1     Running   0
# policy-engine-xxx                   1/1     Running   0
# identity-service-xxx                1/1     Running   0
# slm-service-xxx                     1/1     Running   0
# analytics-service-xxx               1/1     Running   0
# redis-xxx                           1/1     Running   0
# clickhouse-0                        1/1     Running   0
# temporal-xxx                        1/1     Running   0
```

### Check Services
```bash
# Verify services are exposed
kubectl get svc -n somaagent

# Test gateway API
GATEWAY_IP=$(kubectl get svc gateway-api -n somaagent -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$GATEWAY_IP:8080/health

# Expected: {"status": "healthy"}
```

### Check Metrics
```bash
# Port-forward Prometheus
kubectl port-forward -n observability svc/prometheus-prometheus 9090:9090

# Open browser: http://localhost:9090
# Query: up{namespace="somaagent"}
# All targets should be UP

# Port-forward Grafana
kubectl port-forward -n observability svc/prometheus-grafana 3000:80

# Open browser: http://localhost:3000 (admin/admin)
# Navigate to SomaAgent dashboards
```

### Test Real Execution

```bash
# Run KAMACHIQ workflow
kubectl exec -n somaagent deployment/orchestrator -- \
  python temporal_worker.py

# In another terminal, trigger workflow
kubectl exec -n somaagent deployment/orchestrator -- python -c "
import asyncio
from temporalio.client import Client
from workflows import KAMACHIQProjectWorkflow

async def test():
    client = await Client.connect('temporal.somaagent:7233')
    result = await client.execute_workflow(
        KAMACHIQProjectWorkflow.run,
        args=['Create a Python hello world script', 'test_user', 'test_001'],
        id='test-workflow-001',
        task_queue='kamachiq-tasks',
    )
    print(f'Result: {result}')

asyncio.run(test())
"
```

## Monitoring

### Real-time Logs
```bash
# All services
stern -n somaagent .

# Specific service
kubectl logs -f -l app=orchestrator -n somaagent

# Temporal worker
kubectl logs -f -l app=orchestrator -n somaagent -c orchestrator | grep temporal
```

### Metrics Queries

```promql
# Request rate per service
rate(http_requests_total{namespace="somaagent"}[5m])

# Error rate
rate(http_requests_total{namespace="somaagent",status=~"5.."}[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Policy blocking rate
rate(policy_decisions_total{allowed="false"}[5m])

# KAMACHIQ success rate
rate(workflow_executions_total{status="completed"}[1h])
/ rate(workflow_executions_total[1h])
```

### Alerts
```bash
# Check active alerts
kubectl get prometheusrules -n observability

# View firing alerts
curl http://localhost:9090/api/v1/alerts | jq
```

## Production Checklist

### Security
- [ ] Changed all default passwords
- [ ] Configured TLS/SSL certificates
- [ ] Enabled network policies
- [ ] Configured RBAC policies
- [ ] Enabled pod security policies
- [ ] Configured secret encryption at rest
- [ ] Set up cert-manager for auto-renewal

### Reliability
- [ ] Configured resource requests/limits
- [ ] Set up horizontal pod autoscaling
- [ ] Configured pod disruption budgets
- [ ] Set up multi-zone deployment
- [ ] Configured health checks
- [ ] Set up liveness/readiness probes

### Observability
- [ ] All ServiceMonitors deployed
- [ ] Grafana dashboards configured
- [ ] Alert rules configured
- [ ] PagerDuty/Slack integration
- [ ] Log aggregation (ELK/Loki)
- [ ] Distributed tracing

### Data
- [ ] ClickHouse backups configured
- [ ] Redis persistence enabled
- [ ] Database backup policies
- [ ] Disaster recovery plan
- [ ] Data retention policies

### Operations
- [ ] CI/CD pipelines configured
- [ ] Rollback procedures documented
- [ ] Incident response playbook
- [ ] On-call rotation configured
- [ ] Runbooks for common issues

## Troubleshooting

### Pods Not Starting
```bash
# Check pod events
kubectl describe pod <pod-name> -n somaagent

# Check logs
kubectl logs <pod-name> -n somaagent --previous

# Common issues:
# - Image pull errors → Check registry credentials
# - OOMKilled → Increase memory limits
# - CrashLoopBackOff → Check application logs
```

### Services Not Reachable
```bash
# Check service endpoints
kubectl get endpoints -n somaagent

# Check NetworkPolicies
kubectl get networkpolicies -n somaagent

# Test internal connectivity
kubectl run -it --rm debug --image=curlimages/curl -n somaagent -- \
  curl http://orchestrator:8000/health
```

### High Latency
```bash
# Check resource usage
kubectl top pods -n somaagent

# Check HPA status
kubectl get hpa -n somaagent

# Scale manually if needed
kubectl scale deployment orchestrator -n somaagent --replicas=5
```

### ClickHouse Issues
```bash
# Check ClickHouse logs
kubectl logs -n somaagent clickhouse-0

# Connect to ClickHouse
kubectl exec -it -n somaagent clickhouse-0 -- clickhouse-client

# Check table sizes
SELECT table, formatReadableSize(sum(bytes)) AS size
FROM system.parts
WHERE database = 'somaagent'
GROUP BY table;
```

## Performance Tuning

### Resource Optimization
```yaml
# Adjust based on load
resources:
  requests:
    cpu: "2000m"      # Minimum guaranteed
    memory: "4Gi"
  limits:
    cpu: "8000m"      # Maximum allowed
    memory: "16Gi"
```

### Autoscaling
```bash
# Enable HPA
kubectl autoscale deployment orchestrator \
  --namespace somaagent \
  --cpu-percent=70 \
  --min=2 \
  --max=10
```

### Database Tuning
```sql
-- ClickHouse optimization
OPTIMIZE TABLE capsule_executions FINAL;
OPTIMIZE TABLE conversations FINAL;
OPTIMIZE TABLE policy_decisions FINAL;
```

## Backup & Recovery

### ClickHouse Backup
```bash
# Create backup
kubectl exec -n somaagent clickhouse-0 -- \
  clickhouse-client --query="BACKUP DATABASE somaagent TO Disk('backups', 'backup-$(date +%Y%m%d).zip')"

# Restore from backup
kubectl exec -n somaagent clickhouse-0 -- \
  clickhouse-client --query="RESTORE DATABASE somaagent FROM Disk('backups', 'backup-20241018.zip')"
```

### Redis Backup
```bash
# Trigger RDB snapshot
kubectl exec -n somaagent redis-0 -- redis-cli BGSAVE

# Copy snapshot
kubectl cp somaagent/redis-0:/data/dump.rdb ./redis-backup.rdb
```

## Next Steps

1. **Configure DNS**: Set up proper domain names
2. **Enable HTTPS**: Configure ingress with TLS
3. **Set Up Backups**: Automate backup procedures
4. **Configure Alerting**: Set up PagerDuty/Slack
5. **Load Testing**: Run performance tests
6. **Documentation**: Update runbooks

## Support

- **Issues**: Check logs and metrics first
- **Runbooks**: See `/docs/runbooks/`
- **Architecture**: See `/docs/SomaGent_Architecture.md`
- **Security**: See `/docs/SomaGent_Security.md`
