# SomaAgentHub Development Environment Setup

**Complete guide for setting up, developing, deploying, and troubleshooting SomaAgentHub**

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Development Environment](#development-environment)
4. [Building & Testing](#building--testing)
5. [Deployment](#deployment)
6. [API Testing](#api-testing)
7. [Troubleshooting](#troubleshooting)
8. [Common Issues](#common-issues)

---

## Prerequisites

### Required Software

| Tool | Version | Installation |
|------|---------|--------------|
| **Docker Desktop** | Latest | [Download](https://www.docker.com/products/docker-desktop) |
| **kubectl** | 1.28+ | `brew install kubectl` |
| **Kind** | 0.20+ | `brew install kind` |
| **Helm** | 3.12+ | `brew install helm` |
| **Python** | 3.13+ | `brew install python@3.13` |
| **jq** | Latest | `brew install jq` |
| **curl** | Latest | Pre-installed on macOS |

### System Requirements

- **OS**: macOS, Linux, or WSL2 on Windows
- **RAM**: Minimum 8GB (16GB recommended)
- **Disk**: 20GB free space
- **CPU**: 4+ cores recommended

### Verify Installations

```bash
# Check Docker
docker --version
docker ps

# Check Kubernetes tools
kubectl version --client
kind version
helm version

# Check Python
python3 --version

# Check utilities
jq --version
curl --version
```

---

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/somatechlat/somagent.git
cd somagent
```

### 2. Start Docker Desktop

```bash
# Open Docker Desktop application
open -a Docker

# Wait for Docker to start (check status)
docker ps
```

### 3. Create Kind Cluster

```bash
# Create a new Kind cluster named "soma-agent-hub"
kind create cluster --name soma-agent-hub

# Verify cluster is running
kubectl cluster-info --context kind-soma-agent-hub

# Check nodes
kubectl get nodes
```

**Expected Output:**
```
NAME                           STATUS   ROLES           AGE   VERSION
soma-agent-hub-control-plane   Ready    control-plane   1m    v1.34.0
```

---

## Development Environment

### Project Structure

```
somagent/
├── services/
│   ├── gateway-api/          # Main API gateway (port 60000)
│   ├── identity-service/     # Authentication & authorization
│   ├── orchestrator/         # Task orchestration
│   ├── memory-gateway/       # Memory management
│   ├── policy-engine/        # Policy enforcement
│   └── ...                   # Other microservices
├── k8s/
│   └── helm/
│       └── soma-agent/       # Helm chart for deployment
├── scripts/
│   ├── build_and_push.sh     # Build all Docker images
│   └── rapid-deploy-all.sh   # Quick deployment script
└── docs/                     # Documentation
```

### Key Configuration Files

| File | Purpose |
|------|---------|
| `k8s/helm/soma-agent/values.yaml` | Helm chart configuration |
| `k8s/helm/soma-agent/templates/service.yaml` | Kubernetes Service definitions |
| `k8s/helm/soma-agent/templates/deployment.yaml` | Pod deployment specs |
| `services/gateway-api/Dockerfile` | Gateway API container definition |
| `services/gateway-api/app/main.py` | Gateway API application code |

---

## Building & Testing

### Build All Docker Images

```bash
# Build and load all service images into Kind
./scripts/build_and_push.sh
```

**What this does:**
- Builds Docker images for all services
- Tags images with version `029a130`
- Loads images into the Kind cluster node
- Takes ~2-5 minutes

**Expected Output:**
```
🔨 Building jobs...
✅ jobs complete
🔨 Building gateway-api...
✅ gateway-api complete
...
🎉 All images built and pushed successfully!
```

### Build Single Service (Gateway API)

```bash
# Navigate to service directory
cd services/gateway-api

# Build image
docker build -t ghcr.io/somatechlat/soma-gateway-api:029a130 \
             -t ghcr.io/somatechlat/soma-gateway-api:latest .

# Load into Kind cluster
kind load docker-image ghcr.io/somatechlat/soma-gateway-api:029a130 --name soma-agent-hub

# Return to project root
cd ../..
```

### Verify Images

```bash
# List Docker images
docker images | grep soma

# Check images in Kind node
docker exec soma-agent-hub-control-plane crictl images | grep soma
```

---

## Deployment

### Deploy with Helm

```bash
# Deploy the entire platform
helm upgrade --install soma-agent-hub ./k8s/helm/soma-agent \
  --namespace soma-agent-hub \
  --create-namespace \
  --set global.imageTag=029a130 \
  --wait \
  --timeout 10m
```

**What this does:**
- Creates namespace `soma-agent-hub`
- Deploys all enabled services
- Waits for pods to be ready
- Times out after 10 minutes if not ready

### Verify Deployment

```bash
# Check Helm release
helm list -n soma-agent-hub

# Check pods
kubectl get pods -n soma-agent-hub

# Check services
kubectl get svc -n soma-agent-hub

# Check specific pod logs
kubectl logs -l app.kubernetes.io/name=gateway-api -n soma-agent-hub
```

**Expected Pod Status:**
```
NAME                           READY   STATUS    RESTARTS   AGE
gateway-api-xxxxx-xxxxx        1/1     Running   0          2m
```

### Update Deployment (After Code Changes)

```bash
# 1. Rebuild image
cd services/gateway-api
docker build -t ghcr.io/somatechlat/soma-gateway-api:029a130 .
kind load docker-image ghcr.io/somatechlat/soma-gateway-api:029a130 --name soma-agent-hub
cd ../..

# 2. Restart deployment
kubectl rollout restart deployment gateway-api -n soma-agent-hub

# 3. Watch rollout status
kubectl rollout status deployment gateway-api -n soma-agent-hub

# 4. Verify new pod is running
kubectl get pods -n soma-agent-hub -l app.kubernetes.io/name=gateway-api
```

---

## API Testing

### Access Gateway API

#### Option 1: Port Forward (Recommended for Local Testing)

```bash
# Forward local port 60000 to the gateway pod
kubectl port-forward -n soma-agent-hub deployment/gateway-api 60000:60000 &

# Verify connection
curl http://localhost:60000/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "service": "gateway-api"
}
```

#### Option 2: NodePort (Cluster Access)

```bash
# Get node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Access via NodePort (30080)
curl http://$NODE_IP:30080/health
```

### Test All Endpoints

```bash
# 1. Root endpoint
curl -s http://localhost:60000/ | jq .

# 2. Health check
curl -s http://localhost:60000/health | jq .

# 3. Metrics (Prometheus format)
curl -s http://localhost:60000/metrics | head -20

# 4. List models
curl -s http://localhost:60000/v1/models | jq .

# 5. Create session
curl -s -X POST http://localhost:60000/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test-user","metadata":{"test":true}}' | jq .

# 6. Chat completion
curl -s -X POST http://localhost:60000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"somaagent-demo","messages":[{"role":"user","content":"Hello"}]}' | jq .

# 7. OpenAPI documentation (in browser)
open http://localhost:60000/docs
```

### API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root message |
| `/health` | GET | Health check |
| `/metrics` | GET | Prometheus metrics |
| `/docs` | GET | Interactive API docs (Swagger UI) |
| `/openapi.json` | GET | OpenAPI schema |
| `/v1/models` | GET | List available models |
| `/v1/sessions` | POST | Create new session |
| `/v1/chat/completions` | POST | Chat completions (OpenAI-compatible) |

---

## Troubleshooting

### Common Commands

```bash
# View pod logs
kubectl logs -f deployment/gateway-api -n soma-agent-hub

# Describe pod (see events and status)
kubectl describe pod -l app.kubernetes.io/name=gateway-api -n soma-agent-hub

# Get pod details
kubectl get pods -n soma-agent-hub -o wide

# Check service endpoints
kubectl get endpoints gateway-api -n soma-agent-hub

# Execute command inside pod
kubectl exec -it deployment/gateway-api -n soma-agent-hub -- /bin/sh

# Delete and recreate deployment
kubectl delete deployment gateway-api -n soma-agent-hub
helm upgrade --install soma-agent-hub ./k8s/helm/soma-agent \
  --namespace soma-agent-hub \
  --set global.imageTag=029a130 \
  --wait --timeout 10m
```

### Check Cluster Health

```bash
# Cluster info
kubectl cluster-info

# Node status
kubectl get nodes

# All resources in namespace
kubectl get all -n soma-agent-hub

# Events (recent issues)
kubectl get events -n soma-agent-hub --sort-by='.lastTimestamp'
```

### Clean Up Resources

```bash
# Delete Helm release
helm uninstall soma-agent-hub -n soma-agent-hub

# Delete namespace
kubectl delete namespace soma-agent-hub

# Delete Kind cluster
kind delete cluster --name soma-agent-hub

# Remove all Docker images
docker rmi $(docker images 'ghcr.io/somatechlat/soma-*' -q)
```

---

## Common Issues

### Issue 1: Pod in `InvalidImageName` State

**Symptom:**
```bash
kubectl get pods -n soma-agent-hub
# Shows: InvalidImageName
```

**Cause:** Image not found in Kind cluster or incorrect image reference

**Solution:**
```bash
# 1. Check image exists
docker images | grep soma-gateway-api

# 2. Load image into Kind
kind load docker-image ghcr.io/somatechlat/soma-gateway-api:029a130 --name soma-agent-hub

# 3. Restart deployment
kubectl rollout restart deployment gateway-api -n soma-agent-hub
```

---

### Issue 2: Pod in `CrashLoopBackOff` State

**Symptom:**
```bash
kubectl get pods -n soma-agent-hub
# Shows: CrashLoopBackOff
```

**Cause:** Application crashes on startup

**Solution:**
```bash
# 1. Check logs
kubectl logs -l app.kubernetes.io/name=gateway-api -n soma-agent-hub --previous

# 2. Common fixes:
# - Missing Python dependencies → rebuild image
# - Port already in use → check Dockerfile
# - Missing environment variables → check values.yaml

# 3. Fix and rebuild
cd services/gateway-api
# Fix issue in code or Dockerfile
docker build -t ghcr.io/somatechlat/soma-gateway-api:029a130 .
kind load docker-image ghcr.io/somatechlat/soma-gateway-api:029a130 --name soma-agent-hub
kubectl rollout restart deployment gateway-api -n soma-agent-hub
```

---

### Issue 3: `curl: (7) Failed to connect`

**Symptom:**
```bash
curl http://localhost:60000/health
# Returns: Failed to connect to localhost port 60000
```

**Cause:** Port forward not running

**Solution:**
```bash
# 1. Kill any existing port-forward
pkill -f "kubectl port-forward"

# 2. Start new port-forward
kubectl port-forward -n soma-agent-hub deployment/gateway-api 60000:60000 &

# 3. Wait 2 seconds and test
sleep 2
curl http://localhost:60000/health
```

---

### Issue 4: `context deadline exceeded` During Helm Install

**Symptom:**
```bash
helm upgrade --install ...
# Returns: Error: UPGRADE FAILED: context deadline exceeded
```

**Cause:** Pods taking too long to start or image pull issues

**Solution:**
```bash
# 1. Check pod status
kubectl get pods -n soma-agent-hub

# 2. Check events
kubectl get events -n soma-agent-hub --sort-by='.lastTimestamp' | tail -20

# 3. Increase timeout
helm upgrade --install soma-agent-hub ./k8s/helm/soma-agent \
  --namespace soma-agent-hub \
  --set global.imageTag=029a130 \
  --wait \
  --timeout 15m

# 4. Or deploy without waiting
helm upgrade --install soma-agent-hub ./k8s/helm/soma-agent \
  --namespace soma-agent-hub \
  --set global.imageTag=029a130
```

---

### Issue 5: Docker Not Running

**Symptom:**
```bash
docker ps
# Returns: Cannot connect to the Docker daemon
```

**Solution:**
```bash
# Start Docker Desktop
open -a Docker

# Wait 30 seconds
sleep 30

# Verify
docker ps
```

---

### Issue 6: Kind Cluster Already Exists

**Symptom:**
```bash
kind create cluster --name soma-agent-hub
# Returns: ERROR: cluster already exists
```

**Solution:**
```bash
# Option 1: Use existing cluster
kind get clusters
kubectl cluster-info --context kind-soma-agent-hub

# Option 2: Delete and recreate
kind delete cluster --name soma-agent-hub
kind create cluster --name soma-agent-hub
```

---

## Development Workflow

### Quick Start (From Scratch)

```bash
# 1. Start Docker Desktop
open -a Docker && sleep 30

# 2. Create Kind cluster
kind create cluster --name soma-agent-hub

# 3. Build all images
./scripts/build_and_push.sh

# 4. Deploy with Helm
helm upgrade --install soma-agent-hub ./k8s/helm/soma-agent \
  --namespace soma-agent-hub \
  --create-namespace \
  --set global.imageTag=029a130 \
  --wait --timeout 10m

# 5. Start port-forward
kubectl port-forward -n soma-agent-hub deployment/gateway-api 60000:60000 &

# 6. Test API
curl http://localhost:60000/health
```

### Typical Development Cycle

```bash
# 1. Make code changes
# Edit files in services/gateway-api/app/

# 2. Rebuild image
cd services/gateway-api
docker build -t ghcr.io/somatechlat/soma-gateway-api:029a130 .
kind load docker-image ghcr.io/somatechlat/soma-gateway-api:029a130 --name soma-agent-hub
cd ../..

# 3. Restart deployment
kubectl rollout restart deployment gateway-api -n soma-agent-hub

# 4. Wait for pod to be ready
kubectl rollout status deployment gateway-api -n soma-agent-hub

# 5. Test changes
curl http://localhost:60000/health
```

---

## Configuration Reference

### values.yaml Key Settings

```yaml
# Global settings
global:
  imageTag: "029a130"           # Image version
  imagePullPolicy: IfNotPresent # Never pull from registry
  namespace: soma-agent-hub     # Kubernetes namespace

# Gateway API settings
services:
  gateway-api:
    enabled: true               # Enable this service
    replicaCount: 1             # Number of replicas
    port: 60000                 # Container port
    nodePort: 30080             # External NodePort (30000-32767 range)
    image: "ghcr.io/somatechlat/soma-gateway-api:029a130"
    imagePullPolicy: Never      # Don't pull, use local image
```

### Environment Variables

None currently required. All configuration is in `values.yaml`.

---

## Monitoring & Logs

### Real-time Logs

```bash
# Follow gateway-api logs
kubectl logs -f deployment/gateway-api -n soma-agent-hub

# All pods in namespace
kubectl logs -f --all-containers=true -n soma-agent-hub

# Last 100 lines
kubectl logs --tail=100 deployment/gateway-api -n soma-agent-hub
```

### Metrics

```bash
# Prometheus metrics
curl http://localhost:60000/metrics

# Key metrics to watch:
# - python_gc_collections_total (garbage collection)
# - process_cpu_seconds_total (CPU usage)
# - http_requests_total (request count)
```

---

## Additional Resources

- **OpenAPI Documentation**: `http://localhost:60000/docs`
- **Helm Chart**: `k8s/helm/soma-agent/`
- **Source Code**: `services/gateway-api/app/`
- **Scripts**: `scripts/`

---

## Quick Reference Card

| Task | Command |
|------|---------|
| **Build all images** | `./scripts/build_and_push.sh` |
| **Deploy** | `helm upgrade --install soma-agent-hub ./k8s/helm/soma-agent --namespace soma-agent-hub --set global.imageTag=029a130 --wait --timeout 10m` |
| **Port forward** | `kubectl port-forward -n soma-agent-hub deployment/gateway-api 60000:60000 &` |
| **Test health** | `curl http://localhost:60000/health` |
| **View logs** | `kubectl logs -f deployment/gateway-api -n soma-agent-hub` |
| **Restart** | `kubectl rollout restart deployment gateway-api -n soma-agent-hub` |
| **Clean up** | `kind delete cluster --name soma-agent-hub` |

---

**Last Updated**: October 7, 2025  
**Version**: 1.0  
**Maintainers**: SomaTech Development Team
