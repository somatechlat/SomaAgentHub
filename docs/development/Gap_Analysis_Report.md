# 📊 SomaAgent Gap Analysis Report
**Generated:** 2025-10-04  
**Scope:** Comprehensive comparison of Canonical Roadmap vs. Implemented Codebase  
**Status:** 🔴 CRITICAL GAPS IDENTIFIED - FOUNDATION INCOMPLETE

---

## 🎯 Executive Summary

### Current State Assessment
The codebase contains **12 FastAPI microservices** with varying levels of implementation maturity. Recent parallel sprint work delivered vertical slices (Policy Engine enhancements, Orchestrator streaming, Admin Console, Token Estimator), but **critical infrastructure and integration gaps remain unfilled**.

### Gap Severity Classification
- 🔴 **CRITICAL** (Blocks production deployment): 8 gaps
- 🟡 **HIGH** (Limits functionality): 12 gaps  
- 🟢 **MEDIUM** (Deferred features): 9 gaps

### Recommendation
**Shift focus from feature expansion to infrastructure stabilization.** Prioritize Sprint Wave 1 canonical roadmap completion before advancing to Wave 2/3 features.

---

## 🔴 CRITICAL GAPS (BLOCKERS)

### 1. Kafka Infrastructure Missing
**Roadmap Expectation:** Sprint 1A - Kafka/KRaft deployment with Helm charts  
**Current State:** 
- ✅ Helm chart exists (`k8s/helm/soma-agent`) with Kafka dependency declared
- ✅ `aiokafka` dependency in 5 service requirements.txt files
- ❌ **Kafka disabled in `values.yaml`** (`kafka.enabled: false`)
- ❌ No running Kafka cluster (local or K8s)
- ❌ No producer/consumer implementations wired to real brokers

**Impact:** 
- All async event-driven patterns blocked
- Orchestrator conversation events can't publish to topics
- Identity audit trail not persisting
- SLM async queue not operational
- Training mode audit events not flowing

**Evidence:**
```python
# services/orchestrator/app/api/conversation.py:103
# TODO: Wire to real Kafka producer when infrastructure available
```

**Fix Required:**
1. Enable Kafka in Helm `values.yaml` (`kafka.enabled: true`)
2. Deploy Kafka via Helm: `helm install soma k8s/helm/soma-agent -n soma-agent`
3. Wire producers in Orchestrator, Identity, Policy Engine to brokers
4. Validate topics auto-create or provision schemas

**Priority:** 🔴 P0 - Blocks all async workflows

---

### 2. Memory Gateway Not Integrated with SomaBrain
**Roadmap Expectation:** Sprint 1B - Connect Memory Gateway to actual SomaBrain  
**Current State:**
- ✅ Memory Gateway service exists (`services/memory-gateway/app/main.py`)
- ❌ **In-memory dict stub** (`MEMORY_STORE: dict[str, Any] = {}`)
- ❌ No vector database integration (Weaviate/Qdrant)
- ❌ No SomaBrain client library wired
- ❌ RAG endpoint echoes query as answer (dummy implementation)

**Impact:**
- Conversation memory persistence broken
- Multi-turn context not retained
- RAG retrieval non-functional
- Personalization features impossible

**Evidence:**
```python
# services/memory-gateway/app/main.py:35
@app.post("/v1/rag/retrieve", response_model=RAGResponse)
async def rag(request: RAGRequest):
    # Dummy implementation – echo the query as answer
    return RAGResponse(answer=f"Result for query: {request.query}", sources=[])
```

**Fix Required:**
1. Implement SomaBrain client SDK or vector DB adapter
2. Replace in-memory dict with persistent storage
3. Build semantic search with embeddings (use SLM service `/v1/embeddings`)
4. Add conversation history tracking per session
5. Wire `/v1/recall/{key}` to actual retrieval logic

**Priority:** 🔴 P0 - Core conversation feature broken

---

