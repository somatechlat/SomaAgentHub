# Installation Guide

![Version](https://img.shields.io/badge/version-1.0.0-blue)

## Prerequisites

### Local Development
- Docker & Docker Compose
- Python 3.11+
- Kind (Kubernetes in Docker)
- Helm 3+
- kubectl

### Production Deployment
- Kubernetes 1.24+
- Helm 3+
- Container registry access
- Persistent storage (for Qdrant, Redis, PostgreSQL)

## Quick Start (Local)

### 1. Clone Repository
```bash
git clone https://github.com/somatechlat/somaAgentHub.git
cd somaAgentHub
```

### 2. Create Local Cluster
```bash
make start-cluster
```

This command:
- Creates a Kind cluster named `soma-agent-hub`
- Applies persistent volume configuration
- Creates required namespaces (`soma-agent-hub`, `observability`)
- Builds and loads service images
- Deploys via Helm chart

### 3. Verify Installation
```bash
kubectl get pods -n soma-agent-hub
kubectl get svc -n soma-agent-hub
```

Expected services:
- `gateway-api` (port 10000)
- `orchestrator` (port 10001)
- `identity-service` (port 10002)
- `memory-gateway` (port 10021)
- `policy-engine` (port 10020)

### 4. Access Gateway API
```bash
make port-forward-gateway LOCAL=8080 REMOTE=10000
```

Gateway available at: http://localhost:8080

## Development Setup

### 1. Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### 2. Start Local Infrastructure
```bash
make dev-up
```

Starts:
- Temporal server (port 7233)
- Redis (port 6379)

### 3. Run Services Locally
```bash
make dev-start-services
```

Starts:
- Gateway API on port 10000
- Orchestrator on port 10001

## Production Deployment

### 1. Configure Helm Values
Edit `k8s/helm/soma-agent/values.yaml`:

```yaml
global:
  imageRegistry: your-registry.com
  imageTag: v1.0.0
  namespace: soma-agent-hub

services:
  gateway:
    enabled: true
    replicas: 3
  orchestrator:
    enabled: true
    replicas: 2
  memoryGateway:
    enabled: true
  policyEngine:
    enabled: true
```

### 2. Deploy with Helm
```bash
helm upgrade --install soma-agent-hub ./k8s/helm/soma-agent \
  --namespace soma-agent-hub \
  --create-namespace \
  -f values-production.yaml
```

### 3. Configure Ingress
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: soma-agent-hub
  namespace: soma-agent-hub
spec:
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

## Configuration

### Environment Variables

#### Gateway API
- `SOMAGENT_GATEWAY_REDIS_URL`: Redis connection string
- `SOMAGENT_GATEWAY_ORCHESTRATOR_URL`: Orchestrator service URL
- `AUTH_URL`: Identity service URL
- `PRICING_SERVICE_URL`: Pricing service URL (optional)

#### Orchestrator
- `TEMPORAL_HOST`: Temporal server host:port
- `TEMPORAL_NAMESPACE`: Temporal namespace
- `POLICY_ENGINE_URL`: Policy engine URL
- `IDENTITY_SERVICE_URL`: Identity service URL

#### Memory Gateway
- `QDRANT_URL`: Qdrant vector database URL
- `REDIS_URL`: Redis connection string

### Persistent Storage

Required volumes:
- Qdrant data: `/qdrant/storage`
- Redis data: `/data`
- PostgreSQL data: `/var/lib/postgresql/data`

## Health Checks

All services expose health endpoints:
- `/health` - Liveness probe
- `/ready` - Readiness probe
- `/metrics` - Prometheus metrics

## Troubleshooting

### Common Issues

**Pods not starting**
```bash
kubectl describe pod <pod-name> -n soma-agent-hub
kubectl logs <pod-name> -n soma-agent-hub
```

**Service connectivity**
```bash
kubectl get svc -n soma-agent-hub
kubectl port-forward svc/gateway-api 8080:8000 -n soma-agent-hub
```

**Temporal connection**
```bash
kubectl logs -l app=orchestrator -n soma-agent-hub
```

### Smoke Tests
```bash
make k8s-smoke
```

Validates:
- All pods are running
- Services are accessible
- Health endpoints respond
- Basic workflow execution