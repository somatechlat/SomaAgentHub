# Production Docker Compose Setup for SomaAgentHub

**macOS-optimized, production-grade local development environment with realistic resource allocation and configurations.**

---

## 1. Overview

This guide provides a **production-grade local development setup** using Docker Compose. All settings reflect production requirements (resource limits, logging, metrics, security) while being runnable on a development machine.

**Key Principles**:
- ✅ Real resource limits (not bare minimum)
- ✅ Production logging & metrics from day 1
- ✅ Secure defaults (no mocking)
- ✅ Actual database optimization
- ✅ Health checks on all services
- ✅ Observable & debuggable

---

## 2. System Requirements

### 2.1 Minimum Specifications (macOS)

```
- macOS 12.0 or later (Intel or M1/M2/M3 chip)
- Docker Desktop 24.0+ (or Docker Engine v24 + Docker Compose v2)
- 8GB RAM dedicated to Docker
- 30GB free SSD space
- Python 3.11+
```

### 2.2 Recommended Specifications

```
- macOS 13.0 or later
- Docker Desktop 25.0+ with 16GB RAM allocated
- 50GB SSD free space (for volumes + cache)
- M2 Pro/Max or equivalent CPU
- Parallel execution (fan cooling recommended)
```

### 2.3 Docker Desktop Configuration (macOS)

```bash
# Configure Docker Desktop for optimal performance
# GUI: Docker → Preferences → Resources

Resources:
  CPUs: 6+ cores (or max available)
  Memory: 12-16 GB (minimum 8GB)
  Swap: 2GB
  Disk Image Size: 50GB+
  File Sharing: Enable for /Users/

Network:
  DNS: 8.8.8.8

Advanced:
  Enable VirtioFS: Checked (improves volume performance)
```

---

## 3. Quick Start (5 Minutes)

```bash
# 1. Clone and enter directory
git clone https://github.com/somatechlat/somaAgentHub.git
cd somaAgentHub

# 2. Create Python environment
python3.11 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements-dev.txt --upgrade

# 4. Start full stack (pulls images + creates volumes)
make dev-up

# 5. Verify (open new terminal, keep services running in first)
docker compose ps

# 6. Bootstrap secrets
bash scripts/bootstrap-vault.sh

# 7. Run smoke tests
make k8s-smoke HOST="localhost:10000"
```

---

## 4. Production-Grade Service Configuration

### 4.1 Resource Allocation

```yaml
# docker-compose.yml resource settings
services:
  temporal:
    # Temporal is memory-intensive for workflow history
    mem_limit: 1g
    cpus: '0.75'
    
  temporal-postgres:
    # Database for workflow state
    mem_limit: 512m
    cpus: '0.5'
    
  soma-postgres:
    # Application data
    mem_limit: 768m
    cpus: '0.5'
    
  soma-redis:
    # Caching + sessions
    mem_limit: 512m
    cpus: '0.25'
    
  soma-qdrant:
    # Vector embeddings (RAG)
    mem_limit: 1g
    cpus: '0.75'
    
  soma-clickhouse:
    # Analytics / events
    mem_limit: 1g
    cpus: '0.75'
    
  soma-minio:
    # S3 object storage
    mem_limit: 512m
    cpus: '0.5'

# Total: ~6.5GB RAM, 4.75 CPU cores
```

### 4.2 PostgreSQL Production Settings

```env
# Optimized for 768MB memory allocation
POSTGRES_INITDB_ARGS=-c max_connections=300 \
  -c shared_buffers=192MB \
  -c effective_cache_size=576MB \
  -c maintenance_work_mem=48MB \
  -c checkpoint_completion_target=0.9 \
  -c wal_buffers=16MB \
  -c default_statistics_target=100 \
  -c random_page_cost=1.1 \
  -c effective_io_concurrency=200 \
  -c work_mem=640kB
```

### 4.3 Redis Production Configuration

```bash
# Redis maxmemory policy (LRU eviction)
redis-server --maxmemory 512mb \
  --maxmemory-policy allkeys-lru \
  --loglevel notice \
  --appendonly yes \
  --appendfilename "appendonly.aof"
```

### 4.4 ClickHouse Tuning

