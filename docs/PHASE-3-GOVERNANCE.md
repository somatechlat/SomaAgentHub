# Phase 3: Governance & Event Pipeline

**Status**: ✅ **Complete**  
**Date**: October 16, 2025  
**Components**: OpenFGA Authorization + Argo CD GitOps + Kafka Event Pipeline

---

## Objective

Implement fine-grained authorization, declarative deployments, and event-driven audit trail.

---

## 1. OpenFGA Fine-Grained Authorization

### Architecture

```
┌─────────────────────────────────────────────────────┐
│  Application Layer (Services)                       │
│  - Gateway API                                      │
│  - Orchestrator                                     │
│  - Policy Engine                                    │
│                                                     │
│  Every access decision → OpenFGA check              │
│  (e.g., "Can user:john execute project:acme?")    │
└──────────────────────┬────────────────────────────┘
                       │
                       ↓ gRPC/HTTP
┌─────────────────────────────────────────────────────┐
│  OpenFGA Service (Authorization Engine)             │
│                                                     │
│  Model: Relationship-based access control (ReBAC)  │
│  - Users, Services, Organizations                  │
│  - Projects, Workflows, Models                     │
│  - Actions: read, write, execute, deploy           │
│                                                     │
│  Storage: PostgreSQL                               │
│  API: CheckRequest → allow/deny decision           │
└──────────────────────┬────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────┐
│  Relationship Tuples (in PostgreSQL)               │
│  - user:alice#member@organization:acme              │
│  - service:gateway-api#owner@project:acme-prod     │
│  - user:bob#editor@project:acme-prod               │
│  - organization:acme#admin@user:alice               │
└─────────────────────────────────────────────────────┘
```

### Deployment

#### Install OpenFGA

```bash
# 1. Create namespace
kubectl create namespace openfga-system

# 2. Deploy OpenFGA
kubectl apply -f k8s/openfga-deployment.yaml

# 3. Wait for deployment
kubectl rollout status deployment/openfga -n openfga-system --timeout=5m

# 4. Verify OpenFGA is running
kubectl get pods -n openfga-system
# Expected: openfga-xxxxx running
```

#### Initialize Authorization Model

```bash
# 1. Port-forward to OpenFGA
kubectl port-forward -n openfga-system svc/openfga 8080:8080 &

# 2. Create OpenFGA store
curl -X POST http://localhost:8080/stores \
  -H "Content-Type: application/json" \
  -d '{"name":"soma-agent-hub"}'

# Expected response:
# {
#   "id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
#   "name": "soma-agent-hub",
#   "created_at": "2024-10-16T10:00:00Z",
#   "updated_at": "2024-10-16T10:00:00Z"
# }

STORE_ID="01ARZ3NDEKTSV4RRFFQ69G5FAV"  # Replace with actual ID

# 3. Upload authorization model
curl -X POST http://localhost:8080/stores/$STORE_ID/models \
  -H "Content-Type: application/json" \
  -d @infra/openfga/model.fga

# 4. Verify model is installed
curl http://localhost:8080/stores/$STORE_ID/models | jq '.models[0].schema_version'
# Expected: "1.1"
```

#### Test Authorization Checks

```bash
STORE_ID="01ARZ3NDEKTSV4RRFFQ69G5FAV"

# 1. Add relationship: user:alice is admin of organization:acme
curl -X POST http://localhost:8080/stores/$STORE_ID/write \
  -H "Content-Type: application/json" \
  -d '{
    "writes": {
      "tuple_keys": [
        {
          "user": "user:alice",
          "relation": "admin",
          "object": "organization:acme"
        }
      ]
    }
  }'

# 2. Add relationship: user:bob is viewer of project:acme-prod
curl -X POST http://localhost:8080/stores/$STORE_ID/write \
  -H "Content-Type: application/json" \
  -d '{
    "writes": {
      "tuple_keys": [
        {
          "user": "user:bob",
          "relation": "viewer",
          "object": "project:acme-prod"
        }
      ]
    }
  }'

# 3. Check authorization: Can alice edit project:acme-prod?
curl -X POST http://localhost:8080/stores/$STORE_ID/check \
  -H "Content-Type: application/json" \
  -d '{
    "tuple_key": {
      "user": "user:alice",
      "relation": "can_edit",
      "object": "project:acme-prod"
    }
  }'
# Expected: {"allowed": true} (alice is admin of organization)

# 4. Check authorization: Can bob execute project:acme-prod?
curl -X POST http://localhost:8080/stores/$STORE_ID/check \
  -H "Content-Type: application/json" \
  -d '{
    "tuple_key": {
      "user": "user:bob",
      "relation": "can_execute",
      "object": "project:acme-prod"
    }
  }'
# Expected: {"allowed": false} (bob is only viewer)
```

