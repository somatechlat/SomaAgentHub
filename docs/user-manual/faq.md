# SomaAgentHub FAQ & Troubleshooting

**Quick answers to common questions and solutions to frequent issues**

This guide provides answers to the most frequently asked questions about using SomaAgentHub, along with troubleshooting steps for common problems.

---

## 🎯 General Questions

### What is SomaAgentHub and how is it different from other AI platforms?

**SomaAgentHub** is an enterprise-grade agent orchestration platform that specializes in **coordinating multiple AI agents** working together on complex tasks. Unlike single-agent systems or simple API wrappers, SomaAgentHub provides:

- **Multi-Agent Coordination** - Multiple specialized agents collaborating on tasks
- **Production Infrastructure** - Kubernetes-native deployment with monitoring
- **Intelligent Memory** - Persistent, semantic context across conversations
- **Policy Governance** - Built-in AI safety and constitutional constraints
- **Tool Integration** - 16+ pre-built connectors to external services

### Is SomaAgentHub compatible with OpenAI APIs?

**Yes!** SomaAgentHub provides OpenAI-compatible endpoints, so you can:

```bash
# Use existing OpenAI client libraries
curl -X POST http://your-domain.com/v1/chat/completions \
  -H "Authorization: Bearer your-token" \
  -d '{"model": "gpt-3.5-turbo", "messages": [...]}'
```

**Key differences:**
- Enhanced with multi-agent orchestration capabilities
- Built-in memory and context management
- Policy enforcement and governance features
- Local model support (no external API costs)

### What are the system requirements for running SomaAgentHub?

**Minimum Requirements:**
- **CPU**: 2+ cores (Intel/AMD x64 or ARM64)
- **RAM**: 4GB (8GB+ recommended for production)
- **Storage**: 10GB free space
- **OS**: Linux, macOS, or Windows with WSL2
- **Docker**: Version 20.10+

**Recommended for Production:**
- **CPU**: 4+ cores
- **RAM**: 16GB+  
- **Storage**: 50GB+ (SSD recommended)
- **Kubernetes**: 1.24+ (for K8s deployments)

### Can I use SomaAgentHub without Kubernetes?

**Yes!** SomaAgentHub supports multiple deployment options:

1. **Docker Compose** (simplest) - Great for development and small-scale usage
2. **Local Kubernetes (Kind)** - Production-like environment locally  
3. **Existing Kubernetes** - Full production deployment
4. **Cloud Managed** - EKS, GKE, AKS with managed services

Start with Docker Compose and scale up as needed.

---

## 🚀 Getting Started

### How do I install SomaAgentHub quickly?

**Fastest method (5 minutes):**

```bash
# 1. Clone repository
git clone https://github.com/somatechlat/somaAgentHub.git
cd somaAgentHub

# 2. Start with Docker Compose
make dev-up

# 3. Verify installation  
curl http://localhost:8080/health
```

See the [Installation Guide](installation.md) for detailed instructions and other deployment options.

### I'm getting "connection refused" errors. What should I check?

**Troubleshooting steps:**

```bash
# 1. Check if services are running
docker compose ps

# 2. Check service logs
docker compose logs gateway-api
docker compose logs orchestrator

# 3. Verify port bindings
docker compose port gateway-api 8080

# 4. Test internal connectivity
docker compose exec gateway-api curl http://orchestrator:8001/health
```

**Common causes:**
- Services still starting up (wait 2-3 minutes)
- Port conflicts (check if 8080, 8001, etc. are available)
- Firewall blocking connections
- Docker daemon not running

### How do I create my first agent workflow?

**Quick example:**

```bash
# Start a simple workflow
curl -X POST http://localhost:8001/v1/workflows/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "workflow_type": "simple_task",
    "input": {
      "task": "Analyze the benefits of renewable energy",
      "output_format": "bullet_points"
    },
    "metadata": {"user_id": "getting_started"}
  }'

# Check workflow status
curl http://localhost:8001/v1/workflows/WORKFLOW_ID \
  -H "Authorization: Bearer demo-token"
```

Follow the [Quick Start Tutorial](quick-start-tutorial.md) for a complete walkthrough.

---

## 💡 Usage Questions

### How do I make agents remember information between conversations?

Use the **Memory System** to store and recall context:

