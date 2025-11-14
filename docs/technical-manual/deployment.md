# Deployment Guide

![Version](https://img.shields.io/badge/version-1.0.0-blue)

## Overview

This guide covers production deployment of SomaAgentHub on Kubernetes clusters with high availability, security, and observability configurations.

## Prerequisites

### Infrastructure Requirements
- **Kubernetes**: 1.24+ with RBAC enabled
- **Helm**: 3.8+ for package management
- **Storage**: Persistent volumes for databases
- **Networking**: Ingress controller (nginx, traefik, etc.)
- **Monitoring**: Prometheus operator (optional but recommended)

### Resource Requirements
| Component | CPU | Memory | Storage | Replicas |
|-----------|-----|--------|---------|----------|
| Gateway API | 500m | 512Mi | - | 3+ |
| Orchestrator | 1000m | 1Gi | - | 2+ |
| Identity Service | 500m | 512Mi | - | 2+ |
| Memory Gateway | 500m | 1Gi | - | 2+ |
| Policy Engine | 300m | 256Mi | - | 2+ |
| Redis | 500m | 1Gi | 10Gi | 1-3 |
| PostgreSQL | 1000m | 2Gi | 50Gi | 1-3 |
| Qdrant | 1000m | 2Gi | 100Gi | 1-3 |

## Deployment Methods

### Method 1: Helm Chart (Recommended)

#### 1. Prepare Environment
```bash
# Create namespace
kubectl create namespace soma-agent-hub

# Add any required secrets
kubectl create secret generic soma-secrets \
  --from-literal=jwt-secret="your-jwt-secret" \
  --from-literal=redis-password="your-redis-password" \
  --namespace soma-agent-hub
```

#### 2. Configure Values
Create `values-production.yaml`:
```yaml
global:
  imageRegistry: "your-registry.com"
  imageTag: "v1.0.0"
  namespace: "soma-agent-hub"
  environment: "production"

services:
  gateway:
    enabled: true
    replicas: 3
    resources:
      requests:
        cpu: 500m
        memory: 512Mi
      limits:
        cpu: 1000m
        memory: 1Gi
    ingress:
      enabled: true
      host: "api.somaagent.com"
      tls:
        enabled: true
        secretName: "soma-tls-cert"

  orchestrator:
    enabled: true
    replicas: 2
    resources:
      requests:
        cpu: 1000m
        memory: 1Gi
      limits:
        cpu: 2000m
        memory: 2Gi

  identityService:
    enabled: true
    replicas: 2
    database:
      host: "postgres.example.com"
      port: 5432
      name: "soma_identity"
      existingSecret: "postgres-credentials"

  memoryGateway:
    enabled: true
    replicas: 2
    qdrant:
      persistence:
        enabled: true
        size: 100Gi
        storageClass: "fast-ssd"

  policyEngine:
    enabled: true
    replicas: 2

external:
  redis:
    enabled: true
    host: "redis.example.com"
    port: 6379
    auth:
      enabled: true
      existingSecret: "redis-credentials"

  temporal:
    enabled: true
    host: "temporal.example.com"
    port: 7233
    namespace: "default"

monitoring:
  prometheus:
    enabled: true
    serviceMonitor: true
  grafana:
    enabled: true
    dashboards: true
```

#### 3. Deploy with Helm
```bash
# Install/upgrade the release
helm upgrade --install soma-agent-hub ./k8s/helm/soma-agent \
  --namespace soma-agent-hub \
  --values values-production.yaml \
  --timeout 10m \
  --wait

# Verify deployment
kubectl get pods -n soma-agent-hub
kubectl get svc -n soma-agent-hub
```

### Method 2: Kustomize

#### 1. Prepare Kustomization
Create `k8s/overlays/production/kustomization.yaml`:
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: soma-agent-hub

resources:
- ../../base

patchesStrategicMerge:
- gateway-production.yaml
- orchestrator-production.yaml

configMapGenerator:
- name: soma-config
  literals:
  - ENVIRONMENT=production
  - LOG_LEVEL=INFO

secretGenerator:
- name: soma-secrets
  literals:
  - JWT_SECRET=your-jwt-secret
  - REDIS_PASSWORD=your-redis-password

images:
- name: somaagent/gateway-api
  newTag: v1.0.0
- name: somaagent/orchestrator
  newTag: v1.0.0
```

#### 2. Deploy with Kustomize
```bash
kubectl apply -k k8s/overlays/production
```

## High Availability Configuration

### Database High Availability

#### PostgreSQL HA
```yaml
# Using PostgreSQL operator or external managed service
postgresql:
  enabled: false
  
external:
  postgresql:
    host: "postgres-primary.example.com"
    replicaHosts:
      - "postgres-replica-1.example.com"
      - "postgres-replica-2.example.com"
    port: 5432
    database: "somaagent"
    auth:
      existingSecret: "postgres-ha-credentials"
```

#### Redis HA
```yaml
redis:
  enabled: false

external:
  redis:
    mode: "sentinel"
    sentinels:
      - host: "redis-sentinel-1.example.com"
        port: 26379
      - host: "redis-sentinel-2.example.com"
        port: 26379
      - host: "redis-sentinel-3.example.com"
        port: 26379
    masterName: "soma-redis"
```

#### Qdrant Clustering
```yaml
qdrant:
  cluster:
    enabled: true
    replicas: 3
    persistence:
      enabled: true
      size: 100Gi
      storageClass: "fast-ssd"
  resources:
    requests:
      cpu: 1000m
      memory: 2Gi
    limits:
      cpu: 2000m
      memory: 4Gi
```

### Service High Availability

#### Pod Disruption Budgets
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: gateway-api-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: gateway-api
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: orchestrator-pdb
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: orchestrator
```

#### Anti-Affinity Rules
```yaml
spec:
  template:
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - gateway-api
              topologyKey: kubernetes.io/hostname
```

## Security Configuration

### Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: soma-network-policy
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/part-of: soma-agent-hub
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
  - from:
    - podSelector:
        matchLabels:
          app.kubernetes.io/part-of: soma-agent-hub
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
  - to:
    - podSelector:
        matchLabels:
          app.kubernetes.io/part-of: soma-agent-hub
```

### RBAC Configuration
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: soma-orchestrator
  namespace: soma-agent-hub
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: soma-orchestrator-role
rules:
- apiGroups: [""]
  resources: ["pods", "configmaps", "secrets"]
  verbs: ["get", "list", "create", "update", "patch"]
- apiGroups: ["batch"]
  resources: ["jobs"]
  verbs: ["create", "get", "list", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: soma-orchestrator-binding
subjects:
- kind: ServiceAccount
  name: soma-orchestrator
roleRef:
  kind: Role
  name: soma-orchestrator-role
  apiGroup: rbac.authorization.k8s.io
```

### TLS Configuration
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: soma-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.somaagent.com
    secretName: soma-tls-cert
  rules:
  - host: api.somaagent.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: gateway-api
            port:
              number: 8000
```

## Monitoring & Observability

### Prometheus Configuration
```yaml
monitoring:
  prometheus:
    enabled: true
    serviceMonitor:
      enabled: true
      interval: 30s
      scrapeTimeout: 10s
    rules:
      enabled: true
      groups:
      - name: soma-agent-hub
        rules:
        - alert: SomaServiceDown
          expr: up{job=~"soma-.*"} == 0
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "SomaAgentHub service is down"
```

### Grafana Dashboards
```yaml
grafana:
  enabled: true
  dashboards:
    enabled: true
    configMaps:
    - soma-dashboards
  datasources:
    prometheus:
      url: http://prometheus:9090
```

## Backup & Recovery

### Database Backups
```bash
# PostgreSQL backup
kubectl create job postgres-backup-$(date +%Y%m%d) \
  --image=postgres:15 \
  -- pg_dump -h postgres.example.com -U soma_user soma_db > backup.sql

# Redis backup
kubectl exec redis-0 -- redis-cli BGSAVE
kubectl cp redis-0:/data/dump.rdb ./redis-backup-$(date +%Y%m%d).rdb

# Qdrant backup
kubectl exec qdrant-0 -- tar -czf /tmp/qdrant-backup.tar.gz /qdrant/storage
kubectl cp qdrant-0:/tmp/qdrant-backup.tar.gz ./qdrant-backup-$(date +%Y%m%d).tar.gz
```

### Configuration Backup
```bash
# Backup Helm values and secrets
helm get values soma-agent-hub -n soma-agent-hub > values-backup.yaml
kubectl get secrets -n soma-agent-hub -o yaml > secrets-backup.yaml
```

## Scaling Guidelines

### Horizontal Scaling
```bash
# Scale based on load
kubectl scale deployment gateway-api --replicas=5 -n soma-agent-hub
kubectl scale deployment orchestrator --replicas=3 -n soma-agent-hub

# Auto-scaling with HPA
kubectl autoscale deployment gateway-api \
  --cpu-percent=70 \
  --min=3 \
  --max=10 \
  -n soma-agent-hub
```

### Vertical Scaling
```bash
# Increase resource limits
kubectl patch deployment gateway-api -n soma-agent-hub -p '
{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "gateway-api",
          "resources": {
            "requests": {"cpu": "1000m", "memory": "1Gi"},
            "limits": {"cpu": "2000m", "memory": "2Gi"}
          }
        }]
      }
    }
  }
}'
```

## Troubleshooting

### Common Deployment Issues

#### Image Pull Errors
```bash
# Check image availability
docker pull your-registry.com/somaagent/gateway-api:v1.0.0

