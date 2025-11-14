# 🚀 Sprint 1: PostgreSQL Migration & Agent Management

## 📋 Overview

Welcome to Sprint 1 of the SomaAgentHub Production Roadmap! This sprint focuses on migrating from in-memory storage to PostgreSQL-backed services and implementing Kubernetes-native agent management.

## 🎯 Sprint Goals

- ✅ **PostgreSQL-backed Capsule Registry** - Replace in-memory `_store` with proper PostgreSQL ORM
- ✅ **AgentInstance Model** - Create database model for tracking Kubernetes agents
- ✅ **Agent Spawner Service** - Kubernetes-native agent spawning without Volcano
- ✅ **Development Environment** - Docker Compose setup for local development

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Sprint 1 Architecture                │
├─────────────────────────────────────────────────────────┤
│  Task Capsule Repo (PostgreSQL)  │  Agent Spawner      │
│  ├── PostgreSQL Models           │  ├── K8s Jobs       │
│  ├── Repository Pattern         │  ├── K8s Deployments│
│  └── FastAPI Endpoints          │  └── Async DB       │
├─────────────────────────────────────────────────────────┤
│        PostgreSQL (5432/5433) │ Redis (6379)         │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- kubectl configured (for agent spawner)
- Python 3.11+ (optional for local development)

### 1. Start Sprint 1 Environment
```bash
make sprint-1-up
```

### 2. Verify Services
```bash
make sprint-1-status
```

### 3. Test Capsule Registry
```bash
# Create a capsule
make sprint-1-test-capsule

# List capsules
curl http://localhost:8000/v1/capsules

# Get specific capsule
curl http://localhost:8000/v1/capsules/<capsule_id>/1.0.0
```

### 4. Test Agent Spawner
```bash
# Spawn an agent
make sprint-1-test-agent

# Check agent status
curl http://localhost:8001/v1/agents/<instance_id>
```

## 🔧 Development Commands

```bash
# Environment control
make sprint-1-up          # Start environment
make sprint-1-down        # Stop environment
make sprint-1-logs        # View logs
make sprint-1-clean       # Clean up

# Testing
make sprint-1-test-capsule  # Test capsule registry
make sprint-1-test-agent    # Test agent spawner
```

## 📚 API Documentation

### Capsule Registry (Port 8000)
- `POST /v1/capsules` - Create new capsule
- `GET /v1/capsules/{id}/{version}` - Get specific version
- `GET /v1/capsules` - List all capsules
- `PUT /v1/capsules/{id}/{version}` - Update capsule
- `DELETE /v1/capsules/{id}/{version}` - Delete capsule

### Agent Spawner (Port 8001)
- `POST /v1/spawn` - Spawn new agent
- `GET /v1/agents/{id}` - Get agent status
- `POST /v1/agents/{id}/terminate` - Terminate agent

## 🗄️ Database Schema

### Capsules Table
```sql
CREATE TABLE capsules (
    id UUID PRIMARY KEY,
    capsule_id UUID NOT NULL,
    version VARCHAR(50) NOT NULL,
    type ENUM('static', 'workflow', 'external_service', 'analytic'),
    execution_mode ENUM('sync', 'async'),
    manifest_yaml TEXT NOT NULL,
    required_roles JSONB DEFAULT '[]',
    requires_payment BOOLEAN DEFAULT FALSE,
    http_config JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### AgentInstances Table
```sql
CREATE TABLE agent_instances (
    id UUID PRIMARY KEY,
    agent_type VARCHAR(100) NOT NULL,
    capsule_id UUID,
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    status ENUM('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED', 'TERMINATED'),
    k8s_namespace VARCHAR(100) NOT NULL,
    k8s_job_name VARCHAR(100),
    k8s_deployment_name VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    resource_requests JSONB DEFAULT '{}',
    resource_limits JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 🔍 Testing Examples

### Capsule Registry Tests
```bash
# Test capsule creation
export CAPSULE_ID=$(uuidgen)
curl -X POST "http://localhost:8000/v1/capsules" \
  -G -d "capsule_id=$CAPSULE_ID" \
  -d "version=1.0.0" \
  -d "type=workflow" \
  -d "manifest_yaml=kind: Workflow\\napiVersion: argoproj.io/v1alpha1\\nmetadata:\\n  name: test-workflow"

# Test listing
curl "http://localhost:8000/v1/capsules?type=workflow&limit=10"
```

### Agent Spawner Tests
```bash
# Test agent spawning
export TENANT_ID="550e8400-e29b-41d4-a716-446655440000"
export USER_ID="550e8400-e29b-41d4-a716-446655440001"

curl -X POST "http://localhost:8001/v1/spawn" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "code-generator",
    "tenant_id": "'"$TENANT_ID"'",
    "user_id": "'"$USER_ID"'",
    "image": "python:3.11-slim",
    "execution_mode": "batch",
    "env_vars": {"TASK": "generate_code"},
    "resource_requests": {"cpu": "100m", "memory": "128Mi"},
    "resource_limits": {"cpu": "500m", "memory": "512Mi"}
  }'
```

## 🐛 Troubleshooting

### PostgreSQL Connection Issues
```bash
# Check if databases are running
docker-compose -f docker-compose.sprint1.yml ps

# Connect to databases
docker-compose -f docker-compose.sprint1.yml exec postgres-capsule psql -U postgres -d capsule_registry
docker-compose -f docker-compose.sprint1.yml exec postgres-agent psql -U postgres -d agent_spawner
```

### Agent Spawner Issues
```bash
# Check if Kubernetes is accessible
kubectl cluster-info

# View spawned agents
kubectl get pods -A | grep agent
kubectl get jobs -A | grep agent
```

## 📊 Sprint Completion Checklist

### Must Have ✅
- [ ] PostgreSQL-backed capsule registry working
- [ ] AgentInstance model created and tested
- [ ] Agent spawner service operational
- [ ] Docker compose environment functional
- [ ] Basic CRUD operations working

### Nice to Have 🎯
- [ ] Comprehensive test suite
- [ ] Monitoring dashboards
- [ ] Performance benchmarks
- [ ] Security hardening
- [ ] Documentation complete

## 🔄 Next Steps

Once Sprint 1 is complete:
1. Run `make sprint-1-complete` to mark completion
2. Move to Sprint 2: Payment Integration
3. Review architecture decisions
4. Performance testing

## 📞 Support

- **Issues**: Create GitHub issue with `sprint-1` label
- **Discussions**: Use #sprint-1 channel
- **Docs**: See `/docs/sprint1/` for detailed documentation

---

Happy coding! 🚀