### 3. Gateway API Routing Incomplete
**Roadmap Expectation:** Sprint 1C - Authentication middleware + request routing  
**Current State:**
- ✅ Gateway API service exists (`services/gateway-api/app/main.py`)
- ❌ **Demo stub endpoints only** (returns hardcoded `"Hello from SomaGent Gateway!"`)
- ❌ No authentication middleware
- ❌ No routing to downstream services (Policy, Orchestrator, Identity)
- ❌ No OpenAI-compatible `/v1/chat/completions` implementation

**Impact:**
- Frontend/CLI can't interact with backend services
- No unified entry point for API consumers
- Security completely bypassed (no JWT validation)
- Admin console can't call live APIs

**Evidence:**
```python
# services/gateway-api/app/main.py:28
@app.post("/v1/chat/completions", tags=["gateway"])
def chat_completions(request: dict):
    return {"id": "chatcmpl-demo", "object": "chat.completion", 
            "choices": [{"message": {"role": "assistant", 
            "content": "Hello from SomaGent Gateway!"}}]}
```

**Fix Required:**
1. Add JWT authentication dependency (call Identity `/tokens/verify`)
2. Route `/v1/chat/completions` → Orchestrator `/v1/conversation/stream`
3. Route `/v1/models` → Settings Service model listing
4. Add policy header propagation (tenant, user_id, capabilities)
5. Implement error handling and rate limiting

**Priority:** 🔴 P0 - No API functionality without this

---

### 4. Integration Tests Missing
**Roadmap Expectation:** Sprint 1A - Integration test validating full stack  
**Current State:**
- ✅ Unit tests exist in 9 services (e.g., `test_identity_flows.py`, `test_policy_app.py`)
- ❌ **No end-to-end integration tests** validating cross-service flows
- ❌ Script `scripts/integration-tests.py` is placeholder
- ❌ No CI pipeline running automated tests

**Impact:**
- Can't validate services work together
- Deployment confidence near zero
- Regression risk extremely high
- Breaking changes undetected until manual testing

**Evidence:**
```bash
$ ls tests/
test_billing_service.py  test_benchmark_runner.py  test_somabrain_client.py
# No integration test suite covering session start → SLM → memory flow
```

**Fix Required:**
1. Create `tests/integration/test_conversation_flow.py`
2. Test: POST `/v1/chat/completions` → verify Kafka event → check SLM response
3. Test: Session creation with memory recall from previous turns
4. Test: Policy rejection triggering Gateway 403 response
5. Add to CI: `pytest tests/integration/ --cov=services`

**Priority:** 🔴 P0 - Can't ship without test coverage

---

### 5. Redis Persistence Not Configured
**Roadmap Expectation:** Sprint 1B - Jobs Service Redis integration  
**Current State:**
- ✅ Redis client imports in Policy Engine, Identity Service
- ✅ `get_redis_client()` helpers implemented
- ❌ **No Redis deployment in Helm chart** (missing from `values.yaml`)
- ❌ Jobs Service uses in-memory dict: `JOB_STORE: Dict[str, JobStatus] = {}`
- ❌ Policy Engine rule cache has 300s TTL but no Redis backend configured

**Impact:**
- Job state lost on service restart
- Policy rules not cached across instances (performance hit)
- Training mode locks ephemeral (data loss risk)
- Constitution hash cache non-functional

**Evidence:**
```python
# services/jobs/app/main.py:18
JOB_STORE: Dict[str, JobStatus] = {}  # FIXME: Replace with Redis
```

**Fix Required:**
1. Add Redis to Helm chart dependencies (Bitnami Redis subchart)
2. Configure Redis connection string in env vars
3. Wire Jobs Service to persist `JobStatus` to Redis keys
4. Validate Policy Engine rule cache hits Redis
5. Add health check pinging Redis

**Priority:** 🔴 P0 - Data loss guaranteed without this

---

### 6. Temporal Workflow Engine Not Deployed
**Roadmap Expectation:** Sprint 2B - Temporal integration for MAO  
**Current State:**
- ✅ Orchestrator mentions Temporal in comments
- ❌ **No Temporal server deployment** (not in Helm chart)
- ❌ No workflow definitions in codebase
- ❌ MAO endpoints return mocked responses