```xml
<!-- production_like.xml config -->
<yandex>
  <max_connections>300</max_connections>
  <max_concurrent_queries>100</max_concurrent_queries>
  <max_execute_query_memory>1073741824</max_execute_query_memory>
  
  <logger>
    <level>notice</level>
    <log>/var/log/clickhouse-server/clickhouse-server.log</log>
    <errorlog>/var/log/clickhouse-server/clickhouse-server.err.log</errorlog>
  </logger>
</yandex>
```

---

## 5. Environment Variables (Production Defaults)

Create `.env` file in project root:

```bash
# Deployment mode
DEPLOYMENT_MODE=production

# Application
APP_ENV=local-prod
DEBUG=false
LOG_LEVEL=info

# API Gateway
GATEWAY_PORT=10000
GATEWAY_JWT_SECRET=$(openssl rand -base64 32)
GATEWAY_CORS_ENABLED=true
GATEWAY_RATE_LIMIT=1000/minute

# Orchestrator
ORCHESTRATOR_PORT=10001
ORCHESTRATOR_WORKERS=4
TEMPORAL_HOST=temporal:7233
TEMPORAL_NAMESPACE=default

# Database
POSTGRES_HOST=soma-postgres
POSTGRES_PORT=5432
POSTGRES_DB=somaagent
POSTGRES_USER=somaagent
POSTGRES_PASSWORD=$(openssl rand -base64 24)
POSTGRES_MAX_CONNECTIONS=300

# Redis
REDIS_HOST=soma-redis
REDIS_PORT=6379
REDIS_PASSWORD=$(openssl rand -base64 24)
REDIS_DB=0

# Observability
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
PROMETHEUS_SCRAPE_INTERVAL=30s
LOKI_URL=http://loki:3100

# Vault (Secrets Management)
VAULT_ADDR=http://vault:8200
VAULT_NAMESPACE=somaagent
VAULT_SKIP_VERIFY=false

# Logging
LOG_FORMAT=json
LOG_OUTPUT=stdout,file
LOG_FILE_DIR=/var/log/somaagent

# Metrics
METRICS_ENABLED=true
METRICS_PORT=9090
METRICS_SCRAPE_DISABLED=false
```

---

## 6. Full Stack Startup Procedure

### 6.1 Initialize Environment

```bash
cd somaAgentHub

# Create directories for volumes + logs
mkdir -p ./volumes/{postgres,redis,qdrant,clickhouse,minio,vault}
mkdir -p ./.logs

# Generate secure passwords
export POSTGRES_PASSWORD=$(openssl rand -base64 24)
export REDIS_PASSWORD=$(openssl rand -base64 24)
export JWT_SECRET=$(openssl rand -base64 32)

# Create .env with above values
cat > .env << EOF
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
REDIS_PASSWORD=$REDIS_PASSWORD
GATEWAY_JWT_SECRET=$JWT_SECRET
DEPLOYMENT_MODE=production
LOG_LEVEL=info
OTEL_ENABLED=true
EOF
```

### 6.2 Start Infrastructure Services

```bash
# Terminal 1: Start Temporal + supporting services
docker compose -f infra/temporal/docker-compose.yml \
  -f infra/temporal/docker-compose.prod.yml up -d

# Wait for Temporal to be ready
docker compose logs temporal | grep "Temporal server started"

# Terminal 2: Start data services (databases, cache, storage)
docker compose -f infra/postgres/docker-compose.yml \
  -f infra/redis/docker-compose.yml \
  -f infra/qdrant/docker-compose.yml \
  -f infra/clickhouse/docker-compose.yml \
  -f infra/minio/docker-compose.yml up -d

# Wait for all services to initialize
sleep 30
docker compose ps --format table
```

### 6.3 Initialize Databases

```bash
# Terminal 3: Run migration scripts
bash scripts/init-postgres.sh
bash scripts/init-clickhouse.sh
bash scripts/init-qdrant.sh

# Create MinIO buckets
bash scripts/init-minio.sh

# Bootstrap Vault with secrets
bash scripts/bootstrap-vault.sh
```

### 6.4 Start Application Services

```bash
# Terminal 4: Start core microservices
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Start Gateway API
(cd services/gateway-api && python -m uvicorn app.main:app \
  --host 0.0.0.0 --port 10000 --reload --log-level info) &

# Start Orchestrator  
(cd services/orchestrator && python -m uvicorn app.main:app \
  --host 0.0.0.0 --port 10001 --reload --log-level info) &

# Start Identity Service
(cd services/identity-service && python -m uvicorn app.main:app \
  --host 0.0.0.0 --port 10002 --reload --log-level info) &

# Start Policy Engine
(cd services/policy-engine && python -m uvicorn app.main:app \
  --host 0.0.0.0 --port 10020 --reload --log-level info) &
```

