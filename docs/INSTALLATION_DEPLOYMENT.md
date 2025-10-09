# Installation & Deployment (Prometheus + Loki)

Date: 2025-10-08

This guide installs the observability baseline and deploys core components in Kubernetes. Commands are for macOS zsh.

## Prerequisites

- kubectl and Helm installed
- A Kubernetes cluster (Kind/Minikube/EKS)

## Install Prometheus (Grafana disabled)

You can use the provided script or run the Helm command directly.

Script (recommended):

```bash
./scripts/deploy.sh
```

Manual Helm command (example):

```bash
kubectl create namespace observability || true
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  -n observability \
  --set grafana.enabled=false \
  --wait --timeout 10m
```

## Deploy Loki

```bash
kubectl apply -f k8s/loki-deployment.yaml
```

Port-forward if needed:

```bash
kubectl -n observability port-forward svc/loki 3100:3100
```

## ServiceMonitors

```bash
kubectl apply -f k8s/monitoring/servicemonitors.yaml
```

Ensure your services’ Kubernetes Services have the expected labels and expose /metrics.

## Airflow (optional)

```bash
kubectl apply -f k8s/airflow-deployment.yaml
```

Set environment variables for the webserver/scheduler (GATEWAY_URL, LOKI_URL) as shown in the manifest.

## Flink (optional)

```bash
kubectl apply -f k8s/flink-deployment.yaml
```

## Verify

- Prometheus UI (port-forward):

```bash
kubectl -n observability port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090
open http://localhost:9090
```

- Loki: query labels and logs via API or your preferred UI. With port-forward:

```bash
curl -s "http://localhost:3100/loki/api/v1/labels" | jq .
```

For deeper instructions and troubleshooting, see docs/observability/README.md.