**Impact:**
- Multi-agent orchestration can't execute
- Task capsule execution not durable
- KAMACHIQ autonomous mode completely blocked
- No retry/compensation logic for failures

**Evidence:**
```python
# services/orchestrator/app/api/routes.py:156
@router.post("/mao/start", response_model=MultiAgentStartResponse, ...)
async def start_mao_workflow(request: MultiAgentStartRequest):
    # TODO: Start Temporal workflow for multi-agent orchestration
    return MultiAgentStartResponse(workflow_id=workflow_id, ...)
```

**Fix Required:**
1. Add Temporal Helm subchart to `k8s/helm/soma-agent/Chart.yaml`
2. Define workflows in `services/orchestrator/app/workflows/mao.py`
3. Implement activities for tool execution, approval gates
4. Wire `/mao/start` to `temporal.start_workflow()`
5. Add workflow status polling endpoint

**Priority:** 🔴 P1 - Blocks Sprint 2B/3A deliverables

---

### 7. Settings Service Incomplete
**Roadmap Expectation:** Sprint 1C - Tenant/profile management endpoints  
**Current State:**
- ✅ Settings service directory exists (`services/settings-service/`)
- ❌ **Minimal implementation** (basic health endpoints only)
- ❌ No `/v1/tenants` CRUD endpoints
- ❌ No persona profile management
- ❌ Model provider preferences not stored

**Impact:**
- Can't configure tenant-specific policies
- Persona switching non-functional
- Multi-tenant isolation broken
- Admin console can't manage settings

**Evidence:**
```bash
$ grep -r "@router" services/settings-service/app/
# Returns only health/metrics endpoints, no business logic
```

**Fix Required:**
1. Implement `/v1/tenants` GET/POST/PUT endpoints
2. Add `/v1/tenants/{id}/personas` for profile management
3. Store preferences in Postgres (add SQLAlchemy models)
4. Wire to Orchestrator for runtime persona selection
5. Add tests in `tests/test_settings_service.py`

**Priority:** 🔴 P1 - Multi-tenancy completely broken

---

### 8. CI/CD Pipeline Missing
**Roadmap Expectation:** Sprint 1A - Update CI pipeline with image building  
**Current State:**
- ❌ **No `.github/workflows/` directory** found
- ❌ No automated testing on PR
- ❌ No container image builds
- ❌ No deployment automation

**Impact:**
- Manual build/test/deploy required for every change
- Quality gates non-existent
- Deployment friction extremely high
- Team velocity severely limited

**Fix Required:**
1. Create `.github/workflows/ci.yml`
2. Add jobs: lint, test, build-images, push-to-registry
3. Configure secrets for GHCR authentication
4. Add deployment trigger for `main` branch
5. Require CI pass before merge

**Priority:** 🔴 P1 - Development velocity killer

---

## 🟡 HIGH PRIORITY GAPS

### 9. SLM Service Kafka Producer Not Wired
**Roadmap:** Sprint 1B - Wire real SLM request/response Kafka topics  
**Status:** aiokafka dependency exists, but no producer instantiation in code  
**Fix:** Implement async producer in `slm-service/app/producer.py`, publish to `slm.inference.requests` topic

### 10. Policy Engine Real Constitution Evaluation Missing
**Roadmap:** Sprint 1B - Implement constitution-based policy evaluation  
**Status:** Policy evaluation uses hardcoded rules, Constitution service not consulted  
**Fix:** Call Constitution service `/constitution/{tenant}` before policy eval, apply constraints

### 11. Task Capsule Marketplace Workflow Incomplete
**Roadmap:** Sprint 1B - Complete marketplace submission workflow  
**Status:** Submit endpoint exists, but review/approval gates stubbed  
**Fix:** Implement `/submissions/{id}/review` workflow with human-in-loop approvals

### 12. Conversation Streaming Not End-to-End
**Roadmap:** Sprint 2A - Real SSE streaming with conversation state  
**Status:** `/v1/conversation/stream` exists but doesn't call downstream services  
**Fix:** Wire to SLM Service + Memory Gateway, emit real tokens via SSE

