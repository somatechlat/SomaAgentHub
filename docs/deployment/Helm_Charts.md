# Helm Charts Usage & Customization

Last Updated: October 9, 2025

This guide explains how to deploy SomaAgentHub using the Helm chart under `k8s/helm/soma-agent`.

## Values Overview

Key values in `values.yaml`:

- global.namespace: Target namespace (default: soma-agent-hub)
- services.gateway-api:
  - enabled: true
  - image: somaagent/soma-gateway-api:latest
  - port: 8080
  - nodePort: 30080 (NodePort type for local)
- services.slm-service:
  - enabled: true
  - image: somaagent/soma-slm-service:latest
  - port: 1001

## Templates

- templates/service.yaml: Generates a Service per enabled entry. Gateway is NodePort by default.
- templates/deployment.yaml: Generates a Deployment per enabled entry.

Both templates include standard labels and a legacy `app: <name>` label for compatibility with external selectors.

## Install / Upgrade

```bash
helm upgrade --install soma-agent-hub k8s/helm/soma-agent -n soma-agent-hub --create-namespace --wait --timeout 180s
```

## Verifications

```bash
kubectl -n soma-agent-hub get deploy,svc | grep -E "gateway-api|slm-service"
kubectl -n soma-agent-hub rollout status deploy/gateway-api
kubectl -n soma-agent-hub rollout status deploy/slm-service
```

## Access

- Gateway: NodePort 30080 → 8080 inside cluster; for port-forward: `kubectl -n soma-agent-hub port-forward svc/gateway-api 8080:8080`
- SLM service: ClusterIP 1001; for port-forward: `kubectl -n soma-agent-hub port-forward svc/slm-service 11001:1001`

## Troubleshooting

- If resources are missing after Helm install, ensure no conflicting manually-applied resources exist.
- Check events: `kubectl -n soma-agent-hub get events --sort-by=.lastTimestamp | tail -n 50`
- Validate manifests: `helm get manifest soma-agent-hub -n soma-agent-hub`