### 6.5 Verify Full Stack

```bash
# Terminal 5: Verification
bash scripts/verify-instrumentation.sh

# Expected output:
# ✅ Gateway API (10000): responding
# ✅ Orchestrator (10001): responding
# ✅ Identity (10002): responding
# ✅ Temporal (7233): responding
# ✅ PostgreSQL (5432): responding
# ✅ Redis (6379): responding
# ✅ Qdrant (6333): responding
# ✅ ClickHouse (8123): responding
# ✅ MinIO (9000): responding
# ✅ Vault (8200): responding
# ✅ All services healthy!
```

---

## 7. Health Checks & Monitoring

### 7.1 Real-Time Health Dashboard

```bash
# Monitor all services in one view
watch -n 5 'docker compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"'
```

### 7.2 Service Health Endpoints

```bash
# Gateway API health
curl -s http://localhost:10000/health | jq .

# Orchestrator health
curl -s http://localhost:10001/health | jq .

# Temporal health
curl -s http://localhost:7233/health 2>/dev/null && echo "Temporal: OK"

# PostgreSQL health
psql postgresql://somaagent:$POSTGRES_PASSWORD@localhost:5432/somaagent \
  -c "SELECT version();"

# Redis health
redis-cli -a $REDIS_PASSWORD ping
```

### 7.3 Performance Metrics

```bash
# CPU usage per service
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Memory consumption
docker compose exec soma-postgres \
  psql -U somaagent -d somaagent -c "SELECT sum(relpages) * 8 as size_mb FROM pg_class;"

# Redis memory usage
docker compose exec soma-redis redis-cli info memory | grep used_memory_human
```

---

## 8. Development Workflows

### 8.1 Run Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (with services running)
pytest tests/integration/ -v --tb=short

# E2E tests
pytest tests/e2e/ -v --timeout=60

# Coverage report
pytest --cov=services --cov-report=html
```

### 8.2 Debug a Service

```bash
# Stream logs from specific service
docker compose logs -f soma-postgres

# Tail application logs
tail -f .logs/orchestrator.log

# Interactive debugging
docker compose exec soma-postgres bash
psql -U somaagent -d somaagent

# View environment in running container
docker compose exec gateway-api env | grep -i log
```

### 8.3 Database Backups (Development)

```bash
# Backup PostgreSQL
docker compose exec soma-postgres pg_dump \
  -U somaagent somaagent > backup.sql

# Restore PostgreSQL
docker compose exec -T soma-postgres psql \
  -U somaagent somaagent < backup.sql
```

---

## 9. Troubleshooting

### 9.1 "Out of Memory" Errors

```bash
# Increase Docker Desktop memory allocation
# Settings → Resources → Memory: 16GB

# Check current limits
docker stats --no-stream

# If services still OOM:
# 1. Reduce replicas
# 2. Lower vector DB dimensions
# 3. Prune old volumes: docker volume prune
```

### 9.2 Port Conflicts

```bash
# Find service using port 5432
lsof -i :5432

# Kill that process (if safe)
kill -9 <PID>

# Or change port in docker-compose.override.yml
echo 'services:
  soma-postgres:
    ports:
      - "5433:5432"' > docker-compose.override.yml
```

### 9.3 Slow Performance

```bash
# Check Docker resource usage
docker stats

# Enable VirtioFS (macOS only)
# Settings → Resources → File Sharing Implementation: VirtioFS

# Rebuild from scratch
docker compose down -v
docker system prune -a
docker compose up -d
```

---

## 10. Cleanup

```bash
# Stop services (keep volumes)
docker compose down

# Stop + remove all volumes (wipes data)
docker compose down -v --remove-orphans

# Full system cleanup
docker system prune -a --volumes

# Free up disk space
docker builder prune
```

---

## Next Steps

1. **First Contribution**: See [Onboarding Manual → First Contribution](../onboarding-manual/first-contribution.md)
2. **API Testing**: Import `/api-collections/SomaAgentHub.postman_collection.json` into Postman
3. **Monitoring**: Check Grafana dashboard at `http://localhost:3000`
4. **Logs**: Review structured logs in Loki UI

---

**All configurations verified on macOS 13+ with Docker Desktop 25+. Performance optimized for development machines with 8GB+ RAM.**
