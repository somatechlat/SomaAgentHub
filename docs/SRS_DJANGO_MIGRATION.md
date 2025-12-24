# SomaAgentHub — Django/Ninja Migration SRS (ISO/IEC/IEEE 29148 Style)

**Document ID:** SAH-SRS-DJANGO-2025-12-22
**Version:** 0.1 (working draft)
**Date:** 2025-12-22
**Owner/Author:** Assistant (architecture + QA + security + performance + UX)

---

## 0. Executive Summary

This SRS defines the mandatory requirements to migrate all SomaAgentHub Python services to a **Django 5 + Django Ninja** control-plane while preserving existing business capabilities (Temporal, Kafka/Flink, Vault, OPA, Milvus, OTEL/Prom) and eliminating FastAPI/Qdrant usage. Migration is **in-place** (no feature drop, no rewrites without parity) and must enforce the VIBE Coding Rules (no placeholders, no invented APIs, full context).

**North-star:** A unified Django project exposing `/api/v2` (HTTP + Channels) that replaces all existing FastAPI surfaces, backed by Django ORM, centralized message catalog, and Lit UI clients.

---

## 1. Scope

### 1.1 Purpose
Provide testable, ISO-style requirements for the Django/Ninja migration of the SomaAgentHub stack, covering APIs, data models, security, observability, and operational guardrails.

### 1.2 In scope
- Gateway/API ingress, routing, authn/z, policy gates, moderation.
- Orchestrator control-plane (workflow/session/capsule APIs) + Temporal worker coordination.
- Identity, policy enforcement facades, audit/outbox, analytics events.
- Memory/vector proxy (Milvus only) and object-store artifact wiring.
- Tool/LLM/catalog CRUD with versioning and health.
- Settings/feature flags, RBAC/ABAC, tenancy.
- UI/console surfaces (Lit, fed from Django Channels/SSE).

### 1.3 Out of scope
- LLM model training or fine-tuning.
- Agent internal reasoning pipelines (SomaBrain execution internals).
- Non-Python services that are not APIs (Flink job binary, etc.), except where Django must expose control endpoints.

---

## 2. Drivers, Constraints, and Policies

- **Framework mandate:** Django 5 + Django Ninja for all new API surfaces; Lit 3.x for UI; Django ORM only. No FastAPI/Qdrant/SQLAlchemy for new work.
- **Existing code reality:** All HTTP APIs are currently FastAPI (gateway, orchestrator, identity-service, policy-engine, memory-gateway, tool-service, settings-service, notification-service, analytics-service, pricing-service, etc.). No Django project exists in the repo.
- **Message system:** All user-facing strings must route through a centralized message catalog (`admin.common.messages.get_message`) — currently absent; must be introduced.
- **Storage/infra:** Keep Temporal, Kafka, Flink, Vault, OPA; swap Qdrant → Milvus for vector storage. Continue MinIO/S3, Redis, Postgres, OTEL/Prom/Grafana, Loki/Tempo.
- **Security:** Fail-closed OPA checks, RBAC matrix adherence (`docs/technical-manual/security/rbac-matrix.md`), Vault for secrets, TLS everywhere, mTLS-ready services.
- **Performance:** Preserve existing endpoints’ latency envelopes; add Channels for realtime updates; keep Kafka-based eventing and outbox semantics.
- **Decoupling:** Modules must be deployable independently but fully usable by SomaAgentHub via the Django control-plane (supports MCP/worker integrations).

---

## 3. Baseline Implementation (current state)

