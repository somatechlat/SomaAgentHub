# Local Runbook (Prod-like Development)

## Prerequisites
- Docker, Kind, Helm

## Create cluster (optional)
- Create a Kind cluster named `soma-dev` if you don't already have one.

## Deploy shared infra
- Namespace: `soma-infra`
- Chart: `infra/helm/soma-infra`
- Values: `values-dev.yaml`

## Deploy application services
- Namespace: `soma-agent-hub`
- Chart: `k8s/helm/soma-agent`
- Values: `k8s/helm/soma-agent/values-dev.yaml`

## Verify
- Check pods Ready in both namespaces.
- Gateway: `/health`, `/ready`
- Identity: `/health`, `/ready`
- Orchestrator: `/health`, `/ready`
- SLM Service: `/health`, `/ready`

## Optional
- Enable Prometheus/Grafana in `infra/helm/soma-infra/values-dev.yaml`.
- Enable ServiceMonitor in app values and OTel exporters via env.
