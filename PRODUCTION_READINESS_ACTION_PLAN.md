# SOMAGENTHUB: PRODUCTION READINESS ACTION PLAN

**Based on**: Truthful audit of actual implementation vs. claims  
**Objective**: Close critical gaps in 3 phases (Week 1-4)  
**Mandate**: NO scaffolding, NO templates, ONLY real implementations

---

## 🎯 PHASE 1-NEXT: GOVERNANCE LAYER (Week 1-2)

### Critical Blockers

#### 1. OpenFGA Authorization Model
**Status**: ✗ MISSING (only infrastructure deployed)  
**What's needed**: Role/relationship/permission model

```fga
# File: infra/openfga/model.fga

model
  schema 1.1

type user
type organization
  relations
    define admin: [user]
    define member: [user]
type project
  relations
    define admin: [user, organization#admin]
    define maintainer: [user]
    define developer: [user] 
    define viewer: [user]
    define owner: [organization]
type agent
  relations
    define parent: [project]
    define can_execute: [user, agent]
    define can_read: [user]
    define can_write: [user]
    define owner: [user] or owner from parent

type resource
  relations
    define parent: [project]
    define can_use: [user]

type service
  relations
    define api_key_holder: [user]
    define can_invoke: [service, agent]
    define admin: [user]

# Permissions
define can_admin_org: admin
define is_member: member
define can_edit_project: admin or maintainer
define can_run_agent: developer or admin from parent
define can_deploy: admin or maintainer
```

**Acceptance Criteria**:
- [ ] Model file exists and is valid OpenFGA syntax
- [ ] Tested against common authorization scenarios
- [ ] Integration with gateway-api for request validation
- [ ] Audit logs for authorization decisions

**Time Estimate**: 2-3 days

---

#### 2. Argo CD Application Definitions
**Status**: ✗ MISSING (only infrastructure deployed)  
**What's needed**: ArgoCD App manifests for all services

```yaml
# File: k8s/apps/gateway-api-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: gateway-api
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/somatechlat/somaAgentHub.git
    targetRevision: main
    path: k8s/services/gateway-api
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

# File: k8s/apps/orchestrator-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: orchestrator
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/somatechlat/somaAgentHub.git
    targetRevision: main
    path: k8s/services/orchestrator
  destination:
    server: https://kubernetes.default.svc
    namespace: soma-agent-hub
  syncPolicy:
    automated:
      prune: true
      selfHeal: true

# ... repeat for all services
```

**Acceptance Criteria**:
- [ ] Application manifest for each service (12+ total)
- [ ] Auto-sync enabled with health checks
- [ ] Argo events webhook configured
- [ ] Tested application sync

**Time Estimate**: 3-4 days

---

#### 3. Kafka Topic Configuration
**Status**: ✗ MISSING (only infrastructure deployed)  
**What's needed**: Topic definitions and producer/consumer groups

```yaml
# File: k8s/kafka/topics.yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: agent-events
  namespace: soma-agent-hub
spec:
  partitions: 3
  replicationFactor: 2
  config:
    retention.ms: 604800000  # 7 days
    cleanup.policy: delete
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: model-invocations
  namespace: soma-agent-hub
spec:
  partitions: 5
  replicationFactor: 2
  config:
    retention.ms: 2592000000  # 30 days
---
# Consumer group configuration
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaUser
metadata:
  name: agent-service
  namespace: soma-agent-hub
spec:
  authentication:
    type: tls
  authorization:
    type: simple
    acls:
      - resource:
          type: topic
          name: agent-events
        operations:
          - Write
      - resource:
          type: topic
          name: model-invocations
        operations:
          - Read
```

**Acceptance Criteria**:
- [ ] Topic definitions for all event types
- [ ] Consumer group ACLs configured
- [ ] Producer/consumer code updated
- [ ] End-to-end event flow tested

**Time Estimate**: 2-3 days

---

#### 4. Pod Security Standards Enforcement
**Status**: ✗ MISSING (only OPA policies exist)  
**What's needed**: PSS enforcement across namespaces

```yaml
# File: k8s/security/pod-security-standards.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: soma-agent-hub
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
---
apiVersion: v1
kind: Namespace
metadata:
  name: observability
  labels:
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/audit: restricted
---
# All pod definitions must have:
# - securityContext.runAsNonRoot: true
# - securityContext.readOnlyRootFilesystem: true
# - resources.requests and limits
# - no privileged containers
```

**Acceptance Criteria**:
- [ ] PSS labels on all namespaces
- [ ] Pod specs comply with restricted standards
- [ ] Audit logs for PSS violations
- [ ] No privileged containers deployed

**Time Estimate**: 1-2 days

---

#### 5. Network Policies
**Status**: ✗ MISSING (Istio policies exist, K8s NetworkPolicy missing)  
**What's needed**: Micro-segmentation via NetworkPolicy

