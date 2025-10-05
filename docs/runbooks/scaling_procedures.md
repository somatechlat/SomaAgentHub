# Scaling Procedures Runbook

## Overview
Procedures for scaling SomaGent infrastructure horizontally and vertically to meet demand.

## Scaling Decision Framework

### When to Scale

#### Scale UP (Horizontal - Add replicas)
- **CPU utilization** > 70% sustained for 10 minutes
- **Memory utilization** > 80% sustained for 10 minutes
- **Request queue depth** > 100 sustained
- **Response time P95** > target SLA for 5 minutes
- **Concurrent users** approaching replica capacity

#### Scale DOWN (Reduce replicas)
- **CPU utilization** < 30% for 1 hour
- **Memory utilization** < 50% for 1 hour
- **Request queue depth** < 10
- **Cost optimization** opportunity identified

#### Scale OUT (Vertical - Increase resources)
- Memory-bound: Single process OOM errors
- CPU-bound: Single-threaded bottlenecks
- I/O-bound: Database connection pool exhaustion

---

## Service Scaling Matrix

| Service | Min Replicas | Max Replicas | CPU Target | Memory Limit | Scale Event |
|---------|--------------|--------------|------------|--------------|-------------|
| gateway-api | 3 | 20 | 70% | 2Gi | High traffic |
| orchestrator | 2 | 10 | 60% | 4Gi | Workflow spike |
| mao-service | 2 | 15 | 70% | 3Gi | Parallel workflows |
| tool-service | 3 | 25 | 70% | 2Gi | Tool invocation spike |
| kamachiq-service | 2 | 10 | 60% | 8Gi | NL processing load |
| memory-gateway | 2 | 8 | 60% | 16Gi | RAG queries |
| constitution-service | 2 | 5 | 50% | 1Gi | Policy checks |
| policy-engine | 2 | 5 | 50% | 1Gi | Enforcement rules |
| billing-service | 1 | 3 | 50% | 1Gi | Month-end |
| marketplace-service | 1 | 5 | 50% | 2Gi | Package downloads |
| evolution-engine | 1 | 3 | 50% | 4Gi | Analysis jobs |
| voice-interface | 1 | 10 | 70% | 4Gi | Voice requests |

---

## Horizontal Scaling Procedures

### Manual Scaling

#### Scale Up
```bash
# Scale specific service
kubectl scale deployment/gateway-api --replicas=10 -n somagent-production

# Verify scaling
kubectl get pods -n somagent-production -l app=gateway-api

# Monitor rollout
kubectl rollout status deployment/gateway-api -n somagent-production

# Check pod distribution across nodes
kubectl get pods -n somagent-production -l app=gateway-api -o wide
```

#### Scale Down
```bash
# Gradually reduce replicas
kubectl scale deployment/gateway-api --replicas=5 -n somagent-production

# Wait for graceful shutdown (30s default)
sleep 30

# Verify no connection errors
kubectl logs deployment/gateway-api -n somagent-production --tail=100 | grep -i error
```

### Autoscaling (HPA - Horizontal Pod Autoscaler)

#### Configure HPA
```bash
# CPU-based autoscaling
kubectl autoscale deployment/gateway-api \
  --min=3 --max=20 --cpu-percent=70 \
  -n somagent-production

# View HPA status
kubectl get hpa -n somagent-production

# Example output:
# NAME          REFERENCE                TARGETS   MINPODS   MAXPODS   REPLICAS
# gateway-api   Deployment/gateway-api   45%/70%   3         20        5
```

#### Custom Metrics HPA
```yaml
# hpa-gateway-api-custom.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: gateway-api-custom
  namespace: somagent-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: gateway-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"  # Scale at 1000 req/s per pod
  - type: Pods
    pods:
      metric:
        name: workflow_queue_depth
      target:
        type: AverageValue
        averageValue: "50"  # Scale when queue > 50 per pod
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5min before scaling down
      policies:
      - type: Percent
        value: 50  # Max 50% scale down at once
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0  # Scale up immediately
      policies:
      - type: Percent
        value: 100  # Max double at once
        periodSeconds: 15
```

Apply:
```bash
kubectl apply -f hpa-gateway-api-custom.yaml
```

### Load Threshold Monitoring

#### Prometheus Queries
```promql
# Current replica count
count(up{job="gateway-api"})

# CPU utilization per pod
rate(container_cpu_usage_seconds_total{pod=~"gateway-api-.*"}[5m]) * 100

# Memory utilization per pod
container_memory_usage_bytes{pod=~"gateway-api-.*"} / 
container_spec_memory_limit_bytes{pod=~"gateway-api-.*"} * 100

# Request rate per pod
rate(http_requests_total{job="gateway-api"}[5m]) / 
count(up{job="gateway-api"})

# P95 latency
histogram_quantile(0.95, 
  rate(http_request_duration_seconds_bucket{job="gateway-api"}[5m])
)
```

---

## Vertical Scaling Procedures

### Increase Resource Limits

