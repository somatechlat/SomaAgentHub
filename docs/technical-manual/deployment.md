# SomaAgentHub Deployment Guide

**Comprehensive instructions for deploying SomaAgentHub to production environments.**

This guide provides detailed, step-by-step instructions for deploying the SomaAgentHub platform to a Kubernetes cluster. It is intended for DevOps Engineers, SREs, and System Administrators.

---

## 🎯 Deployment Prerequisites

Before you begin, ensure your environment meets the following requirements.

### 1. Infrastructure
- **Kubernetes Cluster**: Version 1.24+ (EKS, GKE, AKS, or on-premises).
- **kubectl**: Configured to connect to your cluster.
- **Helm**: Version 3.8+ installed.
- **Persistent Storage**: A default StorageClass must be available for databases.
- **Ingress Controller**: An Ingress controller (like NGINX or Traefik) should be installed to expose services.

### 2. Tools
- **Git**: To clone the repository.
- **Docker**: For building and pushing custom images (if necessary).
- **make**: To use the automated deployment scripts.

### 3. Verification Commands
```bash
# Verify cluster access
kubectl cluster-info

# Verify Helm installation
helm version

# Check for a default storage class
kubectl get storageclass
```

---

## 🚀 Production Deployment Steps

This section outlines the standard procedure for a production-grade deployment using Helm.

### Step 1: Clone the Repository
```bash
git clone https://github.com/somatechlat/somaAgentHub.git
cd somaAgentHub
```

### Step 2: Configure Production Values
The deployment is configured via a Helm values file.

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