```yaml
# File: k8s/network/network-policies.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: gateway-policy
  namespace: soma-agent-hub
spec:
  podSelector:
    matchLabels:
      app: gateway-api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-system
      ports:
        - protocol: TCP
          port: 10000
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: orchestrator
      ports:
        - protocol: TCP
          port: 10001
    - to:
        - podSelector:
            matchLabels:
              app: identity-service
      ports:
        - protocol: TCP
          port: 10002
    - to:
        - namespaceSelector: {}
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
---
# Repeat for each service with least-privilege rules
```

**Acceptance Criteria**:
- [ ] NetworkPolicy for each service
- [ ] Ingress/egress traffic flows verified
- [ ] Default deny rules enforced
- [ ] Tested with network analyzers

**Time Estimate**: 2-3 days

---

## 🔄 PHASE 2-NEXT: CHAOS ENGINEERING (Week 2-3)

### What's Missing: COMPLETE Chaos Engineering Layer

#### 1. Chaos Mesh Experiments

```yaml
# File: k8s/chaos/cpu-stress.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: StressChaos
metadata:
  name: gateway-cpu-stress
  namespace: soma-agent-hub
spec:
  action: stress
  mode: fixed
  value: "2"
  selector:
    namespaces:
      - soma-agent-hub
    labelSelectors:
      app: gateway-api
  stressors:
    cpu:
      workers: 4
      load: 100
  duration: 10m
  scheduler:
    cron: "0 2 * * *"  # Daily at 2 AM
---
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: orchestrator-latency
  namespace: soma-agent-hub
spec:
  action: delay
  mode: all
  selector:
    namespaces:
      - soma-agent-hub
    labelSelectors:
      app: orchestrator
  delay:
    latency: "100ms"
    jitter: "10ms"
  duration: 15m
  scheduler:
    interval: 12h
---
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: redis-pod-failure
  namespace: soma-agent-hub
spec:
  action: pod-kill
  mode: fixed
  value: "1"
  selector:
    namespaces:
      - soma-agent-hub
    labelSelectors:
      app: redis
  duration: 5m
  scheduler:
    cron: "0 3 * * *"  # Daily at 3 AM
```

**Acceptance Criteria**:
- [ ] Stress tests for CPU/memory exhaustion
- [ ] Latency/packet loss injection scenarios
- [ ] Pod failure simulations
- [ ] Tested end-to-end with SLO verification

**Time Estimate**: 4-5 days

---

#### 2. SLO/SLI Monitoring

```yaml
# File: infra/prometheus/recording-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: soma-slos
  namespace: monitoring
spec:
  groups:
    - name: soma_slis
      interval: 30s
      rules:
        - record: sli:requests_total:rate5m
          expr: |
            sum(rate(http_requests_total[5m]))
        
        - record: sli:errors_total:rate5m
          expr: |
            sum(rate(http_requests_total{status=~"5.."}[5m]))
        
        - record: sli:latency_p99:histogram_quantile
          expr: |
            histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
        
        - record: slo:availability:ratio
          expr: |
            (1 - (sli:errors_total:rate5m / sli:requests_total:rate5m)) * 100
        
        - record: slo:latency:ratio
          expr: |
            (sli:latency_p99:histogram_quantile < 0.5) * 100
---
# Alerting rules
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: soma-alerts
  namespace: monitoring
spec:
  groups:
    - name: soma_alerting
      rules:
        - alert: AvailabilitySLOBreach
          expr: slo:availability:ratio < 99.9
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Availability SLO breach: {{ $value }}%"
        
        - alert: LatencySLOBreach
          expr: sli:latency_p99:histogram_quantile > 0.5
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Latency SLO breach: p99 > 500ms"
```

**Acceptance Criteria**:
- [ ] SLI/SLO metrics defined for all critical services
- [ ] Recording rules configured and validated
- [ ] Alerting rules integrated with incident response
- [ ] SLO dashboard created in Grafana

**Time Estimate**: 3-4 days

---

#### 3. k6 Load Test Generation

```python
# File: scripts/generate_k6_tests.py
"""Generate executable k6 scripts from load_testing.py definitions."""

import json
from scripts.load_testing import LOAD_TESTS, LoadProfile

def generate_k6_script(test):
    """Generate k6 JavaScript test script from LoadTest definition."""
    
    k6_template = f"""
import http from 'k6/http';
import {{ check, sleep }} from 'k6';
import {{ Rate, Trend }} from 'k6/metrics';

// Custom metrics
const error_rate = new Rate('errors');
const request_duration = new Trend('request_duration');

export const options = {{
  stages: [
    {{ duration: '1m', target: {test.virtual_users} }},
    {{ duration: '{test.duration}', target: {test.virtual_users} }},
    {{ duration: '1m', target: 0 }},
  ],
  thresholds: {{
    'http_req_duration': ['p(99)<500'],
    'errors': ['rate<0.1'],
  }},
}};

export default function () {{
  const response = http.get('{test.target_url}');
  
  check(response, {{
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  }}) || error_rate.add(1);
  
  request_duration.add(response.timings.duration);
  
  sleep(1);
}}
"""
    
    return k6_template

# Generate all k6 scripts
for test in LOAD_TESTS:
    script = generate_k6_script(test)
    filename = f"scripts/k6/{test.name}.js"
    with open(filename, "w") as f:
        f.write(script)
    print(f"Generated: {filename}")
```