- **Gateway (`services/gateway-api`)**: FastAPI `/v1` endpoints: `status`, `aggregate-status`, agents CRUD, crews, workflows register/execute/status/replay, HITL approve/reject, capsules run, dashboard health, health/metrics readiness. Relies on `services/common` models and `RequestContext`.
- **Orchestrator (`services/orchestrator/app/api`)**: FastAPI `/v1` routers (projects, planner, registry, conversation, training, memory, capsules, roles, tasks, tools, evaluations, HITL, RL, tenants, health). Uses contracts in `services/common/contracts`, outbox, Kafka, Temporal worker code present.
- **Identity-service (`services/identity-service/app`)**: FastAPI auth flows, JWT issuance/validation, storage, audit.
- **Policy-engine (`services/policy-engine/app`)**: FastAPI evaluator backed by OPA rego bundles.
- **Other FastAPI services**: memory-gateway, notification-service, tool-service, settings-service, analytics-service, pricing-service, llm-hub, model-proxy, etc.
- **Vector DB**: Qdrant Helm templates present (`k8s/helm/soma-agent/templates/qdrant*`); Milvus client exists (`services/common/milvus_client.py`) but not the default.
- **UI**: React templates and Alpine references exist; Lit components not yet implemented.
- **Django presence**: None detected in repo (`rg Django` → docs only).

---

## 4. Objectives and Non-Goals

### Objectives
1. Deliver a **single Django project** with modular apps (gateway, authz/authn, orchestration control-plane, memory proxy, tool/LLM catalog, settings/feature flags, audit/analytics, A2A collaboration, admin console) exposing `/api/v2`.
2. Achieve **contract parity** with all current `/v1` FastAPI endpoints, with side-effect gating via OPA and RBAC.
3. Migrate storage models to **Django ORM** with full migrations; remove SQLAlchemy usage from new surfaces.
4. Replace **Qdrant** references with **Milvus** in code, Helm, and configs; Kafka/Flink remain for streaming.
5. Introduce **message catalog** for all user-facing strings and enforce `admin.common.messages.get_message(...)` usage.
6. Provide **Lit UI** fed by Django Channels/SSE for realtime (workflows, HITL, A2A, analytics).

### Non-Goals
- Do not drop Temporal, Kafka, Vault, OPA, or Flink.
- Do not freeze worker processes; Temporal workers remain separate executables.
- Do not introduce new non-Django web frameworks.

---

## 5. Target Architecture (Django Control-Plane)

- **Django Project**: `/admin` (or similar) root with apps:
  - `gateway`: request ingress, context, routing, rate-limit, moderation.
  - `authn_authz`: JWT validation (delegating to identity), OPA/spicedb policy adapters, session middleware.
  - `orchestration`: workflow/session/capsule endpoints; Temporal client; outbox publishing to Kafka; HITL endpoints; planner and registry surfaces.
  - `memory`: Milvus proxy, Redis cache, object-store artifacts; embeddings routed via SomaBrain if present.
  - `catalog`: tool/LLM/model registry with versions, health, and GPU/Budget pricing hooks.
  - `settings_flags`: tenant/user settings and feature profiles.
  - `collaboration`: A2A threads/messages, WS/SSE streams.
  - `audit_analytics`: audit log, outbox events, ClickHouse/Flink hooks, metrics/OTEL exporters.
- **API Layer**: Django Ninja routers under `/api/v2`; Channels for WS/SSE.
- **Persistence**: Postgres via Django ORM; migrations via `manage.py makemigrations/migrate`.
- **Eventing**: Kafka publishers/subscribers (outbox and analytics).
- **Vector**: Milvus client as first-class; remove Qdrant templates; align Helm/compose.
- **Security**: OPA fail-closed middleware; Vault secrets; TLS/mTLS; RBAC matrix enforced per endpoint.

---

## 6. Data and Model Migration

- Recreate `services/common/models/*` in Django ORM (tenants, principals, roles, agents, workflows, tasks, tools, capsules, memory artifacts, HITL, RL, blueprints, outbox, audit).
- Ensure UUID PKs, JSONField where applicable, foreign keys with tenant scoping, audit fields (created_at, updated_at, created_by, tenant_id).
- Define migrations for all tables; add idempotent seed data for roles per RBAC matrix.
- Outbox pattern: transactional write with async publisher to Kafka; idempotence keys.

---

## 7. API Parity and Routing Requirements

