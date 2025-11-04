# Deployment Guide for SomaAgentHub

> This guide walks you through deploying the **SomaAgentHub** stack on a local Kubernetes cluster using **Kind**. It covers cluster creation, persistent storage, namespace setup, image building, optional mTLS, Helm installation, verification, and optional features.

---

## 1️⃣ Prerequisites (quick recap)
- **Docker Desktop** (or Docker Engine) with at least **8 GB RAM**.
- **Python 3.11+** – required for helper scripts.
- **kubectl** – Kubernetes CLI.
- **Kind** – `brew install kind` (macOS) or via your package manager.
- **Helm 3** – `brew install helm`.
- **Make** – usually pre‑installed on macOS/Linux.
- (Optional) **VS Code** with the Remote Containers extension.

---

## 2️⃣ Create a Kind cluster (or reuse an existing one)
```bash
# Delete any stale cluster first (safe – it will be recreated)
kind delete cluster --name soma-agent-hub || true

# Create a fresh persistent Kind cluster
kind create cluster --name soma-agent-hub \
    --config=kind-cluster-persistent.yaml
```
The `kind-cluster-persistent.yaml` file configures a storage class and a persistent volume that the chart expects.

> **Tip**: Verify the context after creation:
```bash
kubectl cluster-info --context kind-soma-agent-hub
```

---

## 3️⃣ Apply the persistent volume claim
```bash
kubectl apply -f k8s/local/persistence.yaml
```
You should see `persistentvolume/local-persistent-storage` created.

---

## 4️⃣ Create the required namespaces
```bash
kubectl create namespace soma-agent-hub || true
kubectl create namespace observability || true
```
Both namespaces are used by the Helm chart (the main release lives in `soma-agent-hub`).

---

## 5️⃣ Build and load Docker images
The `make start-cluster` target runs this automatically, but you can build manually if you only need to rebuild images:
```bash
make build-changed
```
All images are tagged as `somaagent/<service>:latest-<git‑sha>` and automatically loaded into the Kind node.

---

## 6️⃣ (Optional) Generate a self‑signed mTLS certificate
If you want mutual TLS between pods, generate the secret **before** installing the chart:
```bash
./scripts/generate-mtls.sh
```
The script creates a secret named `soma-mtls` in the `soma-agent-hub` namespace and prints a reminder to re‑run the Helm install.

---

## 7️⃣ Deploy the Helm chart
```bash
helm upgrade --install soma-agent-hub ./k8s/helm/soma-agent \
    --namespace soma-agent-hub \
    -f ./k8s/helm/soma-agent/values.yaml \
    -f ./k8s/helm/soma-agent/values-dev.yaml \
    --set global.imageTag=$(git rev-parse --short HEAD)
```
**Explanation of flags**
- `upgrade --install` – creates the release if it does not exist.
- `-f values.yaml` – base values.
- `-f values-dev.yaml` – development‑specific overrides (e.g., lower replica counts).
- `--set global.imageTag=…` – pins the images to the exact Git commit you just built.

---

## 8️⃣ Verify the deployment
```bash
# List pods – they should all be in the Running state
kubectl get pods -n soma-agent-hub

# Check the services are exposed
kubectl get svc -n soma-agent-hub
```
You can also stream logs for a specific component, for example the gateway:
```bash
kubectl logs -f -n soma-agent-hub -l app=gateway-api
```

---

## 9️⃣ Port‑forward the gateway (optional, for local API testing)
```bash
make port-forward-gateway LOCAL=8080 REMOTE=10000
```
Now you can reach the gateway at `http://localhost:8080/healthz` or any other endpoint.

---

## 🔟 Optional Features
| Feature | How to enable |
|---------|---------------|
| **mTLS** | Run `./scripts/generate-mtls.sh` **before** the Helm install and keep `mtls.enabled: true` in `values.yaml`. |
| **ServiceMonitors** (Prometheus) | Set `serviceMonitors.enabled: true` in `values.yaml` and install the Prometheus‑Operator (`helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack`). |
| **Ingress** | Un‑comment and configure the `ingress:` block in `values.yaml`, then set `ingress.enabled: true`. |
| **Additional services** (e.g., `slm-service`, `policy-engine`) | Change `services.<name>.enabled: true` in `values.yaml` and ensure the Docker image exists (run `make build-changed`). |

---

## 📌 One‑liner for seasoned users
```bash
kind delete cluster --name soma-agent-hub && \
kind create cluster --name soma-agent-hub --config=kind-cluster-persistent.yaml && \
kubectl apply -f k8s/local/persistence.yaml && \
kubectl create namespace soma-agent-hub && kubectl create namespace observability && \
make build-changed && ./scripts/generate-mtls.sh && \
helm upgrade --install soma-agent-hub ./k8s/helm/soma-agent \
    --namespace soma-agent-hub -f ./k8s/helm/soma-agent/values.yaml -f ./k8s/helm/soma-agent/values-dev.yaml \
    --set global.imageTag=$(git rev-parse --short HEAD)
```

---

## 📚 Further Reading
- **[CONTRIBUTING.md](CONTRIBUTING.md)** – development workflow, testing, PR process.
- **[docs/helm-values.md](docs/helm-values.md)** – exhaustive Helm values reference.
- **[docs/ci-cd.md](docs/ci-cd.md)** – CI pipeline overview.
- **[docs/troubleshooting.md](docs/troubleshooting.md)** – common issues and fixes.
- **[docs/release.md](docs/release.md)** – release and versioning process.
- **[docs/glossary.md](docs/glossary.md)** – glossary of terms.

