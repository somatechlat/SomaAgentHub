# Environment Setup Guide

**Get SomaAgentHub running on your local machine with production-grade configuration.**

---

## 📋 Prerequisites

### System Requirements (macOS)
| Component | Requirement | Why |
|-----------|------------|-----|
| **macOS Version** | 12.x or later | Docker Desktop support, Git LFS |
| **CPU Cores** | 4+ cores | Sufficient for 16 microservices + compilation |
| **RAM** | 16 GB minimum, 32 GB recommended | Services configured for production workloads |
| **Disk Space** | 50 GB free (includes Docker images, volumes) | Data services (PostgreSQL, ClickHouse, MinIO) are persistent |
| **Network** | Stable internet connection | Image pulls, dependency downloads |

### Required Software

```bash
# Check versions (run in terminal)
docker --version          # Docker Desktop 24.0+ (includes docker-compose v2)
docker-compose --version  # v2.20.0+
git --version            # 2.40.0+
python3 --version        # 3.11+ (for local development)
make --version           # GNU Make 3.81+
```

**Installation:**
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Docker Desktop (includes docker-compose)
brew install docker
# Then start Docker Desktop from Applications

# Install Git
brew install git

# Install Python 3.11+
brew install python@3.11

# Install GNU Make
brew install make

# Verify all are installed
docker --version && docker-compose --version && git --version && python3 --version
```

---

## 🚀 Quick Start (5 minutes)

### 1. Clone Repository

```bash
cd ~/Documents  # Or your preferred workspace
git clone https://github.com/somatechlat/SomaAgentHub.git
cd SomaAgentHub
```

**Expected output:**
```
Cloning into 'SomaAgentHub'...
remote: Enumerating objects: 1850, done.
Receiving objects: 100% (1850/1850), 100.0 KiB/s, done.
```

### 2. Verify Setup

```bash
make setup
```

**This script will:**
- ✅ Create `.venv` Python virtual environment
- ✅ Install dependencies (requirements-dev.txt)
- ✅ Copy `.env.example` → `.env` (if not exists)
- ✅ Display verification checklist

**Expected output:**
```
✓ Virtual environment created
✓ Dependencies installed (X packages)
✓ .env file configured
✓ Ready to start: 'make docker-compose-up'
```

### 3. Start Services

```bash
make docker-compose-up
```

**Services will boot in order (wait ~90 seconds for full startup):**
```
✓ gateway-api:10000 (health: ✅)
✓ orchestrator:10001 (health: ✅)
✓ identity-service:10002 (health: ✅)
✓ redis:6379 (health: ✅)
✓ app-postgres:5432 (health: ✅)
✓ qdrant:6333 (health: ✅)
✓ clickhouse:8123 (health: ✅)
✓ minio:9000 (health: ✅)
✓ temporal-server:7233 (health: ✅)
✓ vault:8200 (health: ✅)
✓ prometheus:9090 (health: ✅)
✓ grafana:3000 (health: ✅)
✓ loki:3100 (health: ✅)
✓ tempo:3200 (health: ✅)
✓ otel-collector:4317 (health: ✅)
```

### 4. Verify All Services Healthy

```bash
docker-compose ps
```

**Expected output (all HEALTHY or UP):**
```
NAME                          STATUS              PORTS
somaagenthub-gateway-api      Up 2 minutes        0.0.0.0:10000->10000/tcp
somaagenthub-orchestrator     Up 2 minutes        0.0.0.0:10001->10001/tcp
somaagenthub-identity-service Up 2 minutes        0.0.0.0:10002->10002/tcp
somaagenthub-redis            Up 2 minutes        0.0.0.0:6379->6379/tcp
somaagenthub-app-postgres     Up 2 minutes (healthy)   0.0.0.0:5432->5432/tcp
somaagenthub-qdrant           Up 2 minutes (healthy)   0.0.0.0:6333->6333/tcp
somaagenthub-clickhouse       Up 2 minutes (healthy)   0.0.0.0:8123->8123/tcp
somaagenthub-minio            Up 2 minutes (healthy)   0.0.0.0:9000->9000/tcp
somaagenthub-temporal-server  Up 2 minutes (healthy)   0.0.0.0:7233->7233/tcp
somaagenthub-vault            Up 2 minutes (healthy)   0.0.0.0:8200->8200/tcp
somaagenthub-prometheus       Up 2 minutes (healthy)   0.0.0.0:9090->9090/tcp
somaagenthub-grafana          Up 2 minutes (healthy)   0.0.0.0:3000->3000/tcp
somaagenthub-loki             Up 2 minutes (healthy)   0.0.0.0:3100->3100/tcp
somaagenthub-tempo            Up 2 minutes (healthy)   0.0.0.0:3200->3200/tcp
somaagenthub-otel-collector   Up 2 minutes (healthy)   0.0.0.0:4317->4317/tcp
```

✅ **All services running? Excellent! You're ready to develop.**

---

## ⚙️ Production-Grade Configuration

### Resource Allocation (macOS Docker Desktop)

The docker-compose configuration includes production-level resource allocation to simulate real workloads on your local machine.

**Update Docker Desktop Settings:**

1. Open Docker Desktop → Preferences
2. Navigate to **Resources**
3. Set allocations:
   - **CPU**: 4 cores (or half your total cores)
   - **Memory**: 12 GB (or 2/3 of total RAM)
   - **Disk**: 50 GB (recommended for persistent volumes)

**Verify allocation:**
```bash
docker info | grep -E "CPUs|Memory"
```

**Expected output:**
```
CPUs: 4
Memory: 12 GiB
```

### Service Configuration (Production Mode)

All services are configured for production-like workloads:

| Service | Configuration | Details |
|---------|---|---|
| **PostgreSQL** | `shared_buffers=256MB`, `work_mem=16MB` | Optimized for concurrent connections |
| **Redis** | `maxmemory=512MB`, `maxmemory-policy=allkeys-lru` | Eviction policy set for stability |
| **Qdrant** | `snapshot_cleanup_period=60s` | Auto-cleanup of old snapshots |
| **ClickHouse** | `keeper_server.port=9181` | ClickHouse Keeper configured |
| **Temporal** | `numHistoryShards=4` | Distributed task queues |
| **MinIO** | `MINIO_STORAGE_CLASS_STANDARD` | Replication-aware storage |

**Verify service config:**
```bash
# PostgreSQL: Check connection limits
docker-compose exec app-postgres psql -U somaagent -d somaagent -c "SHOW max_connections;"
# Expected: 200 (production value, not default 100)

