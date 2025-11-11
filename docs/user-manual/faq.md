# Frequently Asked Questions

![Version](https://img.shields.io/badge/version-1.0.0-blue)

## General Questions

### What is SomaAgentHub?
SomaAgentHub is an enterprise-grade orchestration platform for autonomous agents. It provides production-ready infrastructure for multi-agent workflows with parallel execution, real-time orchestration, and comprehensive governance.

### What makes SomaAgentHub different from other agent frameworks?
- **Production Infrastructure**: Full Kubernetes, Helm, and Terraform stack included
- **Governance & Policy**: Dedicated policy engine with constitution service
- **Memory Architecture**: Pluggable Qdrant/Redis memory gateway
- **CI/CD Automation**: Make-driven builds, scans, and deploys
- **Observability**: Metrics, probes, and Grafana dashboards out of the box

### What are the core services?
- **Gateway API** (port 10000): Public ingress and wizard flows
- **Orchestrator** (port 10001): Temporal workflow coordination
- **Identity Service** (port 10002): Token issuance and validation
- **Memory Gateway** (port 10021): Vector and KV storage
- **Policy Engine** (port 10020): Rule-based guardrails

## Installation & Setup

### What are the minimum requirements?
**Local Development:**
- Docker & Docker Compose
- Python 3.11+
- Kind (Kubernetes in Docker)
- Helm 3+

**Production:**
- Kubernetes 1.24+
- 4 CPU cores, 8GB RAM minimum
- Persistent storage for databases

### How do I deploy locally?
```bash
git clone https://github.com/somatechlat/somaAgentHub.git
cd somaAgentHub
make start-cluster
```

### How long does deployment take?
- Local Kind cluster: 3-5 minutes
- Production Kubernetes: 10-15 minutes
- Initial image builds: 5-10 minutes

### Can I run individual services locally?
Yes, for development:
```bash
make dev-up              # Start dependencies (Temporal, Redis)
make dev-start-services  # Run Gateway and Orchestrator locally
```

## Configuration

### How do I configure service ports?
Ports are defined in the Helm chart (`k8s/helm/soma-agent/values.yaml`):
```yaml
services:
  gateway:
    port: 10000
  orchestrator:
    port: 10001
```

### How do I enable/disable services?
Edit the Helm values file:
```yaml
services:
  memoryGateway:
    enabled: true   # Set to false to disable
  policyEngine:
    enabled: true   # Set to false to disable
```

### Where are environment variables configured?
- Development: `.env` files in service directories
- Kubernetes: ConfigMaps and Secrets in Helm chart
- Local: Environment variables in Makefile

### How do I configure external databases?
Update Helm values:
```yaml
external:
  redis:
    enabled: true
    host: "external-redis.example.com"
    port: 6379
  postgresql:
    enabled: true
    host: "external-postgres.example.com"
```

## Usage

### How do I start an agent workflow?
1. Access Gateway API: `http://localhost:8080` (after port-forward)
2. List wizards: `GET /v1/wizards`
3. Start session: `POST /v1/wizards/start`
4. Provide inputs: `POST /v1/wizards/{session_id}/answer`

### How do I monitor agent execution?
- **Logs**: `kubectl logs -f -l app=orchestrator -n soma-agent-hub`
- **Metrics**: Port-forward Prometheus: `make pf-prom`
- **Health**: `curl http://localhost:8080/healthz`

### How do I access the memory system?
Memory Gateway provides REST API:
```bash
# Store memory
curl -X POST http://memory-gateway:8000/collections/my-collection/points \
  -d '{"points": [{"id": 1, "vector": [...], "payload": {...}}]}'

# Search memory
curl -X POST http://memory-gateway:8000/collections/my-collection/points/search \
  -d '{"vector": [...], "limit": 10}'
```

### How do I configure policies?
Policies are defined in the Policy Engine service:
```yaml
# Example policy
apiVersion: v1
kind: ConfigMap
metadata:
  name: agent-policies
data:
  default.rego: |
    package agent.policies
    
    allow {
        input.action == "read"
    }
    
    deny {
        input.action == "delete"
        not input.user.admin
    }
```

## Troubleshooting

### Services won't start
```bash
# Check pod status
kubectl get pods -n soma-agent-hub

# Check events
kubectl get events -n soma-agent-hub --sort-by='.lastTimestamp'

# Check logs
kubectl logs -l app=gateway-api -n soma-agent-hub
```

### Can't access Gateway API
```bash
# Verify service is running
kubectl get svc gateway-api -n soma-agent-hub

# Check port-forward
make port-forward-gateway LOCAL=8080 REMOTE=10000

# Test health endpoint
curl http://localhost:8080/healthz
```

### Temporal connection issues
```bash
# Check Temporal server
kubectl get pods -l app=temporal -n soma-agent-hub

# Test from orchestrator
kubectl exec -it deployment/orchestrator -n soma-agent-hub -- \
  python -c "from temporal import Client; Client('temporal:7233')"
```

### Memory Gateway not responding
```bash
# Check Qdrant status
kubectl get pods -l app=qdrant -n soma-agent-hub

# Test memory gateway health
kubectl exec -it deployment/memory-gateway -n soma-agent-hub -- \
  curl http://localhost:8000/health
```

### High resource usage
```bash
# Check resource consumption
kubectl top pods -n soma-agent-hub

# Scale down non-essential services
kubectl scale deployment analytics-service --replicas=0 -n soma-agent-hub

# Adjust resource limits in Helm values
```

## Development

### How do I add a new service?
1. Create service directory: `services/my-service/`
2. Add Dockerfile and requirements
3. Update Helm chart: `k8s/helm/soma-agent/templates/my-service.yaml`
4. Add to build script: `scripts/build-changed.sh`

### How do I run tests?
```bash
# All tests
make test-all

# Specific service
pytest services/gateway-api/tests/

# Integration tests
make test-int

# End-to-end tests
make test-e2e
```

### How do I debug services locally?
```bash
# Run with debugger
PYTHONPATH=services/gateway-api python -m pdb -m uvicorn app.main:app

# Enable debug logging
LOG_LEVEL=DEBUG python -m uvicorn app.main:app

# Use IDE debugging with port-forward
make port-forward-gateway LOCAL=8080 REMOTE=10000
```

### How do I contribute?
1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes and add tests
4. Run quality checks: `make check`
5. Submit pull request

## Performance

### How many agents can SomaAgentHub handle?
- **Single node**: 50-100 concurrent agents
- **Multi-node cluster**: 500+ concurrent agents
- **Bottlenecks**: Temporal server, Redis, database connections

### How do I scale the platform?
```bash
# Scale orchestrator
kubectl scale deployment orchestrator --replicas=3 -n soma-agent-hub

# Scale gateway
kubectl scale deployment gateway-api --replicas=5 -n soma-agent-hub

# Add cluster nodes
kubectl get nodes
```

### What are the resource requirements per agent?
- **CPU**: 100-200m per active agent
- **Memory**: 128-256MB per agent session
- **Storage**: 10-50MB per agent memory context

## Security

### How is authentication handled?
- Identity Service issues JWT tokens
- All inter-service communication uses service accounts
- Optional SPIFFE/SPIRE for zero-trust networking

### How are secrets managed?
- Kubernetes Secrets for sensitive data
- Optional Vault integration for secret rotation
- Environment variables for non-sensitive config

### Is the platform secure by default?
- Network policies restrict inter-pod communication
- RBAC controls Kubernetes access
- Policy Engine enforces agent behavior constraints
- All services expose health endpoints only

## Support

### Where can I get help?
- GitHub Issues: Bug reports and feature requests
- Documentation: Comprehensive guides in `/docs/`
- Community: Discussions and Q&A

### How do I report a bug?
1. Check existing issues on GitHub
2. Gather logs: `kubectl logs -l app=<service> -n soma-agent-hub`
3. Include reproduction steps and environment details
4. Submit issue with logs and configuration

### How do I request a feature?
1. Check roadmap in `docs/ROADMAP.md`
2. Open GitHub issue with "enhancement" label
3. Describe use case and expected behavior
4. Participate in discussion and design