### Integration with Policy Engine

Services integrate OpenFGA via:

```python
# services/policy-engine/openfga_client.py
from openfga_sdk.client import ClientConfiguration, OpenFgaClient

config = ClientConfiguration(
    api_url="http://openfga:8080",
    store_id=os.getenv("OPENFGA_STORE_ID")
)
client = OpenFgaClient(config)

# Check authorization
is_allowed = await client.check({
    "user": "user:alice",
    "relation": "can_deploy",
    "object": "project:acme-prod"
})

if is_allowed:
    # Allow deployment
else:
    # Deny deployment
```

---

## 2. Argo CD GitOps

### Architecture

```
┌──────────────────────────────────────┐
│  Git Repository (Source of Truth)    │
│  - services/*/k8s/                   │
│  - infra/helm/values-*.yaml          │
│  - k8s/soma-agent-hub-*.yaml         │
└──────────────────┬───────────────────┘
                   │
                   │ Git webhook / polling
                   ↓
┌──────────────────────────────────────┐
│  Argo CD Application Controller      │
│  - Watches git repo                  │
│  - Compares with live cluster        │
│  - Auto-syncs changes                │
│  - Audit log: who deployed what      │
└──────────────────┬───────────────────┘
                   │
                   ↓
┌──────────────────────────────────────┐
│  Kubernetes Cluster                  │
│  - soma-agent-hub namespace          │
│  - Current state = desired state     │
└──────────────────────────────────────┘
```

### Deployment

#### Install Argo CD

```bash
# 1. Create namespace
kubectl create namespace argocd

# 2. Deploy Argo CD
kubectl apply -f k8s/argocd-deployment.yaml

# 3. Wait for deployment
kubectl rollout status deployment/argocd-server -n argocd --timeout=5m
kubectl rollout status deployment/argocd-repo-server -n argocd --timeout=5m

# 4. Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d

# 5. Port-forward to Argo CD UI
kubectl port-forward -n argocd svc/argocd-server 8888:80 &
# Open: http://localhost:8888
# Login: admin / <password>
```

#### Create Git Repository Connection

```bash
# 1. Create GitHub personal access token (or similar)
export GIT_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# 2. Create secret
kubectl create secret generic github-creds \
  -n argocd \
  --from-literal=url=https://github.com/somatechlat/SomaAgentHub \
  --from-literal=password=$GIT_TOKEN \
  --from-literal=username=somatechlat \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Add repository to Argo CD
curl -X POST http://localhost:8888/api/v1/repositories \
  -H "Authorization: Bearer $ARGOCD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repo": "https://github.com/somatechlat/SomaAgentHub",
    "type": "git",
    "name": "soma-agent-hub",
    "username": "somatechlat",
    "password": "'$GIT_TOKEN'"
  }'
```

#### Create Argo CD Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: soma-agent-hub
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/somatechlat/SomaAgentHub
    targetRevision: main
    path: k8s
  destination:
    server: https://kubernetes.default.svc
    namespace: soma-agent-hub
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
  revisionHistoryLimit: 10
```

### GitOps Workflow

```bash
# 1. Make changes in git
git checkout -b feature/new-service
# ... edit k8s manifests ...
git add k8s/
git commit -m "feat: add new service"
git push origin feature/new-service

