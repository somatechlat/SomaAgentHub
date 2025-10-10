# Soma Stack Architecture (Prod-like for Development)

This document adapts the consolidated architecture to a single local Kind cluster while preserving production semantics.

## Namespaces
- `soma-infra`: shared infra (Redis, Kafka; optional Prometheus/Grafana, OPA, Vault, Etcd)
- `soma-agent-hub`: application services (gateway-api, orchestrator, identity-service, policy-engine, slm-service)

## Shared Infra (dev-sized)
- Redis: 1 replica, no persistence, low resources.
- Kafka (KRaft): 1 broker, no persistence, low resources.
- Optional: Prometheus/Grafana, OPA, Vault, Etcd (disabled by default).

DNS:
- `redis.soma-infra.svc.cluster.local:6379`
- `kafka.soma-infra.svc.cluster.local:9092`

## Application Services
- Gateway API (HTTP 8080)
- Orchestrator (HTTP 1004; Temporal disabled by default)
- Identity (Auth) (HTTP 8000)
- Policy Engine (HTTP 8000)
- SLM Service (HTTP 1001)

## Configuration Strategy
- Common BaseSettings in `common/config/settings.py`.
- K8s Secrets for sensitive values; ConfigMaps for non-sensitive.
- Helm values-dev for local; production via separate values.

## Observability
- Common OpenTelemetry helper; OTLP disabled by default.
- Prometheus optional via infra chart; ServiceMonitor toggles in app chart.

## Deploy (dev)
1. Install infra (dev profile):
   - namespace: soma-infra
2. Install apps (dev profile):
   - namespace: soma-agent-hub
3. Validate `/health` endpoints of gateway, identity, orchestrator, slm.

## Notes
- OPA and Vault are optional in dev; policy-engine remains PDP.
- Future work: SA01↔SB gRPC interface; vector DB integration.