### 13. Analytics Dashboard Metrics Stubbed
**Roadmap:** Sprint 1C - Basic dashboard and metrics collection  
**Status:** `/dashboards/agent-one-sight` returns placeholder data  
**Fix:** Query Postgres for real capsule run stats, aggregate metrics

### 14. Billing Service Usage Tracking Broken
**Roadmap:** Billing events should track token consumption  
**Status:** `/usage` endpoint returns empty list  
**Fix:** Consume Kafka billing events, write to ledger table

### 15. Notification Service Email Dispatch Not Implemented
**Roadmap:** Sprint 1C - Notification dispatch to users  
**Status:** Enqueue works, but no worker processing queue  
**Fix:** Add background worker consuming notification queue, send via SMTP/SNS

### 16. Tool Service Adapter System Missing
**Roadmap:** Sprint 2B - Adapter system for external integrations  
**Status:** Service skeleton only, no tool registry or execution  
**Fix:** Implement tool manifest schema, adapter framework, execution sandbox

### 17. Jobs Service Kafka Integration Missing
**Roadmap:** Sprint 1B - Redis + Kafka for async job tracking  
**Status:** In-memory job store only  
**Fix:** Publish job status changes to `jobs.status.updated` topic

### 18. Identity MFA Secret Storage Insecure
**Roadmap:** Sprint 1B - JWT token issuance and validation  
**Status:** MFA secrets stored in-memory dict  
**Fix:** Persist TOTP secrets to encrypted Postgres column

### 19. Orchestrator Session State Not Persistent
**Roadmap:** Sprint 2A - Conversation state management  
**Status:** `/sessions/start` creates workflow ID but doesn't store state  
**Fix:** Write session metadata to Redis with conversation history

### 20. Admin Console API Wiring Incomplete
**Roadmap:** Sprint 4 - Live API integration  
**Status:** React app scaffold exists, but hardcoded mock data  
**Fix:** Replace `useState` mocks with real `fetch()` calls to Gateway API

---

## 🟢 MEDIUM PRIORITY GAPS (DEFERRED FEATURES)

### 21. KAMACHIQ Project Planning Capsules
**Roadmap:** Sprint 3B - High-level roadmap decomposition  
**Status:** YAML definitions exist, but no execution engine  
**Defer to:** Post-MVP (requires Temporal workflows)

### 22. Workspace Provisioning Automation
**Roadmap:** Sprint 3B - Automated Git/VSCode/tool setup  
**Status:** Not started  
**Defer to:** Post-MVP (low user priority)

### 23. Quality Gates Automated Review
**Roadmap:** Sprint 3B - Automated review personas  
**Status:** Not started  
**Defer to:** Post-MVP (nice-to-have)

### 24. Persona Instance Just-in-Time Spawning
**Roadmap:** Sprint 3A - Dynamic agent provisioning  
**Status:** Not started  
**Defer to:** Post-MVP (requires Temporal + advanced orchestration)

### 25. Budget Token Limit Enforcement
**Roadmap:** Sprint 3A - Token limits per session  
**Status:** Not started  
**Defer to:** Post-MVP (can use manual monitoring short-term)

### 26. Parallel Task Execution Scheduler
**Roadmap:** Sprint 3A - Resource allocation for parallel tasks  
**Status:** Not started  
**Defer to:** Post-MVP (requires Temporal)

### 27. Dependency Graph Resolution
**Roadmap:** Sprint 3A - Task graph execution  
**Status:** Not started  
**Defer to:** Post-MVP (advanced MAO feature)

### 28. Disaster Recovery Drill Automation
**Roadmap:** Operations maturity feature  
**Status:** Analytics endpoints exist, but no drill runner  
**Defer to:** Post-GA (operational excellence phase)

### 29. Cross-Region Observability
**Roadmap:** Multi-region deployment monitoring  
**Status:** Not started  
**Defer to:** Post-GA (requires multi-region infra first)

---

