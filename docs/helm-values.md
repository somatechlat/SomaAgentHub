---
title: Helm Values Reference
---

# Helm Values Reference for `soma-agent`

This document provides a concise reference for the **values.yaml** file used by the
`soma-agent` Helm chart. It is intended for developers and operators who need to
customise the deployment of the SomaAgentHub platform.

## Global Settings

```yaml
global:
  imagePullPolicy: IfNotPresent
  namespace: soma-agent-hub
  imageTag: "dev"
  securityContext:
    runAsNonRoot: true
    allowPrivilegeEscalation: false
    readOnlyRootFilesystem: true
    capabilities:
      drop: ["ALL"]
  environment: production
  observability:
    enableOtlp: true
    otlpEndpoint: "http://otel-collector.observability:4317"
  spiffe:
    enabled: true
    trustDomain: "somaagent.io"
    certDir: "/var/run/secrets/spiffe"
    socketPath: "/run/spire/sockets/agent.sock"
    socketMountPath: "/run/spire/sockets"
    hostSocketPath: "/run/spire/sockets"
  resources:
    limits:
      cpu: "500m"
      memory: "512Mi"
    requests:
      cpu: "250m"
      memory: "256Mi"
```

These settings are applied to **all** services unless overridden in the specific
service block.

## Port Definitions

All ports are defined in a single `ports` map, which serves as the source of truth
for both the Helm chart and the Docker‑Compose configuration.

```yaml
ports:
  gateway-api: 10000
  orchestrator: 10001
  identity-service: 10002
  policy-engine: 10020
  memory-gateway: 10021
  # … other services omitted for brevity …
```

Only the **service name** is used in the Helm templates; the chart automatically
links the Service `port` to the corresponding `targetPort` (the container port).

## Service Definitions

Each micro‑service can be enabled/disabled, have its own image, replica count, and
environment variables.  The most common overrides are shown below.

```yaml
services:
  gateway-api:
    enabled: true
    replicaCount: 1
    image: "somaagent/soma-gateway-api"
    envFromSecret: "soma-secrets"
    env:
      - name: ENABLE_OTLP
        value: "true"
      # … additional env vars …

  orchestrator:
    enabled: true
    image: "somaagent/soma-orchestrator"
    env:
      - name: TEMPORAL_ENABLED
        value: "false"

  identity-service:
    enabled: true
    image: "somaagent/identity-service"
    env:
      - name: REDIS_URL
        value: "redis://redis:6379/0"

  policy-engine:
    enabled: true   # <-- optional service now enabled by default
    image: "somaagent/soma-policy-engine"

  memory-gateway:
    enabled: true   # <-- optional service now enabled by default
    # No extra env needed; the service uses the default port mapping
```

### Disabling an Optional Service

If you wish to run the platform without a particular optional component, simply
set `enabled: false` for that service and re‑run the Helm upgrade:

```bash
helm upgrade --install soma-agent-hub ./k8s/helm/soma-agent \
  --set services.memory-gateway.enabled=false \
  --set services.policy-engine.enabled=false
```

## Observability Configuration

The chart includes optional OpenTelemetry, Prometheus, Grafana, Loki and Tempo
components.  Their toggles live under `global.observability` and the dedicated
`opa` section for the policy engine.

## Helm Linting & Upgrade

Use the provided Make targets for convenience:

```bash
make helm-lint      # Validate the chart locally
make helm-upgrade   # Install or upgrade the release
```

---

For a full description of every field, see the **`values.yaml`** file in the
chart directory.
# Helm Values Reference for SomaAgentHub

This file documents every configurable key in `k8s/helm/soma-agent/values.yaml`. The default file is shipped with the chart; the table below describes the purpose, type, and typical values.

## Global Settings
| Key | Description | Default | Notes |
|-----|-------------|---------|-------|
| `global.imagePullPolicy` | Pull policy for all service containers. | `IfNotPresent` | Change to `Always` for CI builds. |
| `global.namespace` | Namespace where the release is installed. | `soma-agent-hub` | Must match the namespace you create. |
| `global.imageTag` | Tag applied to all service images. | `dev` | Usually set to the short git SHA (`$(git rev-parse --short HEAD)`). |
| `global.securityContext` | Pod‑level security context applied to every service. | see file | Enforces non‑root, drop all capabilities, read‑only FS. |
| `global.environment` | Runtime environment identifier. | `production` | Used by services for config selection. |
| `global.observability.enableOtlp` | Enable OpenTelemetry exporter. | `true` | Set to `false` to disable tracing. |
| `global.observability.otlpEndpoint` | OTLP collector endpoint. | `http://otel-collector.observability:4317` | Adjust if collector runs elsewhere. |
| `global.spiffe.*` | SPIFFE configuration for workload identity. | see file | Used by services that integrate with SPIRE. |
| `global.resources` | Default CPU/Memory requests & limits applied to all services. | `{ limits: {cpu: "500m", memory: "512Mi"}, requests: {cpu: "250m", memory: "256Mi"} }` | Individual services can override. |