#### CPU and Memory
```bash
# Update deployment
kubectl set resources deployment/kamachiq-service \
  --requests=cpu=2,memory=8Gi \
  --limits=cpu=4,memory=16Gi \
  -n somagent-production

# Verify rollout
kubectl rollout status deployment/kamachiq-service -n somagent-production
```

#### Edit Deployment YAML
```yaml
# deployment-kamachiq.yaml
spec:
  template:
    spec:
      containers:
      - name: kamachiq-service
        resources:
          requests:
            cpu: "2000m"
            memory: "8Gi"
          limits:
            cpu: "4000m"
            memory: "16Gi"
```

Apply:
```bash
kubectl apply -f deployment-kamachiq.yaml
```

### Database Vertical Scaling

#### RDS (AWS)
```bash
# Modify instance class
aws rds modify-db-instance \
  --db-instance-identifier somagent-production-db \
  --db-instance-class db.r5.2xlarge \
  --apply-immediately

# Monitor modification
aws rds describe-db-instances \
  --db-instance-identifier somagent-production-db \
  --query 'DBInstances[0].DBInstanceStatus'
```

#### PostgreSQL Connection Pool
```bash
# Increase max_connections (requires restart)
aws rds modify-db-parameter-group \
  --db-parameter-group-name somagent-production \
  --parameters "ParameterName=max_connections,ParameterValue=500,ApplyMethod=pending-reboot"

# Reboot database (plan maintenance window)
aws rds reboot-db-instance \
  --db-instance-identifier somagent-production-db
```

### Redis Vertical Scaling

#### ElastiCache
```bash
# Modify node type
aws elasticache modify-cache-cluster \
  --cache-cluster-id somagent-production-redis \
  --cache-node-type cache.r5.2xlarge \
  --apply-immediately

# Monitor modification
aws elasticache describe-cache-clusters \
  --cache-cluster-id somagent-production-redis \
  --query 'CacheClusters[0].CacheClusterStatus'
```

---

## Database Scaling

### Read Replicas

#### Create Read Replica (PostgreSQL)
```bash
# AWS RDS
aws rds create-db-instance-read-replica \
  --db-instance-identifier somagent-production-db-replica-1 \
  --source-db-instance-identifier somagent-production-db \
  --db-instance-class db.r5.xlarge \
  --availability-zone us-east-1b

# Wait for availability
aws rds wait db-instance-available \
  --db-instance-identifier somagent-production-db-replica-1
```

#### Configure Application (Read/Write Split)
```python
# config.py
DATABASE_WRITE_URL = "postgresql://somagent:pwd@db-primary:5432/somagent"
DATABASE_READ_URLS = [
    "postgresql://somagent:pwd@db-replica-1:5432/somagent",
    "postgresql://somagent:pwd@db-replica-2:5432/somagent",
]

# database.py
from sqlalchemy import create_engine
import random

write_engine = create_engine(DATABASE_WRITE_URL)
read_engines = [create_engine(url) for url in DATABASE_READ_URLS]

def get_read_engine():
    return random.choice(read_engines)

# Usage
def get_projects():
    with get_read_engine().connect() as conn:
        return conn.execute("SELECT * FROM projects").fetchall()

def create_project(data):
    with write_engine.connect() as conn:
        conn.execute("INSERT INTO projects VALUES (...)")
```

### Connection Pool Scaling
```python
# Increase pool size for high concurrency
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=50,  # Default 5
    max_overflow=100,  # Default 10
    pool_pre_ping=True,  # Health check before use
    pool_recycle=3600  # Recycle connections after 1 hour
)
```

---

## Cache Scaling

### Redis Cluster Mode

#### Enable Cluster
```bash
# AWS ElastiCache
aws elasticache create-replication-group \
  --replication-group-id somagent-redis-cluster \
  --replication-group-description "SomaGent Redis Cluster" \
  --num-node-groups 3 \
  --replicas-per-node-group 2 \
  --cache-node-type cache.r5.large \
  --engine redis \
  --engine-version 7.0
```

### Cache Warming
```python
# Preload hot data on scale-up
def warm_cache():
    """Warm Redis cache after scaling."""
    logger.info("Warming cache...")
    
    # Preload frequently accessed data
    projects = db.query(Project).filter(Project.active == True).all()
    for project in projects:
        cache.set(f"project:{project.id}", project.to_dict(), ex=3600)
    
    # Preload tool capabilities
    tools = get_all_tools()
    for tool in tools:
        cache.set(f"tool:{tool.name}:capabilities", tool.capabilities, ex=7200)
    
    logger.info(f"Cache warmed with {len(projects)} projects, {len(tools)} tools")
```

---

## Load Balancer Scaling

### AWS ALB Target Group
```bash
# Increase healthy threshold for faster scaling
aws elbv2 modify-target-group \
  --target-group-arn arn:aws:elasticloadbalancing:... \
  --health-check-interval-seconds 10 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 2

# Increase deregistration delay for graceful shutdown
aws elbv2 modify-target-group-attributes \
  --target-group-arn arn:aws:elasticloadbalancing:... \
  --attributes Key=deregistration_delay.timeout_seconds,Value=60
```

