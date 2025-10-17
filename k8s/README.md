# Kubernetes Tooling

**Deploy SomaAgentHub with Helm charts and monitoring add-ons**

> The `k8s/` directory houses the Helm chart, monitoring manifests, and supplemental resources for Kubernetes-based deployments.

---

## Structure

| Path | Description |
| --- | --- |
| `helm/soma-agent/` | Primary Helm chart bundling gateway, orchestrator, policy engine, identity, and supporting services. |
| `monitoring/` | ServiceMonitors, alerting rules, and Grafana dashboard configs. |
| `airflow-deployment.yaml` | Example deployment for Airflow integration. |
| `flink-deployment.yaml` | Example deployment for streaming workloads. |
| `kind-storageclass.yaml` | StorageClass for local Kind clusters. |
| `namespace.yaml` | Canonical namespace definitions. |

---

## Helm Chart Highlights

- **Global Values**: Set registry, tag, and namespace defaults via `global.*` values.
- **Per-Service Overrides**: Each service (gateway, orchestrator, policy-engine, identity, etc.) exposes toggleable replicas, env vars, and resources.
- **Observability**: Creates ServiceMonitors when `monitoring.enabled=true`.
- **Secrets Management**: Pulls from Kubernetes secrets created ahead of chart installation.

### Installation
```bash
helm upgrade --install soma-agent ./k8s/helm/soma-agent \
  --namespace soma-agent-hub --create-namespace \
  --set global.imageRegistry=ghcr.io/somatechlat \
  --set global.imageTag=$(git rev-parse --short HEAD)
```

---

## Monitoring Assets

- `monitoring/servicemonitors.yaml` — scrapes key services with Prometheus.
- Extend alerting by adding rules in `monitoring/alerts/` (create if missing) and update Grafana dashboards in `monitoring/dashboards/`.

---

## Conventions

- All manifests remain environment-agnostic; use Helm values or Kustomize overlays for environment-specific settings.
- Follow naming convention `soma-agent-hub` for namespaces and labels (`app.kubernetes.io/part-of=soma-agent`).
- Update documentation (`docs/technical-manual/deployment.md`, runbooks under `docs/technical-manual/runbooks/`) whenever chart behavior changes.

---

For chart versioning and release packaging, coordinate with Platform Ops (`#soma-ops`).
