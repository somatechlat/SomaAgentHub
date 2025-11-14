# RUNBOOK-003: Analytics Service Data Ingestion Issues

![Version](https://img.shields.io/badge/version-1.0.0-blue)

| Metadata | Value |
|---|---|
| **Alert Name** | `AnalyticsIngestionDown`, `AnalyticsIngestionLag` |
| **Severity** | P2 (High) - P3 (Medium) |
| **Owner** | Data Engineering Team |
| **Last Updated** | 2024-12-19 |

---

This runbook covers troubleshooting the Analytics Service data ingestion pipeline which processes agent events and stores metrics in ClickHouse.

## 1. Service Overview

**Analytics Service** processes:
- Agent action events from Kafka
- Workflow execution metrics
- Real-time performance data
- Business intelligence aggregations

**Data Flow**:
```
Agent Events → Kafka Topics → Analytics Service → ClickHouse
                    ↓
              Flink Processing → Real-time Metrics → Redis
```

**Dependencies**:
- Kafka (event streaming)
- ClickHouse (analytics database)
- Redis (real-time metrics cache)
- Flink (stream processing)

## 2. Common Alerts

### AnalyticsIngestionDown
**Trigger**: No events processed for >10 minutes
**Impact**: Loss of analytics data, missing business metrics

### AnalyticsIngestionLag
**Trigger**: Consumer lag >1000 messages for >15 minutes
**Impact**: Delayed analytics, stale dashboards

### ClickHouseConnectionFailed
**Trigger**: Database connection failures
**Impact**: Data loss, failed ingestion

### KafkaConsumerError
**Trigger**: Kafka consumer errors or restarts
**Impact**: Event processing interruption

## 3. Triage & Diagnosis

### Initial Checks
```bash
# Check analytics service status
kubectl get pods -n soma-agent-hub -l app=analytics-service

# Check Kafka topics and consumer groups
kubectl exec -it kafka-0 -n soma-agent-hub -- \
  kafka-topics --list --bootstrap-server localhost:9092

# Check ClickHouse connectivity
kubectl exec -it clickhouse-0 -n soma-agent-hub -- \
  clickhouse-client --query "SELECT 1"
```

### Diagnostic Steps

#### 3.1 Check Service Health
```bash
export SERVICE_NAME="analytics-service"
export POD_NAME=$(kubectl get pods -n soma-agent-hub -l app=$SERVICE_NAME -o jsonpath='{.items[0].metadata.name}')

# Check pod status
kubectl get pod $POD_NAME -n soma-agent-hub

# Check service logs
kubectl logs $POD_NAME -n soma-agent-hub --tail=100
```

#### 3.2 Kafka Consumer Analysis
```bash
# Check consumer group status
kubectl exec -it kafka-0 -n soma-agent-hub -- \
  kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group analytics-consumer --describe

# Check topic message counts
kubectl exec -it kafka-0 -n soma-agent-hub -- \
  kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic agent.actions --time -1

# Monitor real-time message flow
kubectl exec -it kafka-0 -n soma-agent-hub -- \
  kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic agent.actions --from-beginning --max-messages 10
```

#### 3.3 ClickHouse Database Health
```bash
# Check ClickHouse system status
kubectl exec -it clickhouse-0 -n soma-agent-hub -- \
  clickhouse-client --query "SELECT * FROM system.processes"

# Check table sizes and recent data
kubectl exec -it clickhouse-0 -n soma-agent-hub -- \
  clickhouse-client --query "
    SELECT 
      table,
      formatReadableSize(sum(bytes)) as size,
      sum(rows) as rows,
      max(modification_time) as last_modified
    FROM system.parts 
    WHERE database = 'somaagent'
    GROUP BY table
    ORDER BY sum(bytes) DESC"

# Check recent ingestion
kubectl exec -it clickhouse-0 -n soma-agent-hub -- \
  clickhouse-client --query "
    SELECT 
      toStartOfMinute(timestamp) as minute,
      count(*) as events
    FROM somaagent.agent_metrics 
    WHERE timestamp >= now() - INTERVAL 1 HOUR
    GROUP BY minute
    ORDER BY minute DESC
    LIMIT 10"
```

#### 3.4 Flink Stream Processing
```bash
# Check Flink job status
kubectl port-forward svc/flink-jobmanager 8082:8082 -n soma-agent-hub &
curl http://localhost:8082/jobs

# Check job metrics
curl http://localhost:8082/jobs/{job-id}/metrics

# Check Flink logs
kubectl logs -l app=flink-taskmanager -n soma-agent-hub --tail=50
```

## 4. Common Issues & Solutions

### 4.1 Kafka Consumer Lag

**Symptoms**: High consumer lag, delayed data processing

**Diagnosis**:
```bash
# Check consumer lag details
kubectl exec -it kafka-0 -n soma-agent-hub -- \
  kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group analytics-consumer --describe

# Check partition distribution
kubectl exec -it kafka-0 -n soma-agent-hub -- \
  kafka-topics --bootstrap-server localhost:9092 \
  --topic agent.actions --describe
```

**Solutions**:

1. **Scale Consumer Instances**:
   ```bash
   # Increase analytics service replicas
   kubectl scale deployment analytics-service --replicas=3 -n soma-agent-hub
   
   # Verify consumer rebalancing
   kubectl logs -l app=analytics-service -n soma-agent-hub | grep "partition.assignment"
   ```

2. **Increase Kafka Partitions**:
   ```bash
   # Add more partitions (cannot be decreased)
   kubectl exec -it kafka-0 -n soma-agent-hub -- \
     kafka-topics --bootstrap-server localhost:9092 \
     --topic agent.actions --alter --partitions 6
   ```

3. **Optimize Consumer Configuration**:
   ```bash
   # Update consumer settings via ConfigMap
   kubectl patch configmap analytics-config -n soma-agent-hub -p '
   {
     "data": {
       "KAFKA_FETCH_MIN_BYTES": "1048576",
       "KAFKA_FETCH_MAX_WAIT_MS": "500",
       "KAFKA_MAX_POLL_RECORDS": "1000"
     }
   }'
   
   # Restart service to apply changes
   kubectl rollout restart deployment/analytics-service -n soma-agent-hub
   ```

### 4.2 ClickHouse Ingestion Failures

**Symptoms**: Database connection errors, failed inserts

**Diagnosis**:
```bash
# Check ClickHouse error logs
kubectl logs clickhouse-0 -n soma-agent-hub | grep -i error

# Check disk space
kubectl exec -it clickhouse-0 -n soma-agent-hub -- df -h

# Check memory usage
kubectl exec -it clickhouse-0 -n soma-agent-hub -- \
  clickhouse-client --query "SELECT * FROM system.metrics WHERE metric LIKE '%Memory%'"
```

**Solutions**:

1. **Connection Pool Issues**:
   ```bash
   # Check active connections
   kubectl exec -it clickhouse-0 -n soma-agent-hub -- \
     clickhouse-client --query "SELECT * FROM system.processes"
   
   # Restart analytics service to reset connections
   kubectl rollout restart deployment/analytics-service -n soma-agent-hub
   ```

2. **Disk Space Issues**:
   ```bash
   # Clean old partitions
   kubectl exec -it clickhouse-0 -n soma-agent-hub -- \
     clickhouse-client --query "
       ALTER TABLE somaagent.agent_metrics 
       DROP PARTITION '202412' -- Adjust date as needed"
   
   # Optimize tables
   kubectl exec -it clickhouse-0 -n soma-agent-hub -- \
     clickhouse-client --query "OPTIMIZE TABLE somaagent.agent_metrics FINAL"
   ```

3. **Performance Tuning**:
   ```bash
   # Increase ClickHouse resources
   kubectl patch statefulset clickhouse -n soma-agent-hub -p '
   {
     "spec": {
       "template": {
         "spec": {
           "containers": [{
             "name": "clickhouse",
             "resources": {
               "requests": {"memory": "4Gi", "cpu": "2000m"},
               "limits": {"memory": "8Gi", "cpu": "4000m"}
             }
           }]
         }
       }
     }
   }'
   ```

### 4.3 Flink Processing Issues

**Symptoms**: Stream processing failures, checkpoint errors

**Diagnosis**:
```bash
# Check Flink job status
curl http://localhost:8082/jobs | jq '.jobs[] | {id: .id, status: .status}'

# Check job exceptions
curl http://localhost:8082/jobs/{job-id}/exceptions

# Check checkpoint status
curl http://localhost:8082/jobs/{job-id}/checkpoints
```

**Solutions**:

1. **Restart Failed Jobs**:
   ```bash
   # Cancel and restart job
   curl -X PATCH http://localhost:8082/jobs/{job-id}?mode=cancel
   
   # Redeploy Flink job
   kubectl delete job flink-analytics-job -n soma-agent-hub
   kubectl apply -f k8s/flink/analytics-job.yaml
   ```

2. **Scale Flink Resources**:
   ```bash
   # Increase TaskManager replicas
   kubectl scale deployment flink-taskmanager --replicas=3 -n soma-agent-hub
   
   # Increase parallelism
   kubectl patch configmap flink-config -n soma-agent-hub -p '
   {
     "data": {
       "parallelism.default": "4",
       "taskmanager.memory.process.size": "2g"
     }
   }'
   ```

### 4.4 Data Quality Issues

**Symptoms**: Missing data, incorrect metrics, schema errors

**Diagnosis**:
```bash
# Check for data gaps
kubectl exec -it clickhouse-0 -n soma-agent-hub -- \
  clickhouse-client --query "
    SELECT 
      toStartOfHour(timestamp) as hour,
      count(*) as events,
      countIf(success = 1) as successful,
      countIf(success = 0) as failed
    FROM somaagent.agent_metrics 
    WHERE timestamp >= now() - INTERVAL 24 HOUR
    GROUP BY hour
    ORDER BY hour DESC"

# Check for schema violations
kubectl logs -l app=analytics-service -n soma-agent-hub | grep -i "schema\|validation\|error"
```

**Solutions**:

1. **Data Validation**:
   ```bash
   # Enable strict schema validation
   kubectl patch configmap analytics-config -n soma-agent-hub -p '
   {
     "data": {
       "STRICT_SCHEMA_VALIDATION": "true",
       "DROP_INVALID_RECORDS": "false"
     }
   }'
   ```

2. **Reprocess Data**:
   ```bash
   # Reset consumer to reprocess recent data
   kubectl exec -it kafka-0 -n soma-agent-hub -- \
     kafka-consumer-groups --bootstrap-server localhost:9092 \
     --group analytics-consumer --reset-offsets \
     --to-datetime 2024-12-19T10:00:00.000 \
     --topic agent.actions --execute
   ```

## 5. Remediation Steps

### Immediate Actions

1. **Restart Analytics Service**:
   ```bash
   kubectl rollout restart deployment/analytics-service -n soma-agent-hub
   kubectl rollout status deployment/analytics-service -n soma-agent-hub
   ```

2. **Clear Consumer Group (if corrupted)**:
   ```bash
   # Stop consumers first
   kubectl scale deployment analytics-service --replicas=0 -n soma-agent-hub
   
   # Delete consumer group
   kubectl exec -it kafka-0 -n soma-agent-hub -- \
     kafka-consumer-groups --bootstrap-server localhost:9092 \
     --group analytics-consumer --delete
   
   # Restart consumers
   kubectl scale deployment analytics-service --replicas=2 -n soma-agent-hub
   ```

3. **Emergency Data Recovery**:
   ```bash
   # Backup current state
   kubectl exec -it clickhouse-0 -n soma-agent-hub -- \
     clickhouse-client --query "
       CREATE TABLE somaagent.agent_metrics_backup AS 
       SELECT * FROM somaagent.agent_metrics 
       WHERE timestamp >= today() - 1"
   
   # Restore from backup if needed
   kubectl exec -it clickhouse-0 -n soma-agent-hub -- \
     clickhouse-client --query "
       INSERT INTO somaagent.agent_metrics 
       SELECT * FROM somaagent.agent_metrics_backup"
   ```

### Recovery Validation

```bash
# Verify data ingestion resumed
kubectl exec -it clickhouse-0 -n soma-agent-hub -- \
  clickhouse-client --query "
    SELECT count(*) as recent_events
    FROM somaagent.agent_metrics 
    WHERE timestamp >= now() - INTERVAL 10 MINUTE"

# Check consumer lag is decreasing
kubectl exec -it kafka-0 -n soma-agent-hub -- \
  kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group analytics-consumer --describe

# Verify Flink jobs are running
curl http://localhost:8082/jobs | jq '.jobs[] | select(.status == "RUNNING")'

# Test analytics API endpoints
kubectl port-forward svc/analytics-service 8080:8000 -n soma-agent-hub &
curl http://localhost:8080/health
curl http://localhost:8080/metrics/agents/summary
```

## 6. Escalation

**Escalate if**:
- Data loss exceeds 1 hour
- Multiple downstream systems affected
- ClickHouse corruption suspected
- Recovery time exceeds 30 minutes

**Escalation Path**:
1. Data Engineering Team Lead
2. Platform Engineering Manager
3. CTO (for data loss >24 hours)

**Information to Provide**:
- Data loss timeframe and scope
- Consumer lag metrics
- ClickHouse table sizes and status
- Recent deployment or configuration changes

## 7. Prevention & Monitoring

### Enhanced Monitoring
```yaml
# Additional alerts
- alert: AnalyticsDataGap
  expr: increase(clickhouse_inserted_rows[5m]) == 0
  for: 10m
  
- alert: AnalyticsHighErrorRate
  expr: rate(analytics_processing_errors_total[5m]) > 0.1
  for: 5m

- alert: ClickHouseDiskSpaceHigh
  expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
  for: 5m
```

### Operational Improvements
- Implement data quality checks and alerts
- Set up automated consumer lag monitoring
- Create data retention policies
- Implement graceful degradation for analytics failures
- Add circuit breakers for external dependencies