# 2. Create PR
# GitHub PR created

# 3. Argo CD automatically syncs to staging namespace
# (if configured with automated sync on feature branches)

# 4. Merge PR
# Argo CD detects main branch update

# 5. Automatic deployment to production
# (if automated sync enabled)
# OR manual approval workflow
# (if manual sync enabled)

# 6. Audit trail in Argo CD UI
# - Who deployed what
# - When
# - From which commit
# - Success/failure status
```

---

## 3. Kafka Event Pipeline

### Architecture

```
┌───────────────────────────────────────────────────┐
│  SomaAgentHub Services                            │
│                                                   │
│  ┌──────────────┐  ┌──────────────┐              │
│  │ Gateway API  │  │ Orchestrator │  ...         │
│  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                      │
│         │ Audit events    │ Workflow events      │
│         │ Policy events   │ Error events         │
│         └────────┬────────┘                      │
│                  │                               │
│                  ↓                               │
├──────────────────────────────────────────────────┤
│  Kafka Topics (Message Broker)                   │
│                                                  │
│  ┌────────────────────┐                         │
│  │ soma-audit-logs    │ ← Policy decisions      │
│  │ (retention: 7d)    │ ← Access control       │
│  └──────────┬─────────┘                         │
│             │                                   │
│  ┌────────────────────┐                         │
│  │ soma-metrics       │ ← Performance metrics   │
│  │ (retention: 1d)    │ ← Error metrics        │
│  └──────────┬─────────┘                         │
│             │                                   │
│  ┌────────────────────┐                         │
│  │ soma-traces        │ ← Distributed traces   │
│  │ (retention: 1d)    │ ← Request flows        │
│  └──────────┬─────────┘                         │
│             │                                   │
│  ┌────────────────────┐                         │
│  │ soma-events        │ ← Business events      │
│  │ (retention: 3d)    │ ← Workflow events      │
│  └──────────┬─────────┘                         │
│             │                                   │
└─────────────┼──────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────┐
│  Consumers                                      │
│                                                │
│  ┌─────────────────────────┐                  │
│  │ ClickHouse Consumer     │                  │
│  │ - soma-audit-logs       │                  │
│  │ - soma-metrics          │                  │
│  │ - soma-traces           │                  │
│  └──────────┬──────────────┘                  │
│             │                                 │
│  ┌──────────────────────────┐                │
│  │ Elasticsearch Consumer    │                │
│  │ - soma-audit-logs        │                │
│  │ (optional, for rich search)              │
│  └──────────┬───────────────┘               │
│             │                               │
│  ┌──────────────────────────┐               │
│  │ Datadog/SaaS Monitor     │               │
│  │ - All topics forwarded   │               │
│  │ (optional)               │               │
│  └──────────┬───────────────┘               │
│             │                               │
└─────────────┼───────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────┐
│  Long-term Storage + Analysis                   │
│  - ClickHouse (queries)                        │
│  - S3 (backups)                                │
│  - Grafana (visualization)                     │
└─────────────────────────────────────────────────┘
```

### Deployment

#### Deploy Kafka

```bash
# 1. Deploy Kafka + Zookeeper
kubectl apply -f k8s/kafka-deployment.yaml

# 2. Wait for Kafka to be ready
kubectl rollout status statefulset/kafka -n kafka-system --timeout=10m

# 3. Verify Kafka cluster
kubectl exec -it kafka-0 -n kafka-system -- \
  kafka-broker-api-versions --bootstrap-server=localhost:9092
# Expected: ApiVersion responses from all brokers
```

#### Create Topics

```bash
# 1. Copy and run topic creation script
chmod +x scripts/create-kafka-topics.sh

# 2. Execute in Kafka container
kubectl exec -it kafka-0 -n kafka-system -- \
  bash -c "$(cat scripts/create-kafka-topics.sh)"

