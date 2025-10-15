# SomaAgentHub Helm Chart

This Helm chart packages the core SomaAgentHub services for Kubernetes deployment.

## Chart Structure

| Path | Purpose |
| --- | --- |
| `Chart.yaml` | Chart metadata (name, version, dependencies). |
| `values.yaml` | Default configuration values. |
| `templates/` | Kubernetes resource templates (deployments, services, ServiceMonitors, secrets). |
| `templates/configmaps/` | Shared configuration for services. |

## Requirements

- Kubernetes 1.24+
- Helm 3.10+
- Pre-created secrets referenced by services (`somaagent-secrets`, gateway JWT, database credentials).

## Installing the Chart

```bash
helm upgrade --install soma-agent ./k8s/helm/soma-agent \
  --namespace soma-agent-hub --create-namespace \
  --set global.imageRegistry=<registry> \
  --set global.imageTag=<tag>
```

Set service-specific overrides:
```bash
helm upgrade soma-agent ./k8s/helm/soma-agent \
  --namespace soma-agent-hub \
  --reuse-values \
  --set gateway.replicas=2 \
  --set orchestrator.temporal.host=temporal-frontend.somaagent:7233
```

## Key Values

| Value | Description |
| --- | --- |
| `global.imageRegistry` | Registry hosting service images. |
| `global.imageTag` | Image tag applied to all services. |
| `gateway.*` | Gateway API deployment configuration (replicas, env vars, probes). |
| `orchestrator.*` | Orchestrator config including Temporal target and worker settings. |
| `policyEngine.*` | Policy engine configuration (Redis, constitution service). |
| `identity.*` | Identity service database credentials and JWT settings. |
| `monitoring.enabled` | Toggle ServiceMonitor creation. |

Refer to `values.yaml` for full list of configurable options.

## Development Workflow

1. Update templates or values as needed.
2. Run `helm lint k8s/helm/soma-agent` to catch syntax issues.
3. Render manifests for inspection:
   ```bash
   helm template soma-agent ./k8s/helm/soma-agent --namespace soma-agent-hub
   ```
4. Document changes in `docs/Kubernetes-Setup.md` and runbook.

## Versioning

- Increment `Chart.yaml` `version` and `appVersion` when releasing.
- Tag chart releases in Git for traceability (`helm package` optional for distribution).

## Testing

- Use `ct lint` (Chart Testing) in CI (add config under `.github/` when ready).
- Deploy to Kind via `make start-cluster` to validate end-to-end.

For questions, contact Platform Ops (`#soma-ops`).
