# SomaAgentHub Port Reference

**CANONICAL PORT MAPPING - Single Source of Truth**

This document defines the official port allocation for all SomaAgentHub services.

## Port Range: 10000-10099

### Core Application Services (10000-10019)
| Service | Port | Container Port | Description |
|---------|------|----------------|-------------|
| **gateway-api** | 10000 | 10000 | Main API gateway, public ingress |
| **orchestrator** | 10001 | 10001 | Workflow coordination service |
| **identity-service** | 10002 | 10002 | Authentication & JWT tokens |
| **redis** | 10003 | 6379 | Cache and session storage |
| **app-postgres** | 10004 | 5432 | Application database |
| **qdrant** | 10005 | 6333 | Vector database |
| **clickhouse** | 10006 | 8123 | Analytics database |
| **minio-api** | 10007 | 9000 | Object storage API |
| **minio-console** | 10008 | 9001 | MinIO web console |
| **vault** | 10009 | 8200 | Secrets management |

### Observability Stack (10010-10019)
| Service | Port | Container Port | Description |
|---------|------|----------------|-------------|
| **prometheus** | 10010 | 9090 | Metrics collection |
| **grafana** | 10011 | 3000 | Metrics visualization |
| **loki** | 10012 | 3100 | Log aggregation |
| **tempo-grpc** | 10013 | 4317 | Tracing (gRPC) |
| **tempo-http** | 10014 | 4318 | Tracing (HTTP) |
| **otel-grpc** | 10015 | 4317 | OpenTelemetry (gRPC) |
| **otel-http** | 10016 | 4318 | OpenTelemetry (HTTP) |
| **otel-prometheus** | 10017 | 8888 | OTel Prometheus metrics |

### Optional Services (10020+)
| Service | Port | Container Port | Description |
|---------|------|----------------|-------------|
| **policy-engine** | 10020 | 10020 | Policy enforcement |
| **memory-gateway** | 10021 | 10021 | Memory & RAG service |
| **slm-service** | 10022 | 10022 | Small Language Models |
| **analytics-service** | 10023 | 10023 | Analytics processing |
| **constitution-service** | 10024 | 10024 | Governance framework |
| **billing-service** | 10025 | 10025 | Usage tracking |
| **notification-service** | 10026 | 10026 | Event notifications |

### Internal Services (No External Ports)
| Service | Container Port | Description |
|---------|----------------|-------------|
| **temporal-server** | 10009 | Workflow engine (internal) |
| **temporal-postgres** | 5432 | Temporal database (internal) |

## Environment Variables

All ports are configurable via environment variables in `.env`:

```bash
# Core Services
GATEWAY_API_PORT=10000
ORCHESTRATOR_PORT=10001
IDENTITY_SERVICE_PORT=10002
REDIS_PORT=10003
APP_POSTGRES_PORT=10004

# Observability
PROMETHEUS_PORT=10010
GRAFANA_PORT=10011
LOKI_PORT=10012

# Optional Services
POLICY_ENGINE_PORT=10020
MEMORY_GATEWAY_PORT=10021
SLM_SERVICE_PORT=10022
```

## Service URLs (Internal Docker Network)

Services communicate internally using container names and internal ports:

```bash
GATEWAY_API_URL=http://gateway-api:10000
ORCHESTRATOR_URL=http://orchestrator:10001
IDENTITY_SERVICE_URL=http://identity-service:10002
REDIS_URL=redis://redis:6379/0
TEMPORAL_HOST=temporal-server:10009
```

## Access URLs (External)

From your local machine:

```bash
# Core Services
curl http://localhost:10000/health  # Gateway API
curl http://localhost:10001/ready   # Orchestrator
curl http://localhost:10002/health  # Identity Service

# Observability
open http://localhost:10010         # Prometheus
open http://localhost:10011         # Grafana
open http://localhost:10009         # Vault

# Storage
open http://localhost:10008         # MinIO Console
```

## Port Conflicts

If you have port conflicts, update the `.env` file:

```bash
# Example: If port 10000 is in use
GATEWAY_API_PORT=11000
```

## Validation

Test all ports are accessible:

```bash
# Check if ports are free
for port in {10000..10026}; do
  nc -z localhost $port && echo "Port $port is in use" || echo "Port $port is free"
done
```

---

**Last Updated:** October 18, 2025  
**Maintained By:** SomaAgentHub Platform Team