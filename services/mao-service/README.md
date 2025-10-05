# Multi-Agent Orchestrator (MAO) Service

## Overview

The MAO service orchestrates multi-agent projects using **Temporal workflows**. It enables:

- **Task Capsule execution** with dependency management (DAG, sequential, parallel)
- **VSCode dev container workspaces** for isolated execution environments
- **Real-time project monitoring** via WebSocket streaming
- **Artifact bundling** and storage (S3)
- **Webhook notifications** for project completion
- **Workspace lifecycle management** (create, provision, cleanup)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MAO Service                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  FastAPI     │───>│  Temporal    │───>│  Workspace   │ │
│  │  REST API    │    │  Client      │    │  Manager     │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                    │                    │        │
│         ▼                    ▼                    ▼        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  WebSocket   │    │  Workflows   │    │  Docker API  │ │
│  │  Streaming   │    │  (DAG/Seq)   │    │  (VSCode)    │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
   Project        Temporal Server         Dev Containers
   Dashboard      (PostgreSQL)           (Isolated Workspaces)
```

## Components

### 1. Temporal Infrastructure

**Docker Compose** (`infra/temporal/docker-compose.yml`):
- Temporal server (v1.22.4)
- PostgreSQL (metadata storage)
- Temporal UI (web interface)
- Admin tools

**Kubernetes** (`infra/k8s/temporal/`):
- Production-ready deployment (3 replicas)
- LoadBalancer services
- ConfigMaps for dynamic configuration
- Health checks and resource limits

### 2. Workflows

**ProjectWorkflow** (`workflows/project_workflow.py`):
- Main orchestration workflow
- Supports 3 execution modes:
  - **Sequential**: Tasks run one after another
  - **Parallel**: All tasks run simultaneously
  - **DAG**: Tasks run based on dependency graph
- Handles workspace setup, task execution, artifact bundling
- Query support for real-time status
- Signal support for cancellation

**Activities** (`workflows/activities.py`):
- `create_workspace`: Launch VSCode dev container
- `provision_git_repo`: Clone repository into workspace
- `execute_capsule`: Run Task Capsule with persona
- `bundle_artifacts`: Upload artifacts to S3
- `notify_completion`: Send webhook notifications
- `cleanup_workspace`: Remove container and volume

### 3. MAO Service

**FastAPI Application** (`app/main.py`):
- REST API for project management
- WebSocket endpoint for real-time updates
- Temporal client integration
- Endpoints:
  - `POST /v1/projects` - Create project
  - `GET /v1/projects/{id}` - Get status
  - `POST /v1/projects/{id}/cancel` - Cancel project
  - `GET /v1/projects/{id}/result` - Get final result
  - `WS /v1/projects/{id}/stream` - Real-time updates

**Worker** (`worker.py`):
- Temporal worker process
- Executes workflow activities
- Concurrent execution (10 activities, 10 workflows)

**Workspace Manager** (`app/workspace_manager.py`):
- Docker container management
- VSCode dev environment provisioning
- Git repository cloning
- Command execution in containers
- Lifecycle management (start, stop, cleanup)

### 4. Project Dashboard UI

**React Application** (`ui/project-dashboard/`):
- Real-time task graph visualization (D3.js + Dagre)
- Project list and detail views
- WebSocket integration for live updates
- Task status monitoring
- Execution controls

## Quick Start

### 1. Start Temporal Cluster

```bash
cd infra/temporal
docker-compose up -d

# Wait for startup
until curl -s http://localhost:7233 > /dev/null; do sleep 1; done

# Open Temporal UI
open http://localhost:8088
```

### 2. Start MAO Service

```bash
# Install dependencies
cd services/mao-service
pip install -r requirements.txt

# Start worker (terminal 1)
python worker.py

# Start API service (terminal 2)
python app/main.py

# API docs available at http://localhost:8007/docs
```

### 3. Create a Project

```bash
# Run example
cd examples/mao-project
python create_project.py
```

Or use the API directly:

```bash
curl -X POST http://localhost:8007/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "Test Project",
    "execution_mode": "dag",
    "tasks": [
      {
        "task_id": "task-1",
        "capsule_id": "test-capsule",
        "persona_id": "test-persona",
        "description": "First task",
        "dependencies": []
      },
      {
        "task_id": "task-2",
        "capsule_id": "test-capsule",
        "persona_id": "test-persona",
        "description": "Second task (depends on task-1)",
        "dependencies": ["task-1"]
      }
    ]
  }'