### Nginx Upstream
```nginx
# /etc/nginx/conf.d/somagent.conf
upstream gateway_api {
    least_conn;  # Load balancing algorithm
    
    server gateway-api-1:8000 max_fails=3 fail_timeout=30s;
    server gateway-api-2:8000 max_fails=3 fail_timeout=30s;
    server gateway-api-3:8000 max_fails=3 fail_timeout=30s;
    # Add more as needed
    
    keepalive 100;  # Connection pooling
}

server {
    listen 80;
    
    location / {
        proxy_pass http://gateway_api;
        proxy_next_upstream error timeout http_502 http_503;
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

---

## Kubernetes Node Scaling

### Cluster Autoscaler

#### Install
```bash
helm install cluster-autoscaler autoscaler/cluster-autoscaler \
  --namespace kube-system \
  --set autoDiscovery.clusterName=somagent-production \
  --set awsRegion=us-east-1
```

#### Configure Node Groups
```bash
# AWS EKS
aws eks create-nodegroup \
  --cluster-name somagent-production \
  --nodegroup-name compute-nodes \
  --scaling-config minSize=3,maxSize=20,desiredSize=5 \
  --instance-types t3.large,t3.xlarge \
  --node-role arn:aws:iam::123456789:role/EKSNodeRole
```

### Manual Node Scaling
```bash
# Scale node group
aws eks update-nodegroup-config \
  --cluster-name somagent-production \
  --nodegroup-name compute-nodes \
  --scaling-config minSize=5,maxSize=30,desiredSize=10

# Verify
kubectl get nodes
```

---

## Scaling Playbooks

### High Traffic Event (Product Launch)

**1 Week Before:**
```bash
# Pre-scale infrastructure
kubectl scale deployment/gateway-api --replicas=15 -n somagent-production
kubectl scale deployment/tool-service --replicas=20 -n somagent-production

# Scale database
aws rds modify-db-instance --db-instance-class db.r5.4xlarge

# Warm caches
python scripts/warm_cache.py

# Load test
locust -f tests/performance/locust_scenarios.py --host=https://api.somagent.ai
```

**During Event:**
```bash
# Monitor metrics
watch -n 10 kubectl top pods -n somagent-production

# Monitor Prometheus
# - Request rate
# - Error rate
# - P95 latency
# - Database connections

# Adjust autoscaling if needed
kubectl patch hpa gateway-api --patch '{"spec":{"maxReplicas":30}}'
```

**After Event:**
```bash
# Gradually scale down over 24 hours
kubectl scale deployment/gateway-api --replicas=10 -n somagent-production
# Wait 4 hours
kubectl scale deployment/gateway-api --replicas=5 -n somagent-production
# Wait 4 hours
kubectl scale deployment/gateway-api --replicas=3 -n somagent-production
```

### Database Migration

**Before Migration:**
```bash
# Create read replica for zero-downtime
aws rds create-db-instance-read-replica ...

# Run migration on replica
DATABASE_URL=$REPLICA_URL python manage.py migrate

# Promote replica to primary
aws rds promote-read-replica --db-instance-identifier replica-1
```

---

## Cost Optimization

### Right-Sizing
```bash
# Analyze resource usage (last 7 days)
kubectl top pods -n somagent-production --sort-by=cpu
kubectl top pods -n somagent-production --sort-by=memory

# Recommendations
# If avg CPU < 30% → reduce requests
# If avg Memory < 50% → reduce limits
```

### Spot Instances
```yaml
# nodegroup-spot.yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: somagent-production
  region: us-east-1
nodeGroups:
  - name: spot-nodes
    instancesDistribution:
      instanceTypes: ["t3.large", "t3.xlarge", "t3a.large"]
      onDemandBaseCapacity: 2
      onDemandPercentageAboveBaseCapacity: 20
      spotInstancePools: 3
    desiredCapacity: 10
    minSize: 3
    maxSize: 30
```

---

## Monitoring Scaling Events

### Prometheus Alerts
```yaml
# infra/monitoring/scaling-alerts.yml
- alert: HighHorizontalScaling
  expr: |
    (count(up{job="gateway-api"}) - count(up{job="gateway-api"} offset 10m)) > 5
  for: 5m
  annotations:
    summary: "Rapid horizontal scaling detected"
    description: "Gateway API scaled by {{ $value }} replicas in 10 minutes"

- alert: MaxReplicasReached
  expr: |
    count(up{job="gateway-api"}) >= 20
  annotations:
    summary: "Max replicas reached for gateway-api"
    description: "Consider vertical scaling or architecture review"
```

---

## References
- [Incident Response](./incident_response.md)
- [Tool Health Monitoring](./tool_health_monitoring.md)
- [Kubernetes HPA Documentation](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [AWS RDS Scaling](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ModifyInstance.html)
