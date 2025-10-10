# Observability Guide

> ⚠️ WE DO NOT MOCK, WE DO NOT IMITATE, WE DO NOT USE BYPASSES OR FAKE VALUES. All observability is real.

Last Updated: October 9, 2025

## Metrics
- All services expose /metrics.
- See [Metrics_Reference.md](Metrics_Reference.md) for the metrics catalog.

## Quick verification
```bash
./scripts/verify-instrumentation.sh
```

## Prometheus Operator (optional)
- Install kube-prometheus-stack and create ServiceMonitors for services.

## Logs
- Loki can be deployed (see `k8s/loki-deployment.yaml`).
- Use `kubectl logs` or port-forward Loki and use clients.