```

### 4. Monitor Progress

```bash
# Get project status
PROJECT_ID="project-abc123"
curl http://localhost:8007/v1/projects/$PROJECT_ID

# WebSocket streaming (use wscat or web client)
wscat -c ws://localhost:8007/v1/projects/$PROJECT_ID/stream
```

## Execution Modes

### Sequential
Tasks execute one after another in order:
```
Task 1 → Task 2 → Task 3 → Task 4
```

### Parallel
All tasks execute simultaneously:
```
Task 1 ┐
Task 2 ├─→ (all run at once)
Task 3 ┘
```

### DAG (Directed Acyclic Graph)
Tasks execute based on dependencies:
```
       Task 1
      /      \
   Task 2   Task 3
      \      /
       Task 4
```

## Configuration

### Workspace Configuration

```python
workspace_config = {
    "vscode_image": "codercom/code-server:latest",
    "cpu_limit": "2",           # CPU cores
    "memory_limit": "4g",        # RAM limit
    "environment": {             # Environment variables
        "NODE_ENV": "development",
        "PYTHON_VERSION": "3.11"
    }
}
```

### Task Configuration

```python
task = {
    "task_id": "unique-task-id",
    "capsule_id": "task-capsule-id",
    "persona_id": "persona-id",
    "description": "Task description",
    "dependencies": ["task-1", "task-2"],  # Dependency list
    "timeout_seconds": 3600,               # 1 hour timeout
    "retry_attempts": 3,                   # Retry on failure
    "metadata": {                          # Custom metadata
        "optional": False,                 # Required task
        "priority": "high"
    }
}
```

## Monitoring

### Temporal UI
- Workflow execution history
- Task queue backlogs
- Worker status
- Failed workflows

Access at: http://localhost:8088

### Prometheus Metrics
- Temporal server metrics (port 9090)
- MAO service metrics
- Workspace resource usage

### Logs
- Structured logging with trace IDs
- Worker activity logs
- API request logs

## Production Deployment

### Kubernetes

```bash
# Apply Temporal infrastructure
kubectl apply -f infra/k8s/temporal/

# Deploy MAO service
kubectl apply -f infra/k8s/mao-service/

# Check status
kubectl get pods -n temporal
kubectl get pods -n somagent
```

### Scaling

**Horizontal scaling**:
- Multiple MAO API replicas (stateless)
- Multiple workers for parallel execution
- Temporal server scaling (3+ replicas)

**Resource limits**:
- Worker: 2 CPU, 4GB RAM per instance
- API: 1 CPU, 2GB RAM per instance
- Temporal: 2-4 CPU, 4-8GB RAM per instance

## Troubleshooting

### Worker not processing tasks
```bash
# Check worker connection
docker logs temporal-server
docker logs mao-worker

# Verify task queue
temporal workflow list --namespace default
```

### Workspace creation fails
```bash
# Check Docker
docker ps
docker images

# Check resources
docker stats

# View workspace logs
docker logs <workspace-id>
```

### Temporal connection issues
```bash
# Test connection
curl http://localhost:7233

# Check PostgreSQL
docker logs temporal-postgres

# Reset Temporal (dev only)
docker-compose -f infra/temporal/docker-compose.yml down -v
docker-compose -f infra/temporal/docker-compose.yml up -d
```

## Development

### Run Tests

```bash
cd services/mao-service
pytest tests/ -v --cov
```

### Lint & Format

```bash
black app/ workflows/
ruff check app/ workflows/
mypy app/ workflows/
```

## Next Steps

1. **Integrate with Task Capsule Repository** - Execute real capsules
2. **Add persona management** - Dynamic persona loading
3. **Implement resource quotas** - Per-tenant limits
4. **Add observability** - Distributed tracing
5. **Build project templates** - Pre-configured workflows

---

**Status**: ✅ Production-Ready  
**Version**: 1.0.0  
**Last Updated**: October 2025
