# Cluster Start Runbook

This runbook brings up a complete SomaAgentHub cluster on Kubernetes (Kind for local), deploys core services, and runs quick smoke checks.

Prereqs:
- Docker, kubectl, helm
- Kind (for local) or an existing K8s cluster

## 1) Create Kind cluster (local)

```bash
kind create cluster --name soma-agent-hub --config k8s/kind-storageclass.yaml
kubectl create namespace soma-agent-hub
kubectl create namespace observability
```

## 2) Deploy Observability (optional but recommended)

```bash
kubectl apply -f k8s/loki-deployment.yaml
# Install Prometheus stack via community chart if desired
# helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
# helm install prometheus prometheus-community/kube-prometheus-stack -n observability
```

## 3) Build and load images into Kind

```bash
make build-all
```

If not using Kind, push images to your registry and set proper imagePullSecrets.

## 4) Deploy with Helm

```bash
helm upgrade --install soma-agent-hub ./k8s/helm/soma-agent \
  --namespace soma-agent-hub \
  --set global.imageTag=$(git rev-parse --short HEAD)
```

This installs:
- gateway-api (NodePort 30080)
- slm-service (ClusterIP)

## 5) Port forwarding (local access)

```bash
# Gateway
kubectl -n soma-agent-hub port-forward svc/gateway-api 60000:60000

# Optional: Prometheus
# kubectl -n observability port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090
```

## 6) Smoke checks

```bash
# Gateway health
curl -s http://localhost:60000/v1/health | jq

# Dashboard (checks slm-service health too)
curl -s http://localhost:60000/v1/dashboard/health | jq
```

## 7) Verify Observability

```bash
make verify-observability
```

## Troubleshooting
- If images are not found: use `imagePullPolicy: IfNotPresent` and ensure images are loaded/pushed.
- If ServiceMonitor is missing: install kube-prometheus-stack to enable CRDs.
- If slm-service is not ready: describe pod to review liveness/readiness probe failures.
