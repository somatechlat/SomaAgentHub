# RUNBOOK-002: Memory Gateway Service Issues

![Version](https://img.shields.io/badge/version-1.0.0-blue)

| Metadata | Value |
|---|---|
| **Alert Name** | `MemoryGatewayDown`, `MemoryGatewayHighLatency` |
| **Severity** | P1 (Critical) - P2 (High) |
| **Owner** | Platform Engineering Team |
| **Last Updated** | 2024-12-19 |

---

This runbook covers troubleshooting the Memory Gateway service (port 10021) which provides vector and key-value storage for agent memory.

## 1. Service Overview

**Memory Gateway** (`memory-gateway`) provides:
- Vector storage via Qdrant integration
- Key-value storage via Redis
- Semantic search capabilities
- Memory lifecycle management

**Dependencies**:
- Qdrant (vector database)
- Redis (key-value cache)
- Kubernetes cluster networking

## 2. Common Alerts

### MemoryGatewayDown
**Trigger**: Service health endpoint returns non-200 status for >5 minutes
**Impact**: Agents cannot store or retrieve memory context

### MemoryGatewayHighLatency
**Trigger**: P95 response time >2 seconds for >10 minutes
**Impact**: Slow agent responses, degraded user experience

### QdrantConnectionFailed
**Trigger**: Qdrant connectivity issues
**Impact**: Vector storage operations fail

## 3. Triage & Diagnosis

### Initial Checks
```bash
# Check service status
kubectl get pods -n soma-agent-hub -l app=memory-gateway

# Check service endpoints
kubectl get svc memory-gateway -n soma-agent-hub

# Test health endpoint
kubectl port-forward svc/memory-gateway 8080:8000 -n soma-agent-hub &
curl http://localhost:8080/health
```

### Diagnostic Steps

#### 3.1 Check Pod Status
```bash
export SERVICE_NAME="memory-gateway"
kubectl get pods -n soma-agent-hub -l app=$SERVICE_NAME

# Expected: Running status
# Issues: CrashLoopBackOff, Pending, ImagePullBackOff
```

#### 3.2 Review Service Logs
```bash
export POD_NAME=$(kubectl get pods -n soma-agent-hub -l app=memory-gateway -o jsonpath='{.items[0].metadata.name}')
kubectl logs -n soma-agent-hub $POD_NAME --tail=100

# Look for:
# - Qdrant connection errors
# - Redis connection failures
# - Memory allocation issues
# - HTTP request errors
```

#### 3.3 Check Dependencies

**Qdrant Health**:
```bash
# Check Qdrant pod status
kubectl get pods -n soma-agent-hub -l app=qdrant

# Test Qdrant connectivity
kubectl exec -it $POD_NAME -n soma-agent-hub -- \
  curl http://qdrant:6333/health
```

**Redis Health**:
```bash
# Check Redis connectivity
kubectl exec -it $POD_NAME -n soma-agent-hub -- \
  redis-cli -h redis ping

# Expected: PONG
```

#### 3.4 Check Resource Usage
```bash
# Check memory and CPU usage
kubectl top pod $POD_NAME -n soma-agent-hub

# Check resource limits
kubectl describe pod $POD_NAME -n soma-agent-hub | grep -A 5 "Limits\|Requests"
```

#### 3.5 Test API Endpoints
```bash
# Port forward for testing
kubectl port-forward svc/memory-gateway 8080:8000 -n soma-agent-hub &

# Test health endpoint
curl http://localhost:8080/health

# Test collections endpoint
curl http://localhost:8080/collections

# Test vector storage (if collections exist)
curl -X POST http://localhost:8080/collections/test/points \
  -H "Content-Type: application/json" \
  -d '{"points": [{"id": 1, "vector": [0.1, 0.2, 0.3], "payload": {"test": true}}]}'
```

## 4. Common Issues & Solutions

### 4.1 Service Won't Start

**Symptoms**: Pod in CrashLoopBackOff or Error state

**Diagnosis**:
```bash
kubectl logs $POD_NAME -n soma-agent-hub --previous
kubectl describe pod $POD_NAME -n soma-agent-hub
```

**Common Causes & Solutions**:

1. **Configuration Issues**:
   ```bash
   # Check ConfigMap
   kubectl get configmap memory-gateway-config -n soma-agent-hub -o yaml
   
   # Verify environment variables
   kubectl exec -it $POD_NAME -n soma-agent-hub -- env | grep -E "(QDRANT|REDIS)"
   ```

2. **Dependency Unavailable**:
   ```bash
   # Restart dependencies first
   kubectl rollout restart deployment/qdrant -n soma-agent-hub
   kubectl rollout restart deployment/redis -n soma-agent-hub
   
   # Wait for dependencies to be ready
   kubectl wait --for=condition=ready pod -l app=qdrant -n soma-agent-hub --timeout=300s
   ```

3. **Resource Constraints**:
   ```bash
   # Check node resources
   kubectl describe nodes
   
   # Increase resource limits
   kubectl patch deployment memory-gateway -n soma-agent-hub -p '
   {
     "spec": {
       "template": {
         "spec": {
           "containers": [{
             "name": "memory-gateway",
             "resources": {
               "requests": {"memory": "512Mi", "cpu": "500m"},
               "limits": {"memory": "1Gi", "cpu": "1000m"}
             }
           }]
         }
       }
     }
   }'
   ```

### 4.2 High Latency Issues

**Symptoms**: Slow response times, timeouts

**Diagnosis**:
```bash
# Check response times
kubectl exec -it $POD_NAME -n soma-agent-hub -- \
  time curl -s http://localhost:8000/health

# Check Qdrant performance
kubectl exec -it $POD_NAME -n soma-agent-hub -- \
  curl http://qdrant:6333/metrics | grep -E "(request_duration|collection_size)"
```

**Solutions**:

1. **Scale Up Service**:
   ```bash
   kubectl scale deployment memory-gateway --replicas=3 -n soma-agent-hub
   ```

2. **Optimize Qdrant**:
   ```bash
   # Check collection sizes
   kubectl exec -it deployment/qdrant -n soma-agent-hub -- \
     curl http://localhost:6333/collections
   
   # Optimize collections (if needed)
   kubectl exec -it deployment/qdrant -n soma-agent-hub -- \
     curl -X POST http://localhost:6333/collections/{collection_name}/index
   ```

3. **Redis Performance**:
   ```bash
   # Check Redis memory usage
   kubectl exec -it deployment/redis -n soma-agent-hub -- \
     redis-cli info memory
   
   # Clear cache if needed (CAUTION: impacts active sessions)
   kubectl exec -it deployment/redis -n soma-agent-hub -- \
     redis-cli flushdb
   ```

### 4.3 Vector Storage Failures

**Symptoms**: Vector operations return errors

**Diagnosis**:
```bash
# Check Qdrant collections
kubectl exec -it deployment/qdrant -n soma-agent-hub -- \
  curl http://localhost:6333/collections

# Check collection health
kubectl exec -it deployment/qdrant -n soma-agent-hub -- \
  curl http://localhost:6333/collections/{collection_name}
```

**Solutions**:

1. **Recreate Collection**:
   ```bash
   # Delete problematic collection
   kubectl exec -it deployment/qdrant -n soma-agent-hub -- \
     curl -X DELETE http://localhost:6333/collections/{collection_name}
   
   # Recreate with proper configuration
   kubectl exec -it deployment/qdrant -n soma-agent-hub -- \
     curl -X PUT http://localhost:6333/collections/{collection_name} \
     -H "Content-Type: application/json" \
     -d '{"vectors": {"size": 1536, "distance": "Cosine"}}'
   ```

2. **Check Disk Space**:
   ```bash
   # Check Qdrant storage usage
   kubectl exec -it deployment/qdrant -n soma-agent-hub -- df -h /qdrant/storage
   
   # Clean up old data if needed
   kubectl exec -it deployment/qdrant -n soma-agent-hub -- \
     find /qdrant/storage -name "*.log" -mtime +7 -delete
   ```

## 5. Remediation Steps

### Immediate Actions

1. **Restart Service**:
   ```bash
   kubectl rollout restart deployment/memory-gateway -n soma-agent-hub
   kubectl rollout status deployment/memory-gateway -n soma-agent-hub
   ```

2. **Scale Up for High Load**:
   ```bash
   kubectl scale deployment memory-gateway --replicas=3 -n soma-agent-hub
   ```

3. **Emergency Bypass** (if critical):
   ```bash
   # Temporarily disable memory storage in agents
   kubectl patch configmap agent-config -n soma-agent-hub -p '
   {
     "data": {
       "MEMORY_ENABLED": "false"
     }
   }'
   ```

### Recovery Validation

```bash
# Verify service health
curl http://localhost:8080/health

# Test vector operations
curl -X POST http://localhost:8080/collections/test/points \
  -H "Content-Type: application/json" \
  -d '{"points": [{"id": 999, "vector": [0.1, 0.2, 0.3], "payload": {"test": true}}]}'

# Test search functionality
curl -X POST http://localhost:8080/collections/test/points/search \
  -H "Content-Type: application/json" \
  -d '{"vector": [0.1, 0.2, 0.3], "limit": 5}'

# Clean up test data
curl -X DELETE http://localhost:8080/collections/test/points/999
```

## 6. Escalation

**Escalate if**:
- Service doesn't recover within 15 minutes
- Data corruption is suspected
- Multiple dependent services are affected

**Escalation Path**:
1. Secondary On-Call Engineer
2. Platform Engineering Team Lead
3. Engineering Manager

**Information to Provide**:
- Alert details and timeline
- Diagnostic command outputs
- Recent deployment history
- Impact assessment

## 7. Prevention & Monitoring

### Monitoring Improvements
```yaml
# Additional alerts to consider
- alert: MemoryGatewayVectorStorageFull
  expr: qdrant_collection_vectors_count > 1000000
  for: 5m
  
- alert: MemoryGatewayRedisMemoryHigh
  expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.8
  for: 10m
```

### Capacity Planning
- Monitor vector storage growth trends
- Plan for Redis memory scaling
- Set up automated collection cleanup

### Operational Improvements
- Implement circuit breakers for external dependencies
- Add retry logic with exponential backoff
- Improve health check granularity