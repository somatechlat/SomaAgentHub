# Intelligent Memory

**Memory Gateway Service for Agent Context Storage**

> Optional memory service that provides vector storage and context management when enabled in SomaAgentHub deployments.

---

## 📋 Overview

The Memory Gateway is an optional SomaAgentHub service (default container port **9595**, exposed locally at `http://localhost:9595`) that provides:

- **Vector Storage** - Qdrant integration for semantic search
- **Context Storage** - Redis-based session state management
- **Optional Deployment** - Not included in default docker-compose stack
- **Configurable Integration** - Can be enabled per deployment needs

---

## 🧠 Core Capabilities

### Vector Storage
When enabled, the memory gateway provides:
- Qdrant vector database integration
- Semantic search capabilities
- Document storage and retrieval

### Context Management
Redis-based context storage for:
- Session state persistence
- Agent conversation history
- Workflow intermediate results

### Configuration
Memory gateway is configured via:
- Environment variables
- Helm chart values
- Service is typically exposed behind a Service/Ingress; container listens on port 8000

---

## 🚀 Getting Started

### Enable Memory Gateway

The memory gateway is an optional service not included in the default docker-compose stack.

**To enable:**
1. Deploy Qdrant vector database
2. Configure memory gateway service
3. Update Helm values to include memory gateway
4. Verify service is reachable (default container port **9595**; external port may vary)

**Check if enabled:**
```bash
# Check if memory gateway is running
kubectl get pods -n soma-agent-hub | grep memory-gateway

# Port forward to test (example mapping)
kubectl port-forward svc/memory-gateway 10021:9595
```

---

## 🔧 Technical Details

### Service Architecture
- **Service Name**: memory-gateway
- **Container Port**: 9595 (exposed locally as `http://localhost:9595`)
- **Dependencies**: Qdrant, Redis
- **Optional**: Not in default docker-compose

### Integration
When enabled, other services can access memory capabilities through the Memory Gateway API. The service also exposes a Prometheus metrics endpoint at `http://localhost:9595/metrics` for external monitoring.

---

## 📞 More Information

For deployment and configuration details, see the technical manual and service documentation in the services/memory-gateway directory.