**Acceptance Criteria**:
- [ ] k6 script generator implemented and tested
- [ ] All load profiles have executable scripts
- [ ] Scripts pass k6 validation
- [ ] Load tests executable via CI/CD

**Time Estimate**: 2 days

---

## ✅ PHASE 3-NEXT: INTEGRATION & VALIDATION (Week 3-4)

### 1. End-to-End Test Suite

```python
# File: tests/e2e/test_authorization_flow.py
def test_authorization_with_openfga():
    """Verify OpenFGA authorization model works end-to-end."""
    # Create user, organization, project
    user = create_user("alice@example.com")
    org = create_organization("ACME Corp")
    project = create_project(org, "Agent Platform")
    
    # Assign roles
    assign_role(user, org, "member")
    assign_role(user, project, "developer")
    
    # Test authorization checks
    assert can_run_agent(user, project) == True
    assert can_deploy_service(user, project) == False
    assert can_edit_project(user, project) == True
```

---

### 2. Production Readiness Checklist

```markdown
# Production Readiness Checklist

## Authorization & Governance
- [ ] OpenFGA model defined and tested
- [ ] Argo CD apps syncing services
- [ ] All authorization decisions logged

## Network Security
- [ ] NetworkPolicies restricting traffic
- [ ] Istio AuthorizationPolicies enforced
- [ ] Audit logs for denials

## Event Pipeline
- [ ] Kafka topics created
- [ ] Producers/consumers integrated
- [ ] Backpressure handled

## Reliability
- [ ] Chaos experiments running daily
- [ ] SLOs monitored and alerting
- [ ] Incident runbooks automated

## Operations
- [ ] Load tests generating data
- [ ] Performance baselines established
- [ ] Cost optimization implemented
```

---

## 📊 SUCCESS CRITERIA

### Week 1 (Governance)
- [ ] OpenFGA model deployed and authorized
- [ ] Argo CD syncing 12+ services
- [ ] NetworkPolicies enforcing least privilege
- [ ] PSS labels on all namespaces

### Week 2-3 (Chaos & Monitoring)
- [ ] Chaos Mesh experiments running
- [ ] SLI/SLO metrics in Prometheus
- [ ] k6 load tests executable
- [ ] Incident alerts configured

### Week 4 (Validation)
- [ ] E2E tests passing (auth, events, deployment)
- [ ] Production readiness checklist 100% complete
- [ ] System bootable and stable for 24h under chaos

---

## 💰 Resource Estimates

| Phase | Task | Dev Days | DevOps Days | Total |
|-------|------|----------|------------|-------|
| 1 | OpenFGA Model | 2 | 1 | 3 |
| 1 | Argo CD Apps | 2 | 2 | 4 |
| 1 | Kafka Topics | 1.5 | 1.5 | 3 |
| 1 | Pod Security | 1 | 1 | 2 |
| 1 | Network Policies | 1 | 1 | 2 |
| | **Phase 1 Total** | **7.5** | **6.5** | **14 days** |
| 2 | Chaos Experiments | 1 | 3 | 4 |
| 2 | SLO Monitoring | 1.5 | 1.5 | 3 |
| 2 | k6 Generation | 1 | 0.5 | 1.5 |
| | **Phase 2 Total** | **3.5** | **5** | **8.5 days** |
| 3 | E2E Tests | 3 | 1 | 4 |
| 3 | Documentation | 1 | 1 | 2 |
| | **Phase 3 Total** | **4** | **2** | **6 days** |
| | **GRAND TOTAL** | **15** | **13.5** | **28.5 days** |

---

## 🚀 Recommended Implementation Order

1. **Day 1-3**: OpenFGA authorization model
2. **Day 4-7**: Argo CD application definitions
3. **Day 8-10**: Kafka topics and consumer setup
4. **Day 11-12**: Pod Security Standards
5. **Day 13-14**: NetworkPolicy manifests
6. **Day 15-18**: Chaos Mesh experiments
7. **Day 19-21**: SLO/SLI monitoring
8. **Day 22-23**: k6 load test generation
9. **Day 24-28**: E2E testing and validation

---

**Report Generated**: Based on TRUTH_REPORT findings  
**Status**: Ready for implementation (all gaps identified and quantified)  
**Next Step**: Prioritize which gaps to close first based on business requirements