```bash
# Store information
curl -X POST http://localhost:8004/v1/memories \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "user_id": "your-user-id",
    "content": "User prefers technical documentation with code examples",
    "memory_type": "user_preferences"
  }'

# Agents automatically recall relevant information
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [...],
    "memory_config": {"use_memory": true},
    "user_id": "your-user-id"
  }'
```

### Can multiple agents work on the same task simultaneously?

**Absolutely!** This is one of SomaAgentHub's core strengths:

```bash
curl -X POST http://localhost:8001/v1/workflows/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "workflow_type": "parallel_research",
    "input": {
      "topic": "Climate change solutions",
      "agents": [
        {"role": "technology_researcher"},
        {"role": "policy_analyst"}, 
        {"role": "economic_analyst"}
      ],
      "coordination": "parallel"
    }
  }'
```

Each agent works independently and their results are automatically coordinated.

### How do I connect agents to external services like GitHub or Slack?

Use the **Tool Service** with pre-built integrations:

```bash
# List available tools
curl http://localhost:8005/v1/tools

# Configure GitHub integration
curl -X POST http://localhost:8005/v1/tools/github/configure \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "config": {
      "github_token": "your-github-token",
      "default_org": "your-organization"
    }
  }'

# Use in workflows
curl -X POST http://localhost:8001/v1/workflows/start \
  -d '{
    "workflow_type": "code_review",
    "input": {
      "repository": "your-org/your-repo",
      "pull_request": 123
    },
    "tools": ["github", "code_analyzer"]
  }'
```

### How do I ensure agents follow our company policies?

Use the **Policy Engine** for governance:

```bash
# Set up policies
curl -X POST http://localhost:8007/v1/policies \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "tenant": "your-company",
    "policies": [
      {
        "rule": "no_sensitive_data_sharing",
        "description": "Prevent sharing of PII or confidential information"
      },
      {
        "rule": "require_approval_for_external_communications", 
        "description": "Human approval required for external emails/messages"
      }
    ]
  }'

# Policies are automatically enforced in all agent interactions
```

---

## 🔧 Technical Issues

### Services are running but workflows aren't executing

**Check workflow execution:**

```bash
# 1. Verify Temporal is running
curl http://localhost:8233

# 2. Check orchestrator connectivity to Temporal
docker compose logs orchestrator | grep -i temporal

# 3. Check workflow worker status
curl http://localhost:8001/v1/workers/status

# 4. Manually trigger a simple workflow
curl -X POST http://localhost:8001/v1/workflows/start \
  -d '{"workflow_type": "health_check", "input": {}}'
```

**Common fixes:**
- Restart orchestrator: `docker compose restart orchestrator`
- Clear Temporal state: `docker compose down && docker volume rm somaAgentHub_temporal_data`
- Check resource limits: `docker stats`

### Memory/recall is not working properly

**Troubleshooting memory issues:**

```bash
# 1. Check memory gateway health
curl http://localhost:8004/health

# 2. Verify Qdrant vector database
curl http://localhost:6333/collections

# 3. Test embedding generation
curl -X POST http://localhost:8004/v1/debug/embedding \
  -d '{"text": "test embedding generation"}'

# 4. Check memory storage
curl http://localhost:8004/v1/memories?user_id=YOUR_USER&limit=5
```

**Common solutions:**
- Restart memory services: `docker compose restart memory-gateway qdrant`
- Clear vector database: `docker volume rm somaAgentHub_qdrant_data`
- Check embedding model availability

### High memory or CPU usage

**Performance optimization:**

```bash
# 1. Monitor resource usage
docker stats --no-stream

# 2. Check service-specific metrics
curl http://localhost:8080/metrics | grep memory
curl http://localhost:8001/metrics | grep cpu

# 3. Scale down if needed
docker compose up -d --scale orchestrator=1 --scale gateway-api=1
```

**Performance tuning:**
- Reduce concurrent workflow limit
- Adjust memory retention policies
- Use local models instead of API calls
- Implement result caching

### API responses are slow

**Performance debugging:**

```bash
# 1. Check response times
time curl http://localhost:8080/v1/models

# 2. Monitor internal service latency  
curl http://localhost:8080/metrics | grep http_request_duration

# 3. Check database performance
docker compose logs postgresql | grep -i slow

# 4. Test with minimal payload
curl -X POST http://localhost:8080/v1/chat/completions \
  -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
```