# Redis: Check memory allocation
docker-compose exec redis redis-cli INFO memory | grep used_memory_human
# Expected: ~50MB allocated

# Temporal: Check task queue distribution
docker-compose exec temporal-server tctl namespace describe --namespace default | head -20
```

### Network Configuration

All services operate on isolated network `somaagenthub-network`:

```bash
docker network inspect somaagenthub-network
```

**Expected:**
- Driver: bridge
- All services connected
- No external exposure (except defined ports)

### Volume Management (Data Persistence)

Persistent data is stored in Docker volumes:

```bash
docker volume ls | grep somaagenthub
```

**Volumes:**
```
somaagenthub-app-postgres-data          # Application state (10+ GB)
somaagenthub-temporal-postgres-data     # Workflow history (2+ GB)
somaagenthub-redis-data                 # Cache/sessions (500MB)
somaagenthub-qdrant-data                # Vector store (5+ GB)
somaagenthub-clickhouse-data            # Analytics (3+ GB)
somaagenthub-minio-data                 # Object storage (10+ GB)
somaagenthub-vault-data                 # Secrets (1GB)
```

**Inspect volume:**
```bash
docker volume inspect somaagenthub-app-postgres-data
# Shows mount point: /var/lib/docker/volumes/...
```

---

## 🔌 Service Endpoints

### Application Services (Primary APIs)

```bash
# Gateway API (OpenAI-compatible endpoints)
curl -X GET http://localhost:10000/health
# Expected: {"status": "healthy", "version": "..."}

# Orchestrator (Multi-agent workflows)
curl -X GET http://localhost:10001/ready
# Expected: 200 OK

