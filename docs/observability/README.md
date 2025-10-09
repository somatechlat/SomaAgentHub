# Observability (Prometheus + Loki)

This repo uses Prometheus for metrics and Loki for logs. Grafana is not used.

## Components
- Prometheus (kube-prometheus-stack, Grafana disabled)
- Loki (single-replica, filesystem)
- OpenTelemetry SDK in services
- Optional python-logging-loki handler (env-driven)

## Deploy

1. Create namespace and install Prometheus (Grafana disabled):

```bash
kubectl create namespace observability || true
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  -n observability \
  --set grafana.enabled=false \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --wait --timeout 5m
```

2. Apply Loki:

```bash
kubectl apply -f k8s/loki-deployment.yaml
```

3. Port-forward locally (optional):

```bash
kubectl port-forward -n observability svc/prometheus-kube-prometheus-prometheus 9090:9090
kubectl port-forward -n observability svc/loki 3100:3100
```

## Service scraping
- ServiceMonitors are in `k8s/monitoring/servicemonitors.yaml`. They target Services with:
  - `labels: { app: <svc>, monitoring: enabled }`
  - a `metrics` port exposing `/metrics`.
- Namespaces covered include `somaagent`, `soma-agent-hub`, and `soma-memory`.

## Enable Loki logging in services
Set `LOKI_URL` to the in-cluster Loki service (the code appends `/loki/api/v1/push`). Examples:

```bash
LOKI_URL=http://loki.observability:3100
```

The services will attach a LokiHandler if the `python-logging-loki` package is present (already included in Airflow image). If not present, services continue with standard logging.

## Quick verification
- Metrics: In Prometheus UI, run:

```
sum by (campaign_id,campaign_name) (campaign_analytics_created_total)
```

- Logs: Query Loki by labels from the orchestrator analytics activity’s `logs_label_hint` (e.g., `{service="orchestrator", campaign_id="cmp-123"}`).

## Notes
- `k8s/monitoring/grafana-dashboards.yaml` was removed/neutralized to avoid Grafana usage.
- Airflow logs to Loki by default via `python-logging-loki`; set `LOKI_URL` in its deployment.