## 📈 Implementation Maturity Matrix

| Service | Health Endpoint | Business Logic | Kafka Integration | Tests | Production Ready |
|---------|----------------|----------------|-------------------|-------|------------------|
| **Gateway API** | ✅ | ❌ (stubs) | N/A | ❌ | ❌ |
| **Orchestrator** | ✅ | 🟡 (partial) | ❌ (TODOs) | ✅ | ❌ |
| **Identity Service** | ✅ | ✅ | ✅ (audit) | ✅ | 🟡 |
| **Policy Engine** | ✅ | 🟡 (rules only) | ❌ | ✅ | 🟡 |
| **Constitution Service** | ✅ | ✅ | N/A | ✅ | ✅ |
| **SLM Service** | ✅ | 🟡 (sync only) | ❌ | ✅ | ❌ |
| **Memory Gateway** | ✅ | ❌ (in-mem) | N/A | ❌ | ❌ |
| **Jobs Service** | ✅ | 🟡 (in-mem) | ❌ | ✅ | ❌ |
| **Settings Service** | ✅ | ❌ (minimal) | N/A | ✅ | ❌ |
| **Analytics Service** | ✅ | 🟡 (mocks) | 🟡 (consumers) | ✅ | ❌ |
| **Billing Service** | ✅ | ❌ (stubs) | ❌ | ✅ | ❌ |
| **Task Capsule Repo** | ✅ | 🟡 (partial) | N/A | ❌ | ❌ |
| **Notification Service** | ✅ | 🟡 (queue only) | 🟡 (consumer) | ✅ | ❌ |
| **Token Estimator** | ✅ | 🟡 (heuristic) | N/A | ❌ | 🟡 |

**Legend:**
- ✅ Complete
- 🟡 Partial/In-Progress
- ❌ Missing/Stubbed
- N/A Not Applicable

**Production Ready Count:** 1/14 services (7%)

---

## 🎯 Recommended Remediation Plan

### Phase 1: Infrastructure Foundation (Week 1)
**Goal:** Deploy Kafka, Redis, enable service-to-service communication

1. **Enable Kafka in Helm** (2 days)
   - Set `kafka.enabled: true` in `values.yaml`
   - Deploy: `helm install soma k8s/helm/soma-agent -n soma-agent --create-namespace`
   - Validate: `kubectl exec -n soma-agent kafka-0 -- kafka-topics.sh --list`
   - Create topics: `conversation.events`, `slm.inference.requests`, `audit.identity`

2. **Add Redis to Helm Chart** (1 day)
   - Add Bitnami Redis dependency to `Chart.yaml`
   - Configure in `values.yaml` (single instance, no persistence for dev)
   - Wire connection strings to all services via ConfigMap

3. **Wire Kafka Producers** (2 days)
   - Orchestrator: Publish conversation events to `conversation.events`
   - Identity: Publish audit events to `audit.identity`
   - SLM: Publish inference requests to `slm.inference.requests`
   - Validate: `kafka-console-consumer.sh --topic conversation.events`

**Exit Criteria:** All services connect to Kafka/Redis, smoke test passes

---

### Phase 2: Core Service Completion (Week 2)
**Goal:** Gateway routing, Memory Gateway integration, Settings CRUD

4. **Implement Gateway API Routing** (3 days)
   - Add JWT middleware calling Identity `/tokens/verify`
   - Route `/v1/chat/completions` → Orchestrator `/v1/conversation/stream`
   - Add tenant/user header propagation
   - Test: `curl -H "Authorization: Bearer $TOKEN" http://gateway/v1/chat/completions`

5. **Memory Gateway SomaBrain Integration** (2 days)
   - Replace in-memory dict with Weaviate/Qdrant client
   - Implement semantic search using SLM embeddings
   - Wire `/v1/recall` to vector retrieval
   - Test: Store conversation turn, recall by semantic similarity

6. **Settings Service Tenant Management** (2 days)
   - Implement `/v1/tenants` CRUD with SQLAlchemy
   - Add `/v1/tenants/{id}/personas` profile endpoints
   - Store preferences in Postgres
   - Test: Create tenant, assign persona, retrieve from Orchestrator