## Port Definitions (`ports:`)
Each service expects a port defined here. The key name matches the service name used in the chart.

| Service | Port |
|--------|------|
| `gateway-api` | 10000 |
| `orchestrator` | 10001 |
| `identity-service` | 10002 |
| `policy-engine` | 10003 |
| `memory-gateway` | 10004 |
| `llm-hub` | 10005 |
| `tool-service` | 10006 |
| `analytics-service` | 10007 |
| `settings-service` | 10008 |
| `billing-service` | 10009 |
| `constitution-service` | 10010 |
| `task-capsule-repo` | 10011 |
| `jobs` | 10012 |
| `opa` | 8181 |
| *(additional optional services)* | see file |

## OPA Configuration (`opa:`)
| Key | Description | Default |
|-----|-------------|---------|
| `enabled` | Deploy Open Policy Agent. | `true` |
| `image` | Container image for OPA. | `openpolicyagent/opa:latest` |
| `replicaCount` | Number of OPA pods. | `1` |
| `port` | Port OPA listens on. | `8181` |
| `env` | Extra environment variables (list). | `[]` |

## mTLS Configuration (`mtls:`)
| Key | Description | Default |
|-----|-------------|---------|
| `enabled` | Enable mutual TLS between pods. | `true` |
| `secretName` | Name of the Kubernetes secret containing `tls.crt` and `tls.key`. | `soma-mtls` |
| `tlsCrt` / `tlsKey` | Place‑holders that the `generate-mtls.sh` script populates. | `""` |

## Secrets Configuration (`secrets:`)
Controls the `soma-secrets` Kubernetes secret.

| Key | Description | Default |
|-----|-------------|---------|
| `enabled` | Create the secret via the chart. | `true` |
| `name` | Secret name. | `soma-secrets` |
| `generateDevSecrets` | When `false` the chart expects you to provide real secrets. | `false` |
| `identityJwt` / `gatewayJwt` | Placeholder JWT keys for dev. | `""` |

## Service Blocks (`services:`)
Each micro‑service can be enabled/disabled and customized. Below is a sample of the most common fields – the full list lives in `values.yaml`.

### Example – `gateway-api`
```yaml
gateway-api:
  enabled: true
  replicaCount: 1
  image: "somaagent/soma-gateway-api"
  envFromSecret: "soma-secrets"
```
* `enabled` – set to `false` to skip deployment.
* `replicaCount` – number of pod replicas.
* `image` – full image reference; the tag is injected via `global.imageTag`.
* `envFromSecret` – name of a secret whose key‑value pairs become environment variables.

### Example – `identity-service`
```yaml
identity-service:
  enabled: true
  image: "somaagent/identity-service"
  envFromSecret: "soma-secrets"
  env:
    - name: REDIS_URL
      value: "redis://redis:6379/0"
    - name: OIDC_ISSUER_URL
      value: "http://identity-service:{{ index $.Values.ports \"identity-service\" }}"
```
Other services (`orchestrator`, `memory-gateway`, `policy-engine`, etc.) follow the same pattern.

## Ingress (`ingress:`)
Only needed if you expose the gateway via an external load balancer.
```yaml
ingress:
  enabled: false
  # image field retained for compatibility; not used when disabled
  image: "somaagent/gateway-api"
  # add host, tls, annotations as required
```
Set `enabled: true` and fill out the host/TLS fields for production.

## ServiceMonitors (`serviceMonitors:`)
Optional resources for Prometheus‑Operator.
```yaml
serviceMonitors:
  enabled: false
  namespace: ""
  interval: 30s
```
Enable when the Prometheus‑Operator CRDs are installed.

---

**Tip:** When overriding values, create a `values.override.yaml` and pass it to Helm with `-f values.override.yaml`.