# Verify registry credentials
kubectl get secret regcred -n soma-agent-hub -o yaml
```

#### Resource Constraints
```bash
# Check node resources
kubectl describe nodes
kubectl top nodes

# Check resource quotas
kubectl describe resourcequota -n soma-agent-hub
```

#### Network Connectivity
```bash
# Test service connectivity
kubectl exec -it gateway-api-xxx -n soma-agent-hub -- \
  curl http://orchestrator:8000/health

# Check DNS resolution
kubectl exec -it gateway-api-xxx -n soma-agent-hub -- \
  nslookup orchestrator.soma-agent-hub.svc.cluster.local
```

### Health Checks
```bash
# Verify all services are healthy
kubectl get pods -n soma-agent-hub
kubectl get svc -n soma-agent-hub

# Run smoke tests
make k8s-smoke

# Check ingress
curl -k https://api.somaagent.com/healthz
```

## Maintenance

### Rolling Updates
```bash
# Update image tags
helm upgrade soma-agent-hub ./k8s/helm/soma-agent \
  --namespace soma-agent-hub \
  --set global.imageTag=v1.1.0 \
  --reuse-values

# Monitor rollout
kubectl rollout status deployment/gateway-api -n soma-agent-hub
```

### Certificate Renewal
```bash
# Check certificate expiry
kubectl describe certificate soma-tls-cert -n soma-agent-hub

# Force renewal if needed
kubectl delete certificate soma-tls-cert -n soma-agent-hub
kubectl apply -f ingress.yaml
```

### Database Maintenance
```bash
# PostgreSQL maintenance
kubectl exec postgres-0 -- psql -c "VACUUM ANALYZE;"

# Redis maintenance
kubectl exec redis-0 -- redis-cli BGREWRITEAOF

# Qdrant optimization
kubectl exec qdrant-0 -- curl -X POST http://localhost:6333/collections/optimize
```