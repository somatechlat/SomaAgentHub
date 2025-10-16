# SomaAgentHub Installation Guide

This guide will get SomaAgentHub running on your system in under 15 minutes. Choose your preferred deployment method based on your environment and requirements.

---

## 🎯 Installation Options

| Method | Best For | Time Required | Complexity |
|--------|----------|---------------|------------|
| **[Docker Compose](#docker-compose-recommended)** | Local development, testing | 5 minutes | ⭐ Easy |
| **[Kubernetes (Kind)](#kubernetes-local-cluster)** | Production-like setup | 10 minutes | ⭐⭐ Moderate |
| **[Kubernetes (Existing)](#existing-kubernetes-cluster)** | Production deployment | 15 minutes | ⭐⭐⭐ Advanced |
| **[Cloud Deployment](#cloud-deployment)** | Managed production | 20 minutes | ⭐⭐⭐ Advanced |

---

## ✅ Prerequisites

Before installing SomaAgentHub, ensure you have the following tools installed:

### Required for All Installations
- **Docker** (20.10+) - [Install Docker](https://docs.docker.com/get-docker/)
- **Git** - [Install Git](https://git-scm.com/downloads)

### Required for Kubernetes Deployments
- **kubectl** (1.24+) - [Install kubectl](https://kubernetes.io/docs/tasks/tools/)
- **Helm** (3.8+) - [Install Helm](https://helm.sh/docs/intro/install/)
- **Kind** (0.17+) - [Install Kind](https://kind.sigs.k8s.io/docs/user/quick-start/) _(for local clusters)_

### System Requirements
- **CPU**: 2+ cores (4+ recommended for Kubernetes)
- **RAM**: 4GB minimum (8GB+ recommended)
- **Storage**: 10GB free space (20GB+ for full development setup)
- **OS**: macOS, Linux, or Windows with WSL2

---

## 🐳 Docker Compose (Recommended)

The fastest way to get SomaAgentHub running locally for development and testing.

### 1. Clone the Repository

```bash
git clone https://github.com/somatechlat/somaAgentHub.git
cd somaAgentHub
```

### 2. Start the Platform

```bash
# Start all services with dependencies
make dev-up

# This starts:
# - Gateway API (port 10000)
# - Orchestrator Service (port 10001)  
# - Memory Gateway (port 10004)
# - Policy Engine (port 10003)
# - Identity Service (port 10002)
# - Supporting infrastructure (Redis, PostgreSQL, Temporal)
```

### 3. Verify Installation

```bash
# Check service health
curl http://localhost:10000/health
# Expected: {"status": "healthy"}

# List running services
docker compose ps
```

### 4. Access the Platform

- **Gateway API**: http://localhost:10000
- **API Documentation**: http://localhost:10000/docs
- **Temporal Web UI**: http://localhost:8233
- **Admin Console**: http://localhost:3000

---

## ☸️ Kubernetes (Local Cluster)

Deploy SomaAgentHub on a local Kubernetes cluster using Kind for a production-like environment.

### 1. Create Local Kubernetes Cluster

```bash
# Create Kind cluster with proper configuration
kind create cluster --name soma-agent-hub --config kind-cluster.yaml

# Verify cluster is ready
kubectl cluster-info --context kind-soma-agent-hub
```

### 2. Deploy SomaAgentHub

```bash
# Build and deploy all services
make start-cluster

# This will:
# - Build all Docker images
# - Deploy to Kubernetes via Helm
# - Set up monitoring and observability
# - Configure ingress and networking
```

### 3. Verify Kubernetes Deployment

```bash
# Check all pods are running
kubectl get pods -n soma-agent-hub

# Check services
kubectl get svc -n soma-agent-hub

# Run smoke tests
make k8s-smoke
```

### 4. Access Services

```bash
# Port-forward Gateway API
make port-forward-gateway LOCAL=10000 REMOTE=10000

# Port-forward Grafana (monitoring)
kubectl port-forward -n observability svc/prometheus-grafana 3000:80

# Port-forward Temporal Web UI
kubectl port-forward -n soma-agent-hub svc/temporal-frontend 8233:7233
```

---

## 🌐 Existing Kubernetes Cluster

Deploy SomaAgentHub to an existing Kubernetes cluster (GKE, EKS, AKS, etc.).

### 1. Configure kubectl

Ensure your `kubectl` is configured to access your target cluster:

```bash
# Verify cluster access
kubectl get nodes

# Check available storage classes
kubectl get storageclass
```

### 2. Install Dependencies

```bash
# Add Helm repositories
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install monitoring stack (optional but recommended)
kubectl create namespace observability
helm install prometheus prometheus-community/kube-prometheus-stack -n observability
```

### 3. Deploy SomaAgentHub

```bash
# Create namespace
kubectl create namespace soma-agent-hub

# Deploy with Helm
helm install soma-agent-hub ./k8s/helm/soma-agent \
  --namespace soma-agent-hub \
  --set global.domain=your-domain.com \
  --set ingress.enabled=true
```

### 4. Configure Ingress (Production)

```bash
# Install ingress controller (if not present)
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Configure DNS for your domain to point to the ingress controller
# Example: soma-agent-hub.your-domain.com -> LoadBalancer IP
```

---

## ☁️ Cloud Deployment

Deploy to managed Kubernetes services with enhanced security and scalability.

### AWS EKS

```bash
# Create EKS cluster
eksctl create cluster --name soma-agent-hub --region us-west-2 --nodes 3

# Install AWS Load Balancer Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"

# Deploy SomaAgentHub with AWS-specific settings
helm install soma-agent-hub ./k8s/helm/soma-agent \
  --set cloud.provider=aws \
  --set ingress.class=alb \
  --set storage.class=gp3
```

### Google GKE

```bash
# Create GKE cluster
gcloud container clusters create soma-agent-hub \
  --zone us-central1-a \
  --num-nodes 3 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 10

# Deploy with GCP-specific settings
helm install soma-agent-hub ./k8s/helm/soma-agent \
  --set cloud.provider=gcp \
  --set ingress.class=gce \
  --set storage.class=ssd
```

### Azure AKS

```bash
# Create AKS cluster
az aks create \
  --resource-group myResourceGroup \
  --name soma-agent-hub \
  --node-count 3 \
  --enable-addons monitoring

# Deploy with Azure-specific settings
helm install soma-agent-hub ./k8s/helm/soma-agent \
  --set cloud.provider=azure \
  --set ingress.class=azure \
  --set storage.class=managed-premium
```

---

## 🔧 Post-Installation Configuration

### Environment Variables

Configure key environment variables for your deployment:

```bash
# Core platform settings
export SOMA_DOMAIN="your-domain.com"
export SOMA_ENVIRONMENT="production"
export SOMA_LOG_LEVEL="INFO"

# External service integrations
export OPENAI_API_KEY="your-openai-key"
export GITHUB_TOKEN="your-github-token"
export SLACK_BOT_TOKEN="your-slack-token"
```

### Security Configuration

```bash
# Generate secure secrets
kubectl create secret generic soma-secrets \
  --from-literal=jwt-secret=$(openssl rand -base64 32) \
  --from-literal=db-password=$(openssl rand -base64 16) \
  --namespace soma-agent-hub

# Configure TLS certificates (production)
kubectl apply -f k8s/tls-certificates.yaml
```

### Monitoring Setup

```bash
# Import Grafana dashboards
kubectl apply -f k8s/monitoring/grafana-dashboards.yaml

# Configure alerts
kubectl apply -f k8s/monitoring/prometheus-rules.yaml
```

---

## ✅ Verification Steps

After installation, verify your SomaAgentHub deployment:

### 1. Health Checks

```bash
# Check service health endpoints
curl https://your-domain.com/health
curl https://your-domain.com/v1/models

# Expected responses:
# {"status": "healthy"}
# {"data": [...], "object": "list"}
```

### 2. Integration Tests

```bash
# Run comprehensive integration tests
make integration-test

# Run specific service tests
python scripts/integration-tests.py --service gateway-api
python scripts/integration-tests.py --service orchestrator
```

### 3. Load Testing

```bash
# Basic load testing
python scripts/load_testing.py \
  --target https://your-domain.com \
  --concurrent 10 \
  --duration 60s
```

---

## 🚨 Troubleshooting

### Common Issues

**Services Not Starting**
```bash
# Check logs
kubectl logs -n soma-agent-hub deployment/gateway-api
docker compose logs gateway-api

# Check resource constraints
kubectl describe pods -n soma-agent-hub
```

**Database Connection Errors**
```bash
# Verify database is running
kubectl get pods -l app=postgresql -n soma-agent-hub

# Check connection strings
kubectl get configmap soma-config -o yaml -n soma-agent-hub
```

**Ingress/Load Balancer Issues**
```bash
# Check ingress status
kubectl get ingress -n soma-agent-hub

# Verify DNS resolution
nslookup your-domain.com
```

### Getting Help

- **Documentation**: Check the [Technical Manual](../technical-manual/) for operational details
- **Community**: Open an issue in the GitHub repository
- **Logs**: Always include logs when reporting issues

---

## 🎉 Next Steps

Now that SomaAgentHub is installed:

1. **[Complete the Quick Start Tutorial](quick-start-tutorial.md)** - Learn basic workflows
2. **[Explore Core Features](features/)** - Discover platform capabilities  
3. **[Review Integration Examples](../SOMAGENTHUB_INTEGRATION_GUIDE.md)** - See real-world usage patterns
4. **[Set Up Monitoring](../technical-manual/monitoring.md)** - Configure observability and alerts

---

**Congratulations! SomaAgentHub is ready to orchestrate your autonomous agents.**