### Gateway v1 → Django v2 (representative mapping)
- GET `/v1/status` → GET `/api/v2/status`
- GET `/v1/aggregate-status` → GET `/api/v2/status/aggregate`
- Agents: POST `/v1/agents`, GET/PUT `/v1/agents/{id}` → `/api/v2/agents/...`
- Crews: POST `/v1/crews` → `/api/v2/crews`
- Workflows: POST `/v1/workflows`, POST `/v1/workflows/{id}/execute`, GET `/v1/instances/{id}`, POST `/v1/instances/{id}/replay`
- HITL: POST `/v1/hitls/{session_id}/approve|reject`
- Capsules: POST `/v1/capsules/{capsule_id}/{version}/run`
- Dashboard/health/metrics/readiness endpoints require equivalents under `/api/v2` with Prom/OTEL integration.

### Orchestrator v1 → Django v2 (high level)
- Projects/registry/planner/conversation/training/memory/capsules/tasks/tools/evaluations/RL/roles/tenants/HITL endpoints require parity routes under Ninja, backed by the same business logic and Temporal hooks.

### Policy/Identity
- Identity issuance/validation endpoints re-exposed via Django auth app, delegating to existing keys/logic.
- Policy-engine evaluation endpoints re-exposed via Django, delegating to OPA client; fail-closed.

---

## 8. Security, Privacy, and Compliance

- Enforce RBAC matrix (`docs/technical-manual/security/rbac-matrix.md`) at every endpoint; map roles to permissions in Django.
- OPA checks precede side effects; SpiceDB (north-star) integration for relationship checks.
- Vault-backed secrets; no secrets in repo.
- TLS/mTLS between services; JWT validation via identity keys; audit every admin/privileged action.

---

## 9. Performance and Observability

- Maintain or improve existing latency; add cache where safe (Redis).
- OTEL tracing end-to-end; Prom metrics for every Django app; structured logs.
- Kafka/Flink/ClickHouse pipeline for analytics; health/liveness/readiness endpoints for all Django pods.

---

## 10. UI/UX

- Lit Web Components only; no Alpine/React for new work.
- Realtime via Channels (WS/SSE) for workflow status, HITL prompts, A2A threads, analytics dashboards.
- Apply SUIDS tokens (see `docs/SRS_SomaStack_UI.md`).

---

## 11. Migration Phases (high level)

1. **M0 – Inventory & Foundations:** Document all FastAPI endpoints and models; stand up Django project skeleton with Ninja + Channels; introduce message catalog scaffold.
2. **M1 – Gateway Parity:** Implement `/api/v2` equivalents for gateway routes; wire authn/OPA; health/metrics.
3. **M2 – Orchestrator Parity:** Port orchestrator control-plane endpoints; Temporal client bindings; outbox publishers; HITL flows.
4. **M3 – Identity/Policy:** Port identity-service and policy-engine facades into Django apps; ensure fail-closed; JWT issuance.
5. **M4 – Memory/Tools/LLM Catalog:** Milvus proxy endpoints, tool registry, model/LLM catalog CRUD with health and pricing hooks.
6. **M5 – UI/Realtime:** Lit console + Channels streams; analytics dashboards.
7. **M6 – Decommission FastAPI:** Cut over routing; retire `/v1` once parity + soak confirmed.

Each phase must include tests, metrics, security review, and VIBE compliance check.

---

## 12. Risks and Open Issues

- No existing Django project or message catalog; must be created without breaking current pipelines.
- Large surface area of FastAPI services; parity will require systematic contract mapping and test coverage.
- Qdrant still present in Helm templates; removal must be coordinated with infra changes (Milvus endpoints, data migration).
- gpubroker/voyant repos not present in workspace; integration requirements cannot be validated yet.
- Identity/policy/analytics services contain FastAPI-specific middleware; porting must preserve auth flows and audit logging.

---

## 13. Acceptance Criteria

- Django/Ninja `/api/v2` provides parity endpoints for all `/v1` gateway/orchestrator/identity/policy routes with passing integration tests.
- Django ORM models and migrations exist for all core domains; outbox/audit operational.
- Milvus is the only vector backend referenced in code and deployments; Qdrant removed.
- Lit UI screens consume Channels/SSE for realtime updates.
- Security posture matches RBAC matrix, OPA fail-closed behavior, Vault secrets, TLS.
- FastAPI endpoints can be decommissioned after soak with zero critical regressions.
