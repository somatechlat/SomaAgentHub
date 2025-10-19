# SomaAgentHub Cluster Port Allocation

**Standardized Port Range: 10000-10099**

All SomaAgentHub services use the 10000+ port range for consistency and easy management.

## Core Application Services (10000-10009)

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **Gateway API** | 10000 | Public ingress, wizard flows | ✅ Active |
| **Orchestrator** | 10001 | Workflow coordination | ✅ Active |
| **Identity Service** | 10002 | Authentication, authorization | ✅ Active |
| **Redis** | 10003 | Caching, sessions | ✅ Active |
| **App PostgreSQL** | 10004 | Application database | ✅ Active |
| **Qdrant** | 10005 | Vector database | ✅ Active |
| **ClickHouse** | 10006 | Analytics database | ✅ Active |
| **MinIO API** | 10007 | Object storage API | ✅ Active |
| **MinIO Console** | 10008 | Object storage console | ✅ Active |
| **Temporal Server** | 10009 | Workflow engine | ✅ Active |

## Observability Stack (10010-10019)

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **Prometheus** | 10010 | Metrics collection | ✅ Active |
| **Grafana** | 10011 | Visualization dashboards | ✅ Active |
| **Loki** | 10012 | Log aggregation | 🔄 Optional |
| **Tempo OTLP gRPC** | 10013 | Distributed tracing | 🔄 Optional |
| **Tempo OTLP HTTP** | 10014 | Distributed tracing | 🔄 Optional |
| **OTEL gRPC** | 10015 | OpenTelemetry collector | 🔄 Optional |
| **OTEL HTTP** | 10016 | OpenTelemetry collector | 🔄 Optional |
| **OTEL Prometheus** | 10017 | OpenTelemetry metrics | 🔄 Optional |
| *Reserved* | 10018 | Future observability | 🔄 Reserved |
| *Reserved* | 10019 | Future observability | 🔄 Reserved |

## Optional Services (10020-10029)

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **Policy Engine** | 10020 | Governance, compliance | 🔄 Optional |
| **Memory Gateway** | 10021 | Vector storage gateway | 🔄 Optional |
| **SLM Service** | 10022 | Small Language Models | 🔄 Optional |
| **Analytics Service** | 10023 | Advanced analytics | 🔄 Optional |
| **Constitution Service** | 10024 | Policy constitution | 🔄 Optional |
| **Billing Service** | 10025 | Usage tracking | 🔄 Optional |
| **Notification Service** | 10026 | Alerts and notifications | 🔄 Optional |
| **Tool Service** | 10027 | External integrations | 🔄 Optional |
| *Reserved* | 10028 | Future services | 🔄 Reserved |
| *Reserved* | 10029 | Future services | 🔄 Reserved |

## Security & Infrastructure (10030-10039)

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **Vault** | 10030 | Secrets management | 🔄 Optional |
| **OPA** | 10031 | Policy enforcement | 🔄 Optional |
| **SPIFFE/SPIRE** | 10032 | Identity framework | 🔄 Optional |
| *Reserved* | 10033-10039 | Future security | 🔄 Reserved |

## External Integrations (10040-10099)

Reserved for future external service integrations and custom extensions.

## Migration Notes

**Previous Port Allocations:**
- Temporal Server: `7233` → `10009` ✅ **MIGRATED**

**Configuration Updates Required:**
- [x] `.env.template` - Updated TEMPORAL_PORT=10009
- [x] `.env` - Updated TEMPORAL_HOST=temporal-server:10009
- [x] `docker-compose.yml` - Added port mapping 10009:7233
- [x] `services/orchestrator/app/core/config.py` - Updated default port
- [x] `services/mao-service/worker.py` - Updated default port
- [x] `services/mao-service/app/main.py` - Updated default port
- [x] `services/orchestrator/temporal_worker.py` - Updated default port
- [x] `PORT_REFERENCE.md` - Updated documentation
- [x] `.amazonq/rules/memory-bank/tech.md` - Updated tech docs

## Deployment Commands

**Restart with New Port Configuration:**
```bash
# Stop current services
docker-compose down

# Start with new port allocation
docker-compose up -d

# Verify all services are healthy
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

**Health Check Commands:**
```bash
# Core services
curl -f http://localhost:10000/health  # Gateway API
curl -f http://localhost:10001/ready   # Orchestrator
curl -f http://localhost:10002/health  # Identity Service

# Infrastructure
redis-cli -h localhost -p 10003 ping   # Redis
psql -h localhost -p 10004 -U somaagent -d somaagent -c "SELECT 1;"  # PostgreSQL

# Temporal (new port)
tctl --address localhost:10009 cluster health  # Temporal
```

## Benefits of Standardized Port Range

1. **Consistency** - All services use 10000+ range
2. **Easy Management** - Clear port allocation strategy
3. **Firewall Rules** - Simple to configure (allow 10000-10099)
4. **Documentation** - Clear mapping between services and ports
5. **Scalability** - Room for 100 services in the range
6. **Conflict Avoidance** - No conflicts with system ports (0-1023) or common services

---

**Status: ✅ Ready for Redeployment**

All port configurations have been updated to use the standardized 10000+ range.