# Identity Service (Auth & JWT)
curl -X GET http://localhost:10002/health
# Expected: {"status": "ok"}
```

### Data Services

| Service | Endpoint | Use Case |
|---------|----------|----------|
| **PostgreSQL** | `localhost:5432` | Application state, Temporal workflows |
| **Redis** | `localhost:6379` | Session caching, real-time data |
| **Qdrant** | `localhost:6333` (HTTP) | Vector search, semantic memory |
| **ClickHouse** | `localhost:8123` (HTTP) | Analytic queries, event logs |
| **MinIO** | `localhost:9000` (API), `9001` (Console) | S3-compatible object storage |

### Observability Stack

| Service | URL | Purpose |
|---------|-----|---------|
| **Grafana** | http://localhost:3000 | Metrics dashboards |
| **Prometheus** | http://localhost:9090 | Metrics scraping & queries |
| **Loki** | http://localhost:3100 | Log aggregation |
| **Tempo** | http://localhost:4317 (OTLP) | Distributed tracing |

### Infrastructure Services

| Service | Endpoint | Function |
|---------|----------|----------|
| **Vault** | `http://localhost:8200` | Secrets management |
| **Temporal Server** | `localhost:7233` (gRPC) | Workflow orchestration |

---

## ✅ Verification Procedures

### Health Check Script

```bash
./scripts/verify-instrumentation.sh
```

**Expected output:**
```
✓ Gateway API: HEALTHY (response time: 45ms)
✓ Orchestrator: HEALTHY (response time: 38ms)
✓ Identity Service: HEALTHY (response time: 52ms)
✓ PostgreSQL: HEALTHY (connections: 5/200)
✓ Redis: HEALTHY (memory: 48MB / 512MB)
✓ Qdrant: HEALTHY (collections: 0)
✓ ClickHouse: HEALTHY (uptime: 120s)
✓ Temporal: HEALTHY (workflows: 0)
✓ Prometheus: HEALTHY (targets: 15/15 up)
✓ Grafana: HEALTHY (dashboards: 8)

ALL SERVICES OPERATIONAL ✅
```

### Manual Verification

```bash
# 1. Check all containers running
docker-compose ps --filter "status=running" | wc -l
# Expected: 15+

# 2. Check logs for errors
docker-compose logs --tail=50 | grep -i error
# Expected: (no ERROR lines)

# 3. Test Gateway API endpoint
curl -s http://localhost:10000/health | jq .
# Expected: JSON response with status

# 4. Test PostgreSQL connection
psql -h localhost -U somaagent -d somaagent -c "SELECT version();"
# Expected: PostgreSQL 16.x running

# 5. Test Redis connection
redis-cli -h localhost ping
# Expected: PONG

# 6. Test Qdrant API
curl -s http://localhost:6333/health | jq .
# Expected: Status 200

# 7. Test Grafana dashboard
curl -s http://localhost:3000/api/health | jq .
# Expected: OK

# 8. Verify metrics collection
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'
# Expected: 15+ active targets
```

---

## 🔧 Troubleshooting

### Common Issues

#### Issue: "Insufficient memory" when starting services

**Symptom:**
```
Error response from daemon: OCI runtime create failed: ... memory: ...
```

**Fix:**
1. Stop all containers: `make docker-compose-down`
2. Increase Docker Desktop memory to 16+ GB (Preferences → Resources)
3. Wait 30 seconds, then restart: `make docker-compose-up`

---

#### Issue: Port conflicts (port 6379 already in use)

**Symptom:**
```
Error: listen tcp 127.0.0.1:6379: bind: address already in use
```

**Fix:**
```bash
# Find what's using port 6379
lsof -i :6379
# Kill the process (if not our container)
kill -9 <PID>
# Or use different port in .env
echo "REDIS_PORT=6380" >> .env
```

---

#### Issue: PostgreSQL won't connect after restart

**Symptom:**
```
psql: error: FATAL: the database system is in recovery mode
```

**Fix:**
```bash
# Remove corrupted volume
docker-compose down -v  # WARNING: deletes all data
# Restart
make docker-compose-up
```

---

#### Issue: Vault sealed after restart

**Symptom:**
```
curl http://localhost:8200/v1/sys/seal-status
# Returns: "sealed": true
```

**Fix:**
```bash
# Unseal Vault (dev mode auto-unseal)
docker-compose exec vault vault unseal
# Or restart container
docker-compose restart vault
```

---

#### Issue: ClickHouse server won't start

**Symptom:**
```
Waiting for server to start... timeout
```

**Fix:**
```bash
# Check logs
docker-compose logs clickhouse | tail -50
# Usually need to rebuild image
docker-compose build --no-cache clickhouse
docker-compose restart clickhouse
```

---

### Resource Exhaustion Debugging

