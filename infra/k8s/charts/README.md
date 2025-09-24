# SomaStack Helm Scaffold

This Helm chart (`infra/k8s/charts/somagent`) is a starting point for deploying the gateway, SLM service, and notification orchestrator. Extend it with additional deployments (MAO, settings, etc.), secrets, and ingress.

## Usage
```
helm install somagent infra/k8s/charts/somagent \
  --set image.repository=<your-repo> \
  --set image.tag=<version>
```

Add secrets (certificates, API keys) via `values.yaml` or Kubernetes secrets before production use.