**Optimization strategies:**
- Enable response caching
- Use streaming responses for chat
- Implement connection pooling
- Add load balancing for multiple instances

---

## 🛡️ Security & Compliance

### How secure is SomaAgentHub?

**Security features:**

- **Authentication** - JWT tokens with configurable expiration
- **Authorization** - Role-based access control (RBAC)
- **Encryption** - TLS in transit, AES-256 at rest
- **Audit Logging** - Complete audit trail of all actions
- **Network Security** - Service mesh with mTLS (in Kubernetes deployments)
- **Secrets Management** - Integration with Vault and Kubernetes secrets

### Can I run SomaAgentHub in an air-gapped environment?

**Yes!** SomaAgentHub supports offline deployment:

```bash
# 1. Download offline installation package
wget https://releases.somagenthub.com/offline/v1.0.0/soma-agent-hub-offline.tar.gz

# 2. Load images in air-gapped environment
docker load < soma-agent-hub-images.tar

# 3. Deploy with local model configuration
helm install soma-agent-hub ./helm/soma-agent \
  --set ai.provider=local \
  --set ai.model_path=/opt/models/
```

**Air-gap considerations:**
- Use local embedding models
- Pre-downloaded language models  
- Internal container registry
- Offline documentation

### Does SomaAgentHub comply with GDPR/CCPA?

**Compliance features:**

- **Data Residency** - Configure data storage regions
- **Right to be Forgotten** - Automatic data deletion APIs
- **Data Export** - Complete user data export in standard formats
- **Consent Management** - Granular permission controls
- **Audit Trails** - Complete activity logging

```bash
# Delete user data (GDPR compliance)
curl -X DELETE http://localhost:8004/v1/users/USER_ID/data \
  -H "Authorization: Bearer admin-token"

# Export user data  
curl http://localhost:8004/v1/users/USER_ID/export \
  -H "Authorization: Bearer admin-token"
```

---

## 🔗 Integration Questions

### Can I integrate SomaAgentHub with my existing systems?

**Yes!** Multiple integration approaches:

1. **REST APIs** - OpenAI-compatible endpoints
2. **Webhooks** - Real-time event notifications
3. **SDK Libraries** - Python, JavaScript, Go clients
4. **Tool Adapters** - Pre-built connectors for popular services
5. **Custom Tools** - Build your own integrations

**Example integrations:**
- CRM systems (Salesforce, HubSpot)
- Development tools (GitHub, Jira, Jenkins)  
- Communication (Slack, Discord, Teams)
- Databases (PostgreSQL, MongoDB, Redis)
- Cloud services (AWS, Azure, GCP)

### How do I build custom tool integrations?

**Custom tool development:**

```python
# tools/my_custom_tool.py
from soma_tools import ToolAdapter

class MyCustomTool(ToolAdapter):
    def __init__(self):
        super().__init__(
            name="my_custom_tool",
            description="Connects to my internal system",
            version="1.0.0"
        )
    
    def execute(self, action: str, params: dict) -> dict:
        if action == "get_data":
            # Your custom logic here
            return {"result": "success", "data": [...]}
        
    def configure(self, config: dict):
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url")

# Register the tool
tool_registry.register(MyCustomTool())
```

### Can I use SomaAgentHub with my existing LLM provider?

**Multiple LLM provider support:**

```bash
# Configure different providers
curl -X POST http://localhost:8003/v1/providers/configure \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "providers": [
      {
        "name": "openai",
        "type": "api",
        "config": {"api_key": "your-key", "base_url": "https://api.openai.com"}
      },
      {
        "name": "azure_openai", 
        "type": "azure",
        "config": {"api_key": "your-key", "endpoint": "https://your-resource.openai.azure.com"}
      },
      {
        "name": "local_llama",
        "type": "local",
        "config": {"model_path": "/opt/models/llama-7b", "device": "cuda"}
      }
    ]
  }'

# Use specific provider in requests
curl -X POST http://localhost:8080/v1/chat/completions \
  -d '{
    "model": "gpt-4",
    "provider": "azure_openai",
    "messages": [...]
  }'
```

---

## 📊 Monitoring & Debugging

### How do I monitor SomaAgentHub performance?

**Built-in monitoring:**