---

*Happy hacking!* 🚀# Deployment Guide for SomaAgentHub

This document provides a **complete, step‑by‑step** guide to get the SomaAgentHub stack up and running on a local development machine using **Kind** (Kubernetes in Docker). It assumes you have already satisfied the prerequisites listed in the [CONTRIBUTING guide](CONTRIBUTING.md).

---

## 1️⃣ Prerequisites (quick recap)
- **Docker Desktop** (or Docker Engine) with at least **8 GB RAM**.
- **Python 3.11+** (for the helper scripts).
- **kubectl** – the Kubernetes CLI.
- **Kind** – `brew install kind` (macOS) or via your package manager.
- **Helm 3** – `brew install helm`.
- **Make** – usually pre‑installed on macOS/Linux.
- (Optional) **VS Code** with the Remote Containers extension for a full dev environment.

---

## 2️⃣ Create a Kind cluster (or reuse an existing one)
```bash
# Delete any stale cluster first (safe – it will be recreated)
kind delete cluster --name soma-agent-hub || true

# Create a fresh persistent Kind cluster
kind create cluster --name soma-agent-hub \
    --config=kind-cluster-persistent.yaml
```
The `kind-cluster-persistent.yaml` file configures a storage class and a persistent volume that the chart expects.

> **Tip**: After creation, verify the context:
```bash
kubectl cluster-info --context kind-soma-agent-hub
```

---

## 3️⃣ Apply the persistent volume claim
```bash
kubectl apply -f k8s/local/persistence.yaml
```
You should see `persistentvolume/local-persistent-storage` created.

---

## 4️⃣ Create the required namespaces
```bash
kubectl create namespace soma-agent-hub || true
kubectl create namespace observability || true
```
Both namespaces are used by the Helm chart (the main release lives in `soma-agent-hub`).

---

## 5️⃣ Build and load Docker images
The **make** target `start-cluster` already runs this step, but you can run it manually if you only need to rebuild images:
```bash
# Build only images that have changed (fast)
make build-changed
```
All images are tagged as `somaagent/<service>:latest-<git‑sha>` and automatically loaded into the Kind node.

---

## 6️⃣ (Optional) Generate a self‑signed mTLS certificate
If you want mutual TLS between pods, generate the secret **before** installing the chart:
```bash
./scripts/generate-mtls.sh
```
The script creates a secret named `soma-mtls` in the `soma-agent-hub` namespace and prints a reminder to re‑run the Helm install.

---

## 7️⃣ Deploy the Helm chart
```bash
helm upgrade --install soma-agent-hub ./k8s/helm/soma-agent \
    --namespace soma-agent-hub \
    -f ./k8s/helm/soma-agent/values.yaml \
    -f ./k8s/helm/soma-agent/values-dev.yaml \
    --set global.imageTag=$(git rev-parse --short HEAD)
```
**Explanation of flags**
- `upgrade --install` – creates the release if it does not exist.
- `-f values.yaml` – base values.
- `-f values-dev.yaml` – development‑specific overrides (e.g., lower replica counts).
- `--set global.imageTag=…` – pins the images to the exact Git commit you just built.

---

## 8️⃣ Verify the deployment
```bash
# List pods – they should all be in the Running state
kubectl get pods -n soma-agent-hub

# Check the services are exposed
kubectl get svc -n soma-agent-hub
```
You can also watch the logs of a specific component, for example the gateway:
```bash
kubectl logs -f -n soma-agent-hub -l app=gateway-api
```

---

## 9️⃣ Port‑forward the gateway (optional, for local API testing)
```bash
make port-forward-gateway LOCAL=8080 REMOTE=10000
```
Now you can reach the gateway at `http://localhost:8080/healthz` or any other endpoint.

---

## 🔟 Optional Features
| Feature | How to enable |
|---------|---------------|
| **mTLS** | Run `./scripts/generate-mtls.sh` **before** the Helm install and keep `mtls.enabled: true` in `values.yaml`. |
| **ServiceMonitors** (Prometheus) | Set `serviceMonitors.enabled: true` in `values.yaml` and install the Prometheus‑Operator (`helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack`). |
| **Ingress** | Un‑comment and configure the `ingress:` block in `values.yaml`, then set `ingress.enabled: true`. |
| **Additional services** (e.g., `slm-service`, `policy-engine`) | Change `services.<name>.enabled: true` in `values.yaml` and ensure the Docker image exists (run `make build-changed`). |

---

## 📌 Quick One‑Liner (for seasoned users)
```bash
kind delete cluster --name soma-agent-hub && \
kind create cluster --name soma-agent-hub --config=kind-cluster-persistent.yaml && \
kubectl apply -f k8s/local/persistence.yaml && \
kubectl create namespace soma-agent-hub && kubectl create namespace observability && \
make build-changed && ./scripts/generate-mtls.sh && \
helm upgrade --install soma-agent-hub ./k8s/helm/soma-agent \
    --namespace soma-agent-hub -f ./k8s/helm/soma-agent/values.yaml -f ./k8s/helm/soma-agent/values-dev.yaml \
    --set global.imageTag=$(git rev-parse --short HEAD)
```

---

## 📚 Further Reading
- **CONTRIBUTING.md** – detailed developer workflow, testing, and contribution steps.
- **README.md** – high‑level project overview and architecture.
- **docs/** – in‑depth design docs, runbooks, and troubleshooting guides.

---

*Happy hacking! 🚀*