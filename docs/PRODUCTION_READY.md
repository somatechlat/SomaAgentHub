# Production readiness checklist

This document contains conservative, high-level steps and Helm values for deploying SomaAgent to a production cluster. It is intended to reduce accidental heavy infra deployment from developer machines and to centralize production defaults.

Quick usage

1. Update the image tag placeholder in `k8s/helm/soma-agent/values.prod.yaml` to your release tag (CI should set this).
2. Render the templates locally to validate:

```bash
helm template soma-agent-hub ./k8s/helm/soma-agent -f k8s/helm/soma-agent/values.prod.yaml
```

3. Install to cluster:

```bash
helm upgrade --install soma-agent-hub ./k8s/helm/soma-agent \
  --namespace soma-agent-hub --create-namespace \
  -f k8s/helm/soma-agent/values.prod.yaml --wait
```

Production checklist

- [ ] Ensure `global.imageTag` is set to an immutable release (sha or semver).
- [ ] Provide secrets via Kubernetes Secrets (`soma-secrets`) and set `secrets.generateDevSecrets=false`.
- [ ] Verify `defaultKafka.enabled` and `kafka.enabled` only when Kafka brokers and storage are provisioned.
- [ ] Ensure `slm-service.enabled` is false unless GPU nodes/PVCs are available; model services require large PVCs and compute.
- [ ] Confirm monitoring stack (Prometheus/Grafana/Loki) namespaces and ServiceMonitors are configured and RBAC exists.
- [ ] Validate network policies, resource quotas, and PodDisruptionBudgets before scaling replicas upward.

Security & operational notes

- Do not use `latest` in production images. Use immutable tags.
- Use centralized secrets manager (Vault or cloud KMS) to populate `soma-secrets` instead of `generateDevSecrets`.
- Prefer subcharts for heavy infra (Kafka/Prometheus/Temporal) so operators can enable only the parts they manage.