1. **Prometheus Metrics** - Available at `/metrics` endpoints
2. **Grafana Dashboards** - Pre-built visualization dashboards  
3. **Health Endpoints** - Real-time health status
4. **Temporal Web UI** - Workflow execution visibility
5. **Audit Logs** - Complete activity tracking

```bash
# Access monitoring
open http://localhost:3000  # Grafana dashboards
open http://localhost:8233  # Temporal workflows
curl http://localhost:8080/metrics  # Prometheus metrics
```

### What logs should I check when troubleshooting?

**Key log locations:**

```bash
# Service logs (Docker Compose)
docker compose logs gateway-api
docker compose logs orchestrator  
docker compose logs memory-gateway
docker compose logs policy-engine

# Kubernetes logs
kubectl logs -n soma-agent-hub deployment/gateway-api
kubectl logs -n soma-agent-hub deployment/orchestrator

# Application-specific logs
tail -f /var/log/soma/application.log
tail -f /var/log/soma/audit.log
```

### How do I enable debug logging?

**Enable detailed logging:**

```bash
# Environment variable (Docker Compose)
echo "LOG_LEVEL=DEBUG" >> .env
docker compose up -d

# Kubernetes ConfigMap
kubectl patch configmap soma-config \
  -p '{"data":{"LOG_LEVEL":"DEBUG"}}'
kubectl rollout restart deployment/gateway-api

# Runtime log level change
curl -X PUT http://localhost:8080/v1/admin/log-level \
  -H "Authorization: Bearer admin-token" \
  -d '{"level": "DEBUG"}'
```

---

## 🆘 Getting Help

### Where can I find more detailed documentation?

**Documentation locations:**

- **[User Manual](index.md)** - Complete usage guides (this manual)
- **[Technical Manual](../technical-manual/)** - Deployment and operations
- **[Development Manual](../development-manual/)** - Contributing and customization  
- **[Integration Guide](../SOMAGENTHUB_INTEGRATION_GUIDE.md)** - Comprehensive API examples
- **[GitHub Repository](https://github.com/somatechlat/somaAgentHub)** - Source code and issues

### How do I report bugs or request features?

**GitHub Issues:**
1. Check [existing issues](https://github.com/somatechlat/somaAgentHub/issues) first
2. Use appropriate issue template:
   - 🐛 Bug Report
   - ✨ Feature Request  
   - 📚 Documentation Improvement
   - 🚀 Performance Issue

**Include in bug reports:**
- SomaAgentHub version
- Deployment method (Docker/Kubernetes)
- Steps to reproduce
- Error logs and screenshots
- Expected vs actual behavior

### Is there a community forum or chat?

**Community channels:**

- **GitHub Discussions** - Q&A, feature discussions, showcases
- **Discord Server** - Real-time community chat (link in repository)
- **Stack Overflow** - Tag questions with `somagenthub`
- **Documentation Issues** - Feedback on docs via GitHub issues

### Can I get commercial support?

**Support options:**

- **Community Support** - Free via GitHub and Discord
- **Professional Services** - Custom integrations and deployment assistance
- **Enterprise Support** - SLA-backed support with priority response
- **Training & Consulting** - Team onboarding and best practices

Contact: support@somatech.lat for commercial options.

---

## 🎯 Quick Reference

### Essential Commands

```bash
# Health checks
curl http://localhost:8080/health
curl http://localhost:8001/health  
curl http://localhost:8004/health

# Service restart
docker compose restart
make dev-up

# View logs
docker compose logs -f gateway-api
kubectl logs -f deployment/orchestrator

# Check running workflows
curl http://localhost:8001/v1/workflows?status=running

# Memory usage
docker stats
kubectl top pods
```

### Common Error Codes

| Error | Meaning | Solution |
|-------|---------|----------|
| `HTTP 401` | Authentication failed | Check authorization token |
| `HTTP 429` | Rate limit exceeded | Implement backoff or request limit increase |
| `HTTP 503` | Service unavailable | Check service health and restart if needed |
| `Connection refused` | Service not running | Verify service is started and ports are correct |
| `Timeout` | Request took too long | Check service performance and increase timeout |

---

**Can't find what you're looking for? Open a [GitHub issue](https://github.com/somatechlat/somaAgentHub/issues/new) or join our [community discussions](https://github.com/somatechlat/somaAgentHub/discussions)!**