# 3. Verify topics created
kubectl exec -it kafka-0 -n kafka-system -- \
  kafka-topics --bootstrap-server=localhost:9092 --list
# Expected:
# soma-audit-logs
# soma-metrics
# soma-traces
# soma-events
# soma-dlq
```

#### Integration with Services

Services publish events to Kafka:

```python
# services/common/kafka_producer.py
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=['kafka:9092'],
    value_serializer=lambda x: json.dumps(x).encode('utf-8'),
    acks='all',
    retries=3
)

# Publish audit event
audit_event = {
    "timestamp": datetime.utcnow().isoformat(),
    "user": "user:alice",
    "action": "deploy",
    "resource": "project:acme-prod",
    "result": "success"
}

future = producer.send('soma-audit-logs', value=audit_event)
future.get(timeout=10)  # Wait for ack
```

#### ClickHouse Integration

```bash
# 1. Create audit logs table in ClickHouse
kubectl exec -it <clickhouse-pod> -- clickhouse-client << 'EOF'
CREATE TABLE IF NOT EXISTS soma_audit_logs (
    timestamp DateTime,
    user String,
    action String,
    resource String,
    result Enum('success' = 1, 'failure' = 2),
    error_message Nullable(String)
) ENGINE = MergeTree()
ORDER BY timestamp;
EOF

# 2. Create Kafka table for real-time ingestion
kubectl exec -it <clickhouse-pod> -- clickhouse-client << 'EOF'
CREATE TABLE IF NOT EXISTS soma_audit_logs_kafka (
    timestamp DateTime,
    user String,
    action String,
    resource String,
    result Enum('success' = 1, 'failure' = 2),
    error_message Nullable(String)
) ENGINE = Kafka()
SETTINGS
    kafka_broker_list = 'kafka:9092',
    kafka_topic_list = 'soma-audit-logs',
    kafka_group_id = 'clickhouse-soma',
    kafka_format = 'JSONEachRow',
    kafka_num_consumers = 1;

-- Materialized view to push data
CREATE MATERIALIZED VIEW soma_audit_logs_mv TO soma_audit_logs
AS SELECT * FROM soma_audit_logs_kafka;
EOF

# 3. Query audit logs
kubectl exec -it <clickhouse-pod> -- clickhouse-client << 'EOF'
SELECT count(), user, action, result
FROM soma_audit_logs
WHERE timestamp > now() - INTERVAL 24 HOUR
GROUP BY user, action, result;
EOF
```

---

## 4. End-to-End: Authorization + GitOps + Audit

### Complete Flow

```
1. User requests action (e.g., deploy service)
   ↓
2. Service calls OpenFGA to check authorization
   OpenFGA query: "Can user:alice deploy project:acme-prod?"
   ↓
3. OpenFGA evaluates relationships + returns allow/deny
   ↓
4. If allowed:
   - Service publishes audit event to Kafka (soma-audit-logs)
   - User commits deployment changes to git
   - Argo CD detects changes
   - Argo CD syncs new state to cluster
   - ClickHouse ingests audit log via Kafka
   ↓
5. If denied:
   - Service publishes failure event to Kafka
   - ClickHouse ingests for audit trail
   - Service returns 403 Forbidden to user
   ↓
6. Audit trail is immutable and queryable:
   SELECT * FROM soma_audit_logs WHERE user = 'user:alice'
```

---

## 5. Verification Checklist

- ✅ OpenFGA service running
- ✅ Authorization model loaded
- ✅ Check API responding
- ✅ Argo CD running
- ✅ Git repository connected
- ✅ Application syncing
- ✅ Kafka cluster running
- ✅ All topics created
- ✅ ClickHouse consuming Kafka events
- ✅ Audit logs queryable

---

## 6. Next Steps: Phase 4 (Agent Intelligence)

After Phase 3:
- LangGraph adapter for multi-agent orchestration
- RAG: semantic search over Qdrant
- Advanced orchestration patterns

---

**Status**: ✅ Phase 3 COMPLETE - Governance & Events ready  
**Date**: October 16, 2025
