# Deployment Guide

**Comprehensive procedures for deploying SomaAgentHub across local development, staging, and production Kubernetes environments.**

---

## 📋 Table of Contents

1. [Quick Start](#quick-start-docker-compose)
2. [Local Development (Docker Compose)](#local-development-docker-compose)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Production Configuration](#production-configuration)
5. [Health Checks & Monitoring](#health-checks--monitoring)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start (Docker Compose)

### Prerequisites

```bash
# Verify installed tools
docker --version       # 24.0+
docker-compose --version  # 2.20+
git --version         # 2.40+
make --version        # GNU Make 3.81+
```

### Deploy in 3 Steps

```bash
# 1. Clone and setup
git clone https://github.com/somatechlat/SomaAgentHub.git
cd SomaAgentHub
make setup

# 2. Configure (if needed - edit .env)
# Skip if using defaults (suitable for dev)

# 3. Start all services
make docker-compose-up

# 4. Verify health
docker-compose ps
curl http://localhost:10000/health
```

**Expected result: All 15+ containers running with health status ✅**

---

## Local Development (Docker Compose)

### Architecture

```
┌─────────────────────────────────────────────┐
│      Local Machine (macOS/Linux)            │
├─────────────────────────────────────────────┤
│                                             │
│  Docker Engine (24.0+)                     │
│  ├─ Gateway API (10000)                   │
│  ├─ Orchestrator (10001)                  │
│  ├─ Identity Service (10002)              │
│  │                                        │
│  ├─ PostgreSQL (5432)                     │
│  ├─ Redis (6379)                         │
│  ├─ Qdrant (6333)                        │
│  ├─ ClickHouse (8123)                    │
│  ├─ MinIO (9000)                         │
│  ├─ Temporal (7233)                      │
│  │                                        │
│  ├─ Vault (8200)                         │
│  ├─ Prometheus (9090)                    │
│  ├─ Grafana (3000)                       │
│  ├─ Loki (3100)                          │
│  ├─ Tempo (3200)                         │
│  └─ OTEL Collector (4317)                │
│                                             │
│  Volumes: 8+ persistent data volumes        │
│                                             │
└─────────────────────────────────────────────┘
```

### Configuration Files

#### `.env` - Environment Variables

```bash
# Application
GATEWAY_API_PORT=10000
ORCHESTRATOR_PORT=10001
IDENTITY_SERVICE_PORT=10002

# Infrastructure
POSTGRES_USER=somaagent
POSTGRES_PASSWORD=somaagent
POSTGRES_DB=somaagent
REDIS_URL=redis://redis:6379/0
TEMPORAL_HOST=temporal-server:7233

# Observability
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
LOKI_PORT=3100
TEMPO_PORT=3200

# Secrets (dev only - use Vault in production)
SOMAGENT_IDENTITY_JWT_SECRET=dev-secret
VAULT_TOKEN=dev-token

# Performance tuning (adjust for your hardware)
POSTGRES_SHARED_BUFFERS=256MB
REDIS_MAXMEMORY=512MB
```

### Production-Grade Features in docker-compose.yml

**File location:** `/docker-compose.yml`

**Features:**
- Health checks for every service (10s intervals, 6 retries)
- Resource limits and requests
- Restart policies (`unless-stopped`)
- Named volumes for data persistence
- Internal networking (no external exposure)
- Logging configuration (JSON format)

### Lifecycle Commands

```bash
# Start all services (detached)
docker-compose up -d

# Start specific service
docker-compose up -d postgres redis

# View service logs
docker-compose logs -f gateway-api

# Stop all services (preserve data)
docker-compose down

# Stop and remove volumes (DESTRUCTIVE)
docker-compose down -v

# Restart a service
docker-compose restart postgres

# Execute command in container
docker-compose exec gateway-api bash
docker-compose exec app-postgres psql -U somaagent -d somaagent

# View resource usage
docker stats --no-stream

# Check service status
docker-compose ps
```

### Networking

All services are on internal Docker bridge network `somaagenthub-network`:

```bash
# Inspect network
docker network inspect somaagenthub-network

# Services accessible by hostname
# Example: from gateway-api container:
#   curl http://orchestrator:10001/ready
#   curl http://redis:6379
```

### Volume Persistence

Data is persisted in Docker volumes:

```bash
# List volumes
docker volume ls | grep somaagenthub

# Inspect volume location
docker volume inspect somaagenthub-app-postgres-data
# Output includes: "Mountpoint": "/var/lib/docker/volumes/..."

# Backup volume data
docker run --rm -v somaagenthub-app-postgres-data:/data \
  -v $(pwd):/backup alpine tar czf /backup/postgres-backup.tar.gz /data

# Restore volume data
docker run --rm -v somaagenthub-app-postgres-data:/data \
  -v $(pwd):/backup alpine tar xzf /backup/postgres-backup.tar.gz -C /data
```

---

## Kubernetes Deployment

### Prerequisites

```bash
# Local K8s cluster (Kind)
kind --version              # 0.20.0+

# Kubernetes client
kubectl --version           # 1.28+

# Package manager
helm --version              # 3.13+

# Create local cluster
kind create cluster --name soma-dev --config infra/kind/cluster-config.yaml
kubectl cluster-info
```

### Create Kubernetes Cluster (Kind)

```bash
# Create single-node cluster
kind create cluster --name soma-dev

# Or multi-node with custom config
kind create cluster --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: soma-dev
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30000
    hostPort: 10000
    protocol: TCP
  - containerPort: 30001
    hostPort: 10001
    protocol: TCP
  - containerPort: 30002
    hostPort: 10002
    protocol: TCP
EOF

# Verify cluster
kubectl get nodes
# Expected: soma-dev-control-plane   Ready    control-plane
```

### Namespace & RBAC Setup

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create service account
kubectl create serviceaccount soma-deployer -n soma-agent-hub
kubectl create clusterrolebinding soma-deployer \
  --clusterrole=cluster-admin --serviceaccount=soma-agent-hub:soma-deployer

# Verify
kubectl get sa -n soma-agent-hub
kubectl get rolebindings -n soma-agent-hub
```

### Deploy Core Services

```bash
# 1. Deploy infrastructure (PostgreSQL, Redis, etc.)
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/qdrant-deployment.yaml

# 2. Wait for data services to be healthy
kubectl wait --for=condition=ready pod \
  -l app=postgres -n soma-agent-hub --timeout=300s

# 3. Deploy application services
kubectl apply -f k8s/gateway-api-deployment.yaml
kubectl apply -f k8s/orchestrator-deployment.yaml
kubectl apply -f k8s/identity-service-deployment.yaml

# 4. Deploy observability
kubectl apply -f k8s/prometheus-deployment.yaml
kubectl apply -f k8s/grafana-deployment.yaml

# 5. Deploy security (Vault, policy engine)
kubectl apply -f k8s/vault-deployment.yaml
kubectl apply -f k8s/openfga-deployment.yaml

# 6. Deploy mesh (Istio, if applicable)
kubectl apply -f k8s/istio-peer-auth.yaml
kubectl apply -f k8s/istio-virtual-services.yaml
```

### Helm Chart Deployment (Recommended for Production)

```bash
# 1. Add SomaAgentHub Helm repo
helm repo add somaagenthub https://charts.somaagenthub.io
helm repo update

# 2. Create values override file
cat > my-values.yaml <<EOF
replicaCount: 3
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"
environment: production
EOF

# 3. Install release
helm install soma-release somaagenthub/somagenthub \
  -f my-values.yaml \
  -n soma-agent-hub \
  --create-namespace

# 4. Check status
helm status soma-release -n soma-agent-hub

# 5. Upgrade release
helm upgrade soma-release somaagenthub/somagenthub \
  -f my-values.yaml \
  -n soma-agent-hub

# 6. Rollback on issue
helm rollback soma-release 1 -n soma-agent-hub
```

### Verify Deployment

```bash
# Check all pods running
kubectl get pods -n soma-agent-hub
# Expected: All pods with status Running, Ready 1/1

# Check services
kubectl get svc -n soma-agent-hub
# Expected: IP addresses assigned, ports open

# Check logs
kubectl logs -f deployment/gateway-api -n soma-agent-hub

# Port forward for local testing
kubectl port-forward svc/gateway-api 10000:10000 -n soma-agent-hub
curl http://localhost:10000/health
```

---

## Production Configuration

### Resource Allocation

**Per-service resource requests & limits:**

```yaml
# Example service deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway-api
  namespace: soma-agent-hub
spec:
  replicas: 3  # High availability
  template:
    spec:
      containers:
      - name: gateway-api
        image: somaagenthub/gateway-api:v1.0.0
        resources:
          requests:
            memory: "512Mi"    # Reserved
            cpu: "250m"        # Reserved
          limits:
            memory: "1Gi"      # Max allowed
            cpu: "500m"        # Max allowed
```

**Summary for all services:**

| Service | Memory Request | Memory Limit | CPU Request | CPU Limit |
|---------|---|---|---|---|
| Gateway API | 512Mi | 1Gi | 250m | 500m |
| Orchestrator | 512Mi | 1Gi | 250m | 500m |
| Identity Service | 256Mi | 512Mi | 100m | 250m |
| PostgreSQL | 1Gi | 2Gi | 500m | 1000m |
| Redis | 512Mi | 1Gi | 250m | 500m |
| Qdrant | 1Gi | 2Gi | 500m | 1000m |
| ClickHouse | 1Gi | 2Gi | 500m | 1000m |
| Temporal | 512Mi | 1Gi | 500m | 1000m |

### High Availability Configuration

```bash
# 1. Multi-replica deployment
kubectl scale deployment gateway-api --replicas=3 -n soma-agent-hub

# 2. Pod Disruption Budget (prevent simultaneous evictions)
kubectl apply -f - <<EOF
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: gateway-api-pdb
  namespace: soma-agent-hub
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: gateway-api
EOF

# 3. Horizontal Pod Autoscaler
kubectl apply -f - <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: gateway-api-hpa
  namespace: soma-agent-hub
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: gateway-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF
```

### Storage Configuration

```bash
# 1. Create PersistentVolume for PostgreSQL
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: soma-agent-hub
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  storageClassName: standard
EOF

# 2. Mount in deployment
# (Already configured in postgres-deployment.yaml)
# volumeMounts:
# - name: postgres-storage
#   mountPath: /var/lib/postgresql/data
# volumes:
# - name: postgres-storage
#   persistentVolumeClaim:
#     claimName: postgres-pvc
```

### Secrets Management (Vault Integration)

```bash
# 1. Deploy Vault
kubectl apply -f k8s/vault-deployment.yaml

# 2. Unseal Vault (development only!)
kubectl exec -it vault-0 -n soma-agent-hub -- vault operator init
kubectl exec -it vault-0 -n soma-agent-hub -- vault operator unseal

# 3. Create secrets
kubectl exec vault-0 -n soma-agent-hub -- vault kv put secret/somaagent \
  db_user=somaagent \
  db_password=$(openssl rand -base64 32) \
  jwt_secret=$(openssl rand -base64 32)

# 4. Reference in pod spec
# env:
# - name: POSTGRES_PASSWORD
#   valueFrom:
#     secretKeyRef:
#       name: vault-secret
#       key: db_password
```

---

## Health Checks & Monitoring

### Readiness & Liveness Probes

```yaml
# Example service deployment
spec:
  containers:
  - name: gateway-api
    livenessProbe:
      httpGet:
        path: /health
        port: 10000
      initialDelaySeconds: 30
      periodSeconds: 10
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /ready
        port: 10000
      initialDelaySeconds: 10
      periodSeconds: 5
      failureThreshold: 3
```

### Manual Health Verification

```bash
# Check Gateway API
curl -v http://localhost:10000/health
# Expected: 200 OK, {"status": "healthy"}

# Check Orchestrator
curl http://localhost:10001/ready
# Expected: 200 OK

# Check Identity Service
curl http://localhost:10002/health
# Expected: 200 OK, status field present

# Check PostgreSQL connectivity
docker-compose exec app-postgres pg_isready -U somaagent -d somaagent
# Expected: accepting connections

# Check Redis
redis-cli -h localhost ping
# Expected: PONG

# Check Qdrant
curl http://localhost:6333/health
# Expected: 200 OK

# Check Temporal
grpcurl -plaintext localhost:7233 temporal.api.workflowservice.v1.WorkflowService/DescribeNamespace
# Expected: (namespace description)
```

### Prometheus Metrics

```bash
# Access Prometheus
curl http://localhost:9090/api/v1/query?query=up

# Query active targets
curl http://localhost:9090/api/v1/targets

# Query service latency
curl 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(request_duration_seconds_bucket[5m]))'
```

### Grafana Dashboards

```bash
# Access Grafana UI
open http://localhost:3000

# Default credentials (change immediately in production!)
# Email: admin
# Password: admin

# Pre-built dashboards:
# - SomaAgentHub Overview
# - Service Metrics
# - Database Performance
# - API Latency
```

---

## Troubleshooting

### Common Deployment Issues

#### Services failing to start

```bash
# Check pod status
kubectl describe pod <pod-name> -n soma-agent-hub

# View logs
kubectl logs <pod-name> -n soma-agent-hub
kubectl logs <pod-name> -c <container-name> -n soma-agent-hub

# Common causes:
# 1. Image not available
#    → Fix: docker pull <image>, or check image name/tag
# 2. Resource limits exceeded
#    → Fix: Increase memory/CPU limits, or reduce replica count
# 3. Dependency not ready
#    → Fix: Check postgres/redis health first
```

#### Database connection failures

```bash
# Test PostgreSQL connectivity
kubectl run -it --rm debug --image=postgres:16 --restart=Never -- \
  psql -h postgres -U somaagent -d somaagent -c "SELECT 1;"

# Check postgres pod logs
kubectl logs -f postgres-0 -n soma-agent-hub

# Verify environment variables
kubectl exec gateway-api-0 -n soma-agent-hub -- env | grep POSTGRES
```

#### Out of memory errors

```bash
# Check pod resource usage
kubectl top pod -n soma-agent-hub

# Check node resources
kubectl top nodes

# Increase memory limit
kubectl set resources deployment gateway-api \
  --limits=memory=2Gi --requests=memory=1Gi \
  -n soma-agent-hub

# Or scale down replicas
kubectl scale deployment gateway-api --replicas=1 -n soma-agent-hub
```

#### Networking issues

```bash
# Test internal DNS
kubectl exec -it <pod> -n soma-agent-hub -- nslookup postgres

# Test service connectivity
kubectl exec -it <pod> -n soma-agent-hub -- \
  curl http://postgres:5432 -v

# Check network policies
kubectl get networkpolicies -n soma-agent-hub

# Check service endpoints
kubectl get endpoints -n soma-agent-hub
```

---

## Rollback Procedures

### Docker Compose Rollback

```bash
# Keep old compose file version-controlled in git
git log --oneline docker-compose.yml

# Checkout old version
git checkout <commit-hash> -- docker-compose.yml

# Restart services with old config
docker-compose down
docker-compose up -d
```

### Kubernetes Rollback

```bash
# View rollout history
kubectl rollout history deployment/gateway-api -n soma-agent-hub

# Rollback to previous revision
kubectl rollout undo deployment/gateway-api -n soma-agent-hub

# Rollback to specific revision
kubectl rollout undo deployment/gateway-api --to-revision=2 -n soma-agent-hub

# Check rollback status
kubectl rollout status deployment/gateway-api -n soma-agent-hub
```

---

## Next Steps

- **[Monitoring & Observability](./monitoring.md)** - Setup dashboards and alerts
- **[Security & Hardening](./security/)** - Production security configuration
- **[Runbooks](./runbooks/)** - Operational procedures

---

**✅ Deployment complete! Services are live and ready for use.**

1.  **Copy the production template:**
    ```bash
    cp k8s/helm/soma-agent/values.prod.yaml k8s/helm/soma-agent/my-production-values.yaml
    ```

2.  **Edit `my-production-values.yaml`:**
    Update the following critical sections:
    - `global.domain`: Set your public-facing domain (e.g., `soma.mycompany.com`).
    - `ingress.className`: Specify your Ingress controller class.
    - `persistence`: Configure database sizes and storage classes.
    - `resources`: Adjust CPU and memory requests/limits for each service based on expected load.
    - `secrets`: Provide production-grade secrets for JWT, database passwords, and API keys. **Do not use defaults.**

### Step 3: Create Namespace and Secrets
It's best practice to run the application in its own namespace and manage secrets securely.

1.  **Create the namespace:**
    ```bash
    kubectl create namespace soma-agent-hub
    ```

2.  **Create Kubernetes Secrets:**
    Create a `secrets.yaml` file (and add it to `.gitignore`):
    ```yaml
    apiVersion: v1
    kind: Secret
    metadata:
      name: soma-platform-secrets
      namespace: soma-agent-hub
    type: Opaque
    stringData:
      JWT_SECRET: "your-super-strong-jwt-secret"
      POSTGRES_PASSWORD: "your-secure-db-password"
      REDIS_PASSWORD: "your-secure-redis-password"
      OPENAI_API_KEY: "your-openai-api-key"
    ```
    Apply it:
    ```bash
    kubectl apply -f secrets.yaml
    ```

### Step 4: Deploy with Helm
Use the provided `Makefile` target for a streamlined installation or run the `helm` command directly.

```bash
# Recommended: Use the Makefile
make helm-install VALUES_FILE=k8s/helm/soma-agent/my-production-values.yaml

# Or, run Helm directly
helm install soma-agent-hub k8s/helm/soma-agent/ \
  --namespace soma-agent-hub \
  --values k8s/helm/soma-agent/my-production-values.yaml
```

### Step 5: Verify the Deployment
After the Helm chart is deployed, verify that all components are running correctly.

1.  **Check Pod Status:**
    ```bash
    kubectl get pods -n soma-agent-hub -w
    # Wait for all pods to be in the 'Running' state.
    ```

2.  **Check Service Status:**
    ```bash
    kubectl get services -n soma-agent-hub
    ```

3.  **Check Ingress:**
    ```bash
    kubectl get ingress -n soma-agent-hub
    # Ensure the ADDRESS field is populated with your load balancer's IP.
    ```

4.  **Run Smoke Tests:**
    The repository includes a smoke test script to verify core functionality.
    ```bash
    make k8s-smoke HOST="soma.mycompany.com"
    ```

---

## 🎛️ Configuration Deep Dive

### Resource Management
It is critical to configure resource requests and limits for each microservice in your `values.yaml` to ensure cluster stability.

```yaml
# Example for gateway-api in my-production-values.yaml
gateway-api:
  replicaCount: 2
  resources:
    requests:
      cpu: "250m"
      memory: "512Mi"
    limits:
      cpu: "1000m"
      memory: "1Gi"
```

### Scaling
The platform can be scaled horizontally by adjusting the `replicaCount` for each service.

-   **Stateless Services**: `gateway-api`, `policy-engine`, `slm-service` can be scaled freely.
-   **Stateful Services**: `orchestrator` (via Temporal workers), `memory-gateway` require careful scaling.
-   **Databases**: Scale PostgreSQL, Redis, and Qdrant according to their specific documentation.

### High Availability (HA)
For a high-availability setup:
- Run at least 2 replicas for each stateless service.
- Deploy your Kubernetes cluster across multiple availability zones.
- Use a managed, multi-AZ database service (e.g., AWS RDS, Google Cloud SQL).
- Configure Pod Anti-Affinity to ensure replicas are scheduled on different nodes.

---

## 🔄 Upgrades and Rollbacks

### Upgrading the Platform
To upgrade to a new version of SomaAgentHub:

1.  **Update the repository:**
    ```bash
    git pull origin main
    ```
2.  **Review `values.yaml` changes:** Check for any new configuration options.
3.  **Perform the upgrade:**
    ```bash
    helm upgrade soma-agent-hub k8s/helm/soma-agent/ \
      --namespace soma-agent-hub \
      --values k8s/helm/soma-agent/my-production-values.yaml
    ```

### Rolling Back a Deployment
If an upgrade fails, you can easily roll back to a previous revision with Helm.

1.  **List release history:**
    ```bash
    helm history soma-agent-hub -n soma-agent-hub
    ```
2.  **Roll back to the previous version (e.g., revision 1):**
    ```bash
    helm rollback soma-agent-hub 1 -n soma-agent-hub
    ```

---

## 🔗 Related Documentation
- **[System Architecture](architecture.md)**: To understand the components you are deploying.
- **[Monitoring Guide](monitoring.md)**: To configure observability for your new deployment.
- **[Backup and Recovery](backup-and-recovery.md)**: To set up data protection for your stateful services.
```