**Exit Criteria:** End-to-end conversation flow works (Gateway → Orchestrator → SLM → Memory)

---

### Phase 3: Integration Testing & CI (Week 3)
**Goal:** Automated testing, CI pipeline, deployment confidence

7. **Create Integration Test Suite** (3 days)
   - Test: POST `/v1/chat/completions` → verify Kafka event → SLM response
   - Test: Multi-turn conversation with memory recall
   - Test: Policy rejection flow (Gateway 403)
   - Test: Training mode lock prevents normal inference
   - Run: `pytest tests/integration/ -v --cov`

8. **Build CI/CD Pipeline** (2 days)
   - Create `.github/workflows/ci.yml`
   - Jobs: lint (ruff), test (pytest), build (docker), push (GHCR)
   - Add deployment job for `main` branch
   - Require status checks before PR merge

**Exit Criteria:** CI green on `main`, integration tests passing, auto-deploy functional

---

### Phase 4: Production Readiness (Week 4)
**Goal:** Polish remaining services, security hardening

9. **Complete Remaining Service Implementations** (3 days)
   - Jobs Service: Persist to Redis
   - Analytics: Query real Postgres metrics
   - Billing: Consume Kafka events, write ledger
   - Notification: Add email dispatch worker

10. **Security & Observability** (2 days)
    - Add request tracing (OpenTelemetry)
    - Configure log aggregation (Loki/CloudWatch)
    - Harden secrets (move to K8s Secrets)
    - Run security scan (Trivy on images)

**Exit Criteria:** All P0/P1 gaps closed, production deployment ready

---

## 📊 Gap Closure Metrics

### Current vs. Target State

| Metric | Current | Target (Week 4) | Delta |
|--------|---------|-----------------|-------|
| **Services Production Ready** | 1/14 (7%) | 12/14 (86%) | +79% |
| **Integration Test Coverage** | 0% | 75% | +75% |
| **Kafka Integration** | 0/5 services | 5/5 services | +100% |
| **API Gateway Routing** | 0% | 100% | +100% |
| **Memory Persistence** | In-memory | Vector DB | Full |
| **CI/CD Automation** | None | Full | Full |
| **Helm Deployment Success** | Fails | Passes | Fixed |

---

## 🚨 Risk Assessment

### Top 3 Blockers to Production
1. **Kafka Infrastructure** - Without this, async patterns completely broken (affects 5 services)
2. **Gateway API Routing** - No way for clients to interact with backend
3. **Integration Tests** - Can't validate system works end-to-end

### Mitigation Strategy
- **Prioritize Phase 1 (Infrastructure)** - Unblocks all downstream work
- **Run weekly integration test** - Catch regressions early
- **Freeze feature work** - No new endpoints until P0 gaps closed

---

## 📝 Appendix: Recent Sprint Deliverables vs. Roadmap Alignment

### What Was Built (Parallel Sprints 2-4)
✅ Policy Engine Redis rule store  
✅ Identity Service JWT rotation  
✅ Orchestrator streaming endpoints (`/conversation/step`, `/stream`)  
✅ Training mode controller  
✅ Admin console React scaffold  
✅ Token estimator service  

### What Roadmap Expected (Sprint Wave 1)
❌ Kafka infrastructure deployment  
❌ Memory Gateway SomaBrain integration  
❌ Gateway API routing implementation  
❌ Integration test suite  
❌ CI/CD pipeline  
❌ Redis persistence for Jobs/Policy  

### Diagnosis
**Vertical slicing advanced Sprint 2-4 features without completing Sprint 1 foundation.** This created technical debt in infrastructure layer while expanding surface area. 

### Correction
**Return to canonical roadmap Sprint Wave 1 sequence.** Complete infrastructure before feature expansion.

---

**Generated by:** Gap Analysis Tool  
**Next Review:** Week 2 (post-Phase 2 completion)  
**Owner:** Engineering Lead  
**Approver:** Product/Architecture