**Monitor real-time resource usage:**
```bash
# CPU & Memory per container
docker stats --no-stream

# Disk usage by volumes
docker system df

# Active network connections
docker-compose exec redis redis-cli info clients

# PostgreSQL connections
docker-compose exec app-postgres psql -U somaagent -d somaagent -c \
  "SELECT datname, count(*) as connections FROM pg_stat_activity GROUP BY datname;"
```

---

### Log Inspection

```bash
# View recent logs from all services
docker-compose logs --tail=100 --follow

# Logs from specific service
docker-compose logs -f gateway-api

# Logs with timestamps
docker-compose logs --timestamps --tail=50 orchestrator

# Search logs for errors
docker-compose logs | grep -i "error\|exception\|failed"
```

---

## 🛑 Cleanup & Reset

### Stop Services (Preserve Data)

```bash
make docker-compose-down
# Services stop, volumes persist (safe for resumption)
```

### Full Reset (Delete Data)

```bash
# WARNING: This deletes all persistent data!
make docker-compose-clean

# Or manually:
docker-compose down -v  # -v removes volumes
docker system prune -a  # Remove unused images
```

### Remove Individual Volume

```bash
# List volumes
docker volume ls

# Remove specific volume
docker volume rm somaagenthub-redis-data

# Recreate it on next start
docker-compose up redis
```

---

## 📊 Performance Tuning

### For Low-End Hardware (8 GB RAM)

If your Mac has only 8 GB RAM, reduce resource allocation:

**In `.env`:**
```env
# Reduce memory allocation
POSTGRES_SHARED_BUFFERS=128MB
REDIS_MAXMEMORY=256MB
# Disable non-essential services
COMPOSE_PROFILES=core  # Only essential services
```

**Services included in `core` profile:**
- gateway-api, orchestrator, identity-service
- PostgreSQL, Redis, Temporal
- Vault

**Run with reduced services:**
```bash
docker-compose --profile core up
```

---

### For High-End Hardware (32+ GB RAM)

Increase performance:

**In `.env`:**
```env
# Increase memory allocation
POSTGRES_SHARED_BUFFERS=1GB
REDIS_MAXMEMORY=2GB
# Enable all observability
COMPOSE_PROFILES=all
```

---

## 🔐 Security Considerations

### Development Credentials (DO NOT USE IN PRODUCTION)

**Current dev credentials are HARDCODED (insecure):**

| Service | User | Password | Note |
|---------|------|----------|------|
| **PostgreSQL** | somaagent | somaagent | Dev only, change for production |
| **Redis** | (none) | (none) | No auth in dev, enable in prod |
| **MinIO** | minioadmin | minioadmin | Default credentials, rotate immediately |
| **Vault** | dev-token | (token-based) | Dev mode unsealed, use proper auth in prod |
| **Temporal** | (none) | (none) | No auth in dev, add TLS/mTLS in prod |

### For Production Use

```bash
# Generate strong passwords
openssl rand -base64 32  # Use for each service

# Store in Vault
vault kv put secret/somaagent/postgres \
  username=somaagent \
  password=$(openssl rand -base64 32)

# Rotate credentials
docker-compose down
# Update .env with new credentials
docker volume rm somaagenthub-app-postgres-data
docker-compose up
```

---

## 📚 Next Steps

✅ **Environment setup complete!**

### What's Next:

1. **Read the Codebase**: `docs/onboarding-manual/codebase-walkthrough.md`
2. **Make Your First Contribution**: `docs/onboarding-manual/first-contribution.md`
3. **Learn Domain Knowledge**: `docs/onboarding-manual/domain-knowledge.md`
4. **Explore Technical Details**: `docs/technical-manual/deployment.md`

### Quick Reference

```bash
# Start services
make docker-compose-up

# Stop services (keep data)
make docker-compose-down

# View logs
docker-compose logs -f <service>

# Run tests
pytest tests/

# Check code style
ruff check .

# Format code
ruff format .
```

---

## ❓ Getting Help

- **Stuck on setup?** → Ask in `#somagenthub-dev` Slack channel
- **Found a bug?** → File an issue on GitHub
- **Questions?** → Tag `@tech-lead` in Slack
- **Documentation issues?** → Open a PR to improve this guide

---

**🎉 Welcome to SomaAgentHub! Happy coding!**
