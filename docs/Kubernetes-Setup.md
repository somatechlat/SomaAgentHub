# Kubernetes Setup

> ⚠️ WE DO NOT MOCK, WE DO NOT IMITATE, WE DO NOT USE BYPASSES OR FAKE VALUES. This guide deploys real services.

Last Updated: October 9, 2025

## Namespaces
- App namespace: `soma-agent-hub`
- Observability namespace (optional): `observability`

## Install Helm chart
```bash
helm upgrade --install soma-agent-hub k8s/helm/soma-agent -n soma-agent-hub --create-namespace --wait --timeout 180s
```

## Customize values
Create `values.override.yaml`:
```yaml
global:
  namespace: soma-agent-hub
  imagePullPolicy: IfNotPresent

services:
  gateway-api:
    enabled: true
    image: "somaagent/soma-gateway-api:latest"
    port: 8080
    nodePort: 30080  # change to ClusterIP + Ingress in production
  slm-service:
    enabled: true
    image: "somaagent/soma-slm-service:latest"
    port: 1001
```
Apply:
```bash
helm upgrade --install soma-agent-hub k8s/helm/soma-agent -n soma-agent-hub -f values.override.yaml --wait
```

## Ingress (production)
- Disable NodePort for gateway and configure Ingress controller (nginx, traefik, etc.)
- Add TLS via cert-manager.

## Resources & scaling
- Set `resources` per service in values to request CPU/memory and set limits.
- Use HPA if needed.

## Observability
- Services expose /metrics by default.
- If using Prometheus Operator, add ServiceMonitors and scrape selectors.

```mermaid
flowchart TB
  subgraph Namespace: soma-agent-hub
    GW[Service: gateway-api (NodePort 30080)]
    SLM[Service: slm-service (ClusterIP 1001)]
    GW_DEP[Deployment: gateway-api]
    SLM_DEP[Deployment: slm-service]
  end
  GW_DEP --> GW
  SLM_DEP --> SLM
```
