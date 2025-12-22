# SomaAgentHub — Software Requirements Specification (ISO/IEC/IEEE 29148 Style)

**Document ID:** SAH-SRS-2025-12-22
**Version:** 1.1 (working draft; A2A conversations added)
**Date:** 2025-12-22
**Baseline:** Repo snapshot `SomaAgentHub-main(5).zip` (current code reality)
**Owner/Author:** Agent Zero (SomaTech LAT)
**Prepared by:** Assistant (architecture + QA + security + ops + ISO-style spec)

---

## 0. Executive summary

### 0.1 What SomaAgentHub is (product definition)

SomaAgentHub is the **multi-tenant orchestration hub** for fleets of agents. It is the *control plane* and *runtime plane* that provides:

* **Gateway API** (north-south ingress; request context; routing; moderation gates)
* **Orchestration** (workflows, long-running tasks, retries, compensation; Temporal)
* **Identity** (JWT issuance/validation; optional OIDC federation)
* **Policy** (OPA checks; fail-closed; decision cache)
* **Memory** (vector + KV + retrieval endpoints; object-store artifacts)
* **Tool/Capability registry** (tool CRUD; health; audit; invocation contracts)
* **Settings/Feature flags** (tenant/user schema-validated configuration)
* **Audit & analytics** (immutable audit log + event stream → OLAP)
* **Inter-agent collaboration (A2A)** (expert conversations; coordination; replay)
* **UI/Console** (admin + operator view for workflows, tenants, tools, flags)
* **Infra** (Kubernetes/Helm; Docker Compose dev; observability; secrets)

### 0.2 Current state (what is DONE vs BROKEN)

**DONE / solid foundations present in the snapshot**

* Core service skeletons exist and **compile**: `gateway-api`, `orchestrator`, `identity-service`, `policy-engine`.
* Shared platform libraries exist in `services/common`: **env resolver**, OPA client, Vault client, Redis client, MinIO client, Kafka client, audit logger, OTEL/Prom observability helpers, outbox model/repository.
* Multi-tenant model families exist under `services/common/models/` (identity, role, task, tool, capsule, blueprint, RL, etc.).
* `docker-compose.yml`, Helm chart structure, scripts (env centralization, sbom, vuln scan, deploy, backup/restore) exist.
* Orchestrator contains an **A2A protocol module** (`core/a2a_protocol.py`) providing foundational structures (agent cards/registry).

**BROKEN / misleading / needs immediate stabilization**

* Multiple non-core services contain **syntax/indentation or invalid-character errors** (example categories): `memory-gateway`, `analytics-service`, `tool-service`, `billing-service`, `notification-service`, `constitution-service`, `mao-engine`, `airflow-service` dags/plugins, and more.
* **Docs drift**: several docs claim “✅ complete / full coverage / full compliance” that is not consistent with the actual code health; references to files that are missing (e.g., canonical roadmap) and modules that don’t exist.
* **Runtime drift**: Temporal is present, but worker/container wiring is inconsistent (a “worker” container exists in compose but is not a Temporal worker for the orchestrator workflows).
* **Config drift**: the repo contains a canonical env prefix rule (`SOMA_AGENT_HUB_…`) but local scripts/Makefile and older docs still use inconsistent names.
* **Hidden dependency gaps**: some workflow code assumes Ray settings that are not defined in config and not wired in Compose.

### 0.3 Decisions (to make this SaaS-grade and stop the chaos)

This SRS adopts the following **non-negotiable platform decisions**:

1. **Tiering:** We define a **Tier-0 Core** set of services that must compile, test, and ship. Everything else is **Tier-1 (supported later)** or **Labs/Incubation (not shipped)**.
2. **Truthfulness gate:** Docs must not claim ✅ if CI does not pass. “Green check” is allowed only when a pipeline verifies it.
3. **Temporal is canonical:** Workflow orchestration is Temporal. All long tasks must have workflow IDs, status endpoints, cancel/retry, and compensation trail.
4. **Config canonicalization:** Only `SOMA_AGENT_HUB_` prefix is valid for runtime configuration. Non-canonical env vars are treated as legacy aliases only through a single migration layer.
5. **SaaS invariants:** multi-tenancy, RBAC/ABAC, auditability, idempotency, SLOs, and operational runbooks are required.
6. **Agent-to-agent collaboration is first-class:** inter-agent conversations are durable, auditable, tenant-isolated, and workflow-linked.
7. **Airflow is required for batch/background jobs** (ETL, backfills, scheduled maintenance) and is **not** used for runtime orchestration.

### 0.4 Immediate roadmap (high level)

* **Phase 0 (Stabilize):** fix syntax errors; isolate labs; ensure compose brings up Tier-0; CI gates.
* **Phase 1 (SaaS Core):** tenant/user auth, OPA fail-closed gates, outbox for every publish, workflow worker correctness, audit log correctness, **A2A threads/messages**.
* **Phase 2 (Security/AuthZ):** SpiceDB integration + relationship writers; Vault policy hardening; rate limits.
* **Phase 3 (Memory/Analytics):** Milvus migration (north-star) + Kafka→Flink→ClickHouse pipeline; operator UI dashboards.
* **Phase 4 (UI + API v2):** consolidate console; introduce Django Ninja + Channels (north-star) while keeping FastAPI v1 until parity.

### 0.5 Goal and quick take-aways

**Goal:** Turn SomaAgentHub from a prototype into a production-grade, multi-tenant Hub + Autonomous Agent Orchestrator that can schedule, monitor, and self-heal fleets of agents while exposing a clean, versioned API surface.

**Quick take-aways**

* Consolidate API governance under Django Ninja + Channels for versioning and real-time.
* Make Temporal the single source of truth for workflow state and compensation.
* Introduce SpiceDB + OPA for fine-grained, fail-closed authorization.
* Migrate vector store to Milvus and route memory calls through a SomaBrain proxy.
* Deploy a robust A2A engine (Postgres + Kafka) bound to workflows.
* Enforce outbox + audit everywhere for durability and traceability.

---

## 1. Scope

### 1.1 Purpose

Define **complete, testable** functional and non-functional requirements for SomaAgentHub to operate as a **production SaaS orchestration platform**.

### 1.2 Product scope

This SRS covers:

* API Gateway (ingress + authn + policy gates + routing)
* Orchestration (Temporal workflows + worker)
* Identity (JWT/OIDC)
* Policy Engine (OPA)
* Authorization (SpiceDB north-star)
* Memory layer (vector + KV + retrieval + artifacts)
* Tool/Capability registry
* Settings & feature flags
* Audit logging & analytics
* Inter-agent collaboration (A2A) and expert conversations
* UI/Console
* Deployment (K8s/Helm, Compose dev)

### 1.3 Out of scope

* Agent internal reasoning (belongs to SomaAgent01/SomaBrain)
* LLM model training
* AgentIQ governance framework (explicitly removed)

---

## 2. References

* Repo docs (architecture/security/deployment/user manual where accurate)
* `docs/CENTRALIZATION_SUMMARY.md` (env prefix rule)
* `SRS_GAP_ANALYSIS.md` (model inventory confirmation)
* `docs/SRS_SomaStack_UI.md` (SomaStack Unified UI Design System, ISO/IEC/IEEE 29148:2018)
* VIBE Coding Rules (no fake implementations; verify before change)

---

## 3. Terms and definitions

* **Tenant:** isolated customer namespace.
* **Principal:** authenticated user/service identity.
* **Workflow:** Temporal workflow execution.
* **Outbox:** durable event staging table for publish-after-commit.
* **OPA:** policy engine for contextual allow/deny.
* **SpiceDB:** relationship-based authorization system.
* **Milvus:** vector DB (north-star).
* **A2A:** agent-to-agent collaboration and conversation protocol.
* **SUIDS:** SomaStack Unified UI Design System (design tokens + components + UI behaviors).

---

## 4. Stakeholders and users

* **Platform Admin (SomaTech LAT):** operates clusters, policies, billing, upgrades.
* **Tenant Admin:** manages tenant config, roles, tools, budgets.
* **Developer:** integrates agents/tools via APIs.
* **Security/Compliance:** audits permissions, policies, logs, retention.
* **Operator (SRE/On-call):** monitors SLOs, incident response.

---

## 5. System context and overview

### 5.1 Context diagram (conceptual)

```mermaid
flowchart LR
  U[Users / Agents / Integrations] --> GW[Gateway API]
  GW --> ID[Identity Service]
  GW --> PE[Policy Engine (OPA)]
  GW --> ORC[Orchestrator API]
  ORC -->|Temporal gRPC| TEM[Temporal Cluster]
  TEM --> WK[Temporal Workers]
  ORC --> PG[(Postgres)]
  ORC --> KAF[Kafka]
  ORC --> OBJ[(S3/MinIO)]
  GW --> MEM[Memory Gateway]
  MEM --> VDB[(Vector DB: Qdrant now / Milvus target)]
  MEM --> REDIS[(Redis KV/cache)]
  ORC --> COLLAB[Collaboration (A2A Threads/Messages)]
  COLLAB --> PG
  COLLAB --> KAF
  KAF --> FLK[Flink Jobs]
  FLK --> CH[(ClickHouse)]
  ALL[All Services] --> OBS[OTEL + Prometheus + Grafana]
  ALL --> VAULT[Vault]
  ALL --> AUTHZ[SpiceDB]
  ALL --> KC[Keycloak OIDC]
```

### 5.2 Tier-0 Core (the only things we ship first)

**Tier-0 services MUST compile, have tests, and be runnable in Compose + K8s:**

* `gateway-api`
* `orchestrator` + **Temporal worker** (same codebase, separate process)
* `identity-service`
* `policy-engine`
* `collaboration` (A2A threads/messages; may start embedded but Tier-0 behavior)
* `object store` integration (MinIO/S3) for artifacts/digests

Everything else is Tier-1 or Labs until stabilized.

---

## 6. Current implementation assessment (baseline snapshot)

### 6.1 Build/compile health (objective)

**Compiles:** `gateway-api`, `orchestrator`, `identity-service`, `policy-engine`
**Does not compile (examples):** `memory-gateway`, `analytics-service`, `tool-service`, `billing-service`, `notification-service`, `constitution-service`, `mao-engine`, and others.

### 6.2 Configuration drift

* Canonical rule: only `SOMA_AGENT_HUB_*` env vars are valid.
* Drift: Makefile/local scripts still use non-canonical names.

**Requirement outcome:** introduce a single **legacy alias layer** (documented), then eliminate legacy names.

### 6.3 Workflow drift (Temporal)

* Temporal code exists in orchestrator workflows.
* Compose “worker” container is **not** a Temporal worker for those workflows.

**Requirement outcome:** define an explicit `orchestrator-worker` process/image that polls the configured task queue, and ensure Compose/K8s deploy it.

### 6.4 Documentation drift

* Some docs/traceability claim full compliance and tests that are not verifiable from the snapshot.

**Requirement outcome:** docs must be generated/validated by CI; no unverifiable claims.

---

## 7. Target architecture (SaaS-grade)

### 7.1 North-star stack (as requested)

* **API v2:** Django 5 + Django Ninja
* **Realtime:** Django Channels (WS) + SSE
* **UI:** Lit Web Components
* **UI Design System:** SUIDS (see `docs/SRS_SomaStack_UI.md`)
* **Vector:** Milvus (primary)
* **AuthZ:** SpiceDB (relationships)
* **Secrets:** Vault
* **Events/Analytics:** Kafka → Flink → ClickHouse
* **Observability:** Prometheus + OTEL
* **Batch/ETL:** Airflow (required for background jobs)

### 7.2 Pragmatic delivery plan (keep shipping while migrating)

We will run **two API generations** during migration:

* **/api/v1 (current):** FastAPI microservices (Tier-0)
* **/api/v2 (target):** Django Ninja control-plane + Channels for console realtime

**Rule:** /v2 must reuse the same auth, policy, audit, A2A, and tenancy invariants; it is not allowed to bypass Tier-0 gates.

### 7.3 Service boundary refactor (canonical)

* **Gateway API**: ingress, request context, authn, rate limit, moderation, routing.
* **Identity**: JWT/OIDC, keys, token rotation.
* **Policy**: OPA evaluate endpoint, bundles, local cache.
* **Orchestrator API**: workflow submission/status, task graph APIs, tool invocation coordination.
* **Orchestrator Worker**: Temporal worker(s) executing activities/workflows.
* **Collaboration (A2A)**: conversation threads/messages, participants, streaming and replay, workflow binding.
* **Memory**: vector + retrieval.
* **Analytics**: event ingest and query APIs.
* **Console**: UI + admin APIs.

### 7.4 Inter-agent collaboration and expert conversations (A2A)

SomaAgentHub MUST support **structured conversations between expert agents** (e.g., researcher ↔ mathematician ↔ operator) as a first-class platform capability.

#### 7.4.1 Goals

* Enable agents to **coordinate** during workflows (ask/answer, share intermediate results, negotiate plans).
* Persist conversations as **auditable artifacts** tied to workflow/session IDs.
* Provide realtime streaming to the UI (operator console) with replay.

#### 7.4.2 Architectural pattern

* **Conversation Broker (logical component):** implemented as either:

  1. a dedicated `collaboration-service` (recommended), or
  2. a module inside `orchestrator` + `gateway-api` during Phase 1.

* **Transport:**

  * **Kafka** topics for durable inter-agent messaging and replay (canonical).
  * **WS/SSE** fanout for UI updates (console subscriptions).

* **Persistence:** Postgres as the source-of-truth (threads/messages/participants), plus optional ClickHouse for analytics.
* **Identity/Authorization:**

  * Agent instances and users authenticate via JWT.
  * **SpiceDB** enforces who may read/write to a thread.
  * **OPA** enforces contextual rules (budget, safety modes, rate limits).

#### 7.4.3 Message model (minimum)

Each message MUST include:

* `tenant_id`
* `thread_id`
* `sender_type` (agent|user|system)
* `sender_id` (agent_instance_id or user_id)
* `recipient_scope` (thread|direct|role)
* `workflow_id` (optional but recommended)
* `session_id` (optional)
* `message_kind` (question|answer|plan|critique|artifact_ref|status|tool_result)
* `content` (text/structured JSON)
* `artifact_refs[]` (object-store URIs + hashes)
* `created_at`, `correlation_id`, `causation_id`

#### 7.4.4 Workflow integration

* Workflows MUST be able to:

  * create/join a thread
  * post messages (including tool results)
  * subscribe to messages (blocking wait with timeout)
  * produce final “conversation digest” artifact linked to the workflow outcome

#### 7.4.5 Alignment with existing code

The repo already contains an **A2A protocol module** (e.g., `services/orchestrator/app/core/a2a_protocol.py`) with structures such as `AgentCard` and registries. This SRS standardizes that capability into a SaaS-grade, auditable, tenant-isolated conversation system.

### 7.5 Integration contracts: SomaAgent01 and SomaBrain

SomaAgentHub is the **orchestration hub**. SomaAgent01 is the **agent runtime** that executes tasks, invokes tools, and participates in collaboration. SomaBrain is the **memory and context resource** that provides persistent memory and cognition services.

#### 7.5.1 Responsibilities split (do not duplicate)

* **SomaAgent01 (runtime):**
  * Turn execution loop, tool invocation, persona container loading, local workspace, human-in-the-loop UI interaction.
  * Agent-level coordination primitives and internal "agent chat" semantics.
  * Connects to SomaAgentHub as a client (authn, A2A, workflows, tools).
* **SomaAgentHub (platform):**
  * Multi-tenant ingress, authn/authz enforcement, policy gates, workflow orchestration (Temporal), audit/eventing, collaboration transport + storage.
  * Durable system-of-record for workflows, A2A threads, audits, and platform settings.
* **SomaBrain (resource):**
  * Memory tiers, retrieval, embeddings/HDC, scoring/planning modules, provenance and retention.
  * Hub and Agent call SomaBrain through a controlled gateway (direct or via Memory Gateway).

#### 7.5.2 Agent instance identity (required for SaaS correctness)

Every running SomaAgent01 instance MUST have:

* `agent_instance_id` (stable for its lifecycle)
* `tenant_id`
* `principal_id` (service identity)
* `capabilities[]` (declared)

Hub MUST be able to:

* register/update agent_instance presence (heartbeat)
* authorize what the agent may do (SpiceDB + OPA)

#### 7.5.3 Where A2A "lives"

A2A exists at **two layers** and both are required:

1. **Agent-level A2A semantics (SomaAgent01):** how an agent formats a question/answer/plan/tool_result and decides who to talk to.
2. **Platform-level A2A transport + persistence (SomaAgentHub):** how those messages are authenticated, authorized, stored, replayed, and streamed to operators.

#### 7.5.4 Compatibility rule

Hub MUST NOT invent a different A2A schema than the agent unless versioned.

* Put the canonical message envelope + thread model into a shared contract package (`services/common/a2a_contracts` or `sdk/contracts`).
* SomaAgent01 and SomaAgentHub MUST both use that contract to avoid drift.

#### 7.5.5 Execution strategies supported by Hub

Hub MAY deliver A2A messages via multiple backends:

* **Temporal child workflow invocation** (current repo mechanism via `services/orchestrator/app/integrations/a2a_adapter.py`)
* **Kafka topic fanout** (durable pub/sub + replay)
* **Direct WS relay** (operator UI only; not a system-of-record)

The system-of-record remains **Postgres thread/message log**.

### 7.6 Core architectural pillars (normative)

These pillars are required characteristics of the platform. Each pillar is mapped to corresponding requirement sections.

| Pillar | What it solves | Key mechanisms | Requirements |
| --- | --- | --- | --- |
| Unified API Surface | Consistent ingress, versioning, backward compatibility | FastAPI v1 + Django Ninja v2, Channels (WS/SSE), OpenAPI contracts | FR-GW-001..005, FR-UI-003..005, NFR-ENG-004 |
| Temporal-based orchestration | Durable workflows, compensation, auditability | Temporal workers, Saga/compensation, Outbox pattern | FR-ORC-001..005, NFR-REL-001 |
| Autonomous agent lifecycle | Registration, health, scaling, graceful shutdown | Agent registry, heartbeat, HPA hooks, versioned contracts | FR-AGT-001..006, NFR-OBS-001 |
| Pluggable tool & capability registry | Tool versioning and safe invocation | CRUD APIs, semantic versioning, OPA gating, audit/outbox | FR-TOOL-001..004 |
| A2A collaboration engine | Durable expert conversations bound to workflows | Postgres thread/message log, Kafka fan-out, WS/SSE, digest artifacts | FR-A2A-001..006, FR-AUD-001 |
| Vector memory & retrieval | Scalable semantic memory and RAG | Milvus primary, Redis cache, SomaBrain proxy | FR-MEM-001..004, Section 14 |
| Policy & authorization | Centralized fine-grained access control | SpiceDB + OPA, decision cache, fail-closed | FR-AUTHZ-001, FR-POL-001..003 |
| Observability & analytics | End-to-end visibility and business insights | Prometheus, OTEL, Kafka→Flink→ClickHouse | NFR-OBS-001..002, FR-ANA-001..002 |
| Secure secrets & config | Zero-trust config and drift control | Vault, canonical env prefix, CI validation | FR-SET-002, NFR-ENG-004 |
| CI/CD & quality gates | Prevent drift and enforce VIBE | Pre-commit, lint/typecheck, integration + chaos tests | NFR-ENG-001..004, Section 11 |

---

## 8. Functional requirements

> Format: **FR-XXXX** (MUST/SHOULD/MAY) + Acceptance Criteria (AC)

### 8.1 Gateway API

* **FR-GW-001 (MUST):** Expose REST endpoints for session orchestration, tool execution, memory operations, settings/flags, audit browsing (privileged), collaboration (A2A), and health/metrics.

  * **AC:** OpenAPI published; endpoints require auth; `/health` and `/ready` exist; `/metrics` exists.

* **FR-GW-002 (MUST):** Enforce authentication for all non-public endpoints.

  * **AC:** Requests without valid JWT are rejected with 401; service-to-service tokens allowed.

* **FR-GW-003 (MUST):** Perform OPA policy check **before any side effect**.

  * **AC:** If OPA is unavailable, gateway returns 503 and no mutation occurs (fail-closed).

* **FR-GW-004 (MUST):** Tenant routing and isolation.

  * **AC:** Tenant context derived from token + headers; tenant mismatch rejects.

* **FR-GW-005 (SHOULD):** Backpressure and rate limiting.

  * **AC:** Per-tenant and per-principal limits; 429 with retry-after.

### 8.2 Orchestration & Temporal

* **FR-ORC-001 (MUST):** Provide workflow submission API.

  * **AC:** Create workflow returns `workflow_id`; status endpoint returns state.

* **FR-ORC-002 (MUST):** Provide workflow lifecycle operations.

  * **AC:** Cancel, retry, and compensation endpoints exist; all actions are audited.

* **FR-ORC-003 (MUST):** Temporal worker deployment.

  * **AC:** Worker polls configured task queue; Compose and Helm deploy it; liveness/ready checks.

* **FR-ORC-004 (MUST):** Saga + compensation support for multi-step operations.

  * **AC:** Each workflow step has a compensator; compensation results recorded.

* **FR-ORC-005 (MUST):** Outbox pattern for event publish.

  * **AC:** Events are staged in Postgres within transaction; publisher flushes; idempotent.

### 8.3 Identity & Authentication

* **FR-ID-001 (MUST):** JWT issuance and validation.

  * **AC:** token issuance and validation flow; rotation support.

* **FR-ID-002 (SHOULD):** OIDC federation option.

  * **AC:** Well-known endpoints and JWKS; optional Keycloak integration.

### 8.4 Policy (OPA)

* **FR-POL-001 (MUST):** Central OPA evaluation endpoint.

  * **AC:** `/v1/evaluate` returns allow/deny + reason.

* **FR-POL-002 (MUST):** Fail-closed enforcement.

  * **AC:** If policy-engine unreachable, caller denies.

* **FR-POL-003 (SHOULD):** Decision caching.

  * **AC:** Redis cache TTL ≤ 60s; cache key includes tenant + principal + action + resource.

### 8.5 Authorization (SpiceDB north-star)

* **FR-AUTHZ-001 (MUST in v2; SHOULD in v1):** Relationship-based authorization for all privileged operations.

  * **AC:** Writes require relationship check; audit records include check result.

### 8.6 Memory

* **FR-MEM-001 (MUST):** Provide remember/recall/list/search endpoints.

  * **AC:** Insert memory with tenant_id; search returns tenant-isolated results.

* **FR-MEM-002 (MUST):** RAG retrieval endpoint.

  * **AC:** Returns context with token estimates; policy gates applied.

* **FR-MEM-003 (SHOULD):** Vector DB abstraction.

  * **AC:** Pluggable client supports Qdrant now; Milvus target.

* **FR-MEM-004 (MUST):** Memory API calls SHALL be routed through a SomaBrain client or proxy.

  * **AC:** Calls to `/memory/remember` and `/memory/recall` invoke SomaBrain with tenant headers and are audited.

### 8.7 Tool & capability registry

* **FR-TOOL-001 (MUST):** CRUD tools/models/capabilities with versioning.

  * **AC:** Each tool has immutable ID + version; updates create new version.

* **FR-TOOL-002 (MUST):** Invocation auditing.

  * **AC:** Every invocation emits audit event and outbox record.

* **FR-TOOL-003 (SHOULD):** Health probes per provider.

  * **AC:** Health endpoint with latency percentiles; circuit-breaker when failing.

* **FR-TOOL-004 (MUST):** Tool invocation MUST be policy-gated and outbox-audited.

  * **AC:** OPA/SpiceDB checks occur before invocation; invocation produces an outbox event and audit record.

### 8.8 Settings & feature flags

* **FR-SET-001 (MUST):** Schema-validated settings per tenant/user.

  * **AC:** JSON schema validation; optimistic locking.

* **FR-SET-002 (MUST):** Secrets stored in Vault.

  * **AC:** No secrets in Postgres; only references.

* **FR-SET-003 (SHOULD):** Emit `settings.changed` events.

  * **AC:** Event contains old/new hash, actor, timestamp.

### 8.9 Audit & analytics

* **FR-AUD-001 (MUST):** Immutable audit log for all state mutations.

  * **AC:** Contains tenant, principal, action, resource, decision, correlation IDs.

* **FR-ANA-001 (SHOULD):** Kafka event stream for operational + business events.

  * **AC:** Topic naming convention; schema registry or JSON schema.

* **FR-ANA-002 (MAY):** Flink transforms to ClickHouse.

  * **AC:** Materialized views for p95 latency, errors, per-tenant usage.

### 8.10 UI/Console

* **FR-UI-001 (SHOULD):** Admin console with tenants/users/tools/workflows/audit.

  * **AC:** Role-based views; realtime updates via WS/SSE.

* **FR-UI-002 (MUST for public SaaS):** WCAG 2.1 AA.

  * **AC:** Accessibility audit passes.

* **FR-UI-003 (MUST):** UI SHALL conform to the SomaStack Unified UI Design System (SUIDS).

  * **AC:** Conformance is demonstrated against `docs/SRS_SomaStack_UI.md` requirements (tokens, components, roles, accessibility, performance).

* **FR-UI-004 (MUST):** UI implementation SHALL use Lit Web Components while preserving SUIDS behavior and visual standards.

  * **AC:** Lit components implement SUIDS-required components and tokens; any technology-level deviations from SUIDS are documented in Appendix F.

* **FR-UI-005 (SHOULD):** UI SHALL provide the baseline SUIDS screens (layout, dashboard, data management, settings) plus SomaAgentHub-specific screens (agents, workflows, A2A, policies, audit).

  * **AC:** Screen inventory is documented and mapped to SUIDS component requirements.

### 8.11 Inter-agent collaboration and conversations (A2A)

* **FR-A2A-001 (MUST):** Create, list, and manage conversation threads.

  * **AC:** Thread APIs support create/join/leave; include tenant scoping; link to workflow/session.

* **FR-A2A-002 (MUST):** Send messages between agents/users within a thread.

  * **AC:** Message write requires authn + SpiceDB check; OPA evaluated before side effects; returns message_id and monotonic sequence.

* **FR-A2A-003 (MUST):** Realtime stream of thread updates.

  * **AC:** WS/SSE delivers new messages with backoff; supports resume via cursor/sequence.

* **FR-A2A-004 (MUST):** Durable replay and export.

  * **AC:** Thread can be replayed from Postgres log; export JSON/CSV; integrity includes hashes for artifacts.

* **FR-A2A-005 (MUST):** Conversation-to-workflow binding.

  * **AC:** Workflow can create a thread, post messages, and generate a final digest artifact stored in object-store.

* **FR-A2A-006 (SHOULD):** Agent-to-agent “direct” messaging.

  * **AC:** Supports direct recipient (agent_instance_id) with TTL and rate limits; still logged/audited.

### 8.12 Airflow (Batch Workloads)

* **FR-AIR-001 (MUST):** Use Airflow only for batch/ETL and background jobs (not runtime orchestration).

### 8.13 Autonomous agent lifecycle

* **FR-AGT-001 (MUST):** Provide an Agent Registry for self-service agent registration and discovery.

  * **AC:** Agents can register with `agent_instance_id`, `tenant_id`, `principal_id`, and `capabilities[]`; registry supports list/search by tenant and capability.

* **FR-AGT-002 (MUST):** Heartbeat and liveness reporting.

  * **AC:** Agents post heartbeats on a defined interval; registry marks stale agents as unhealthy and exposes status to UI and orchestrator.

* **FR-AGT-003 (SHOULD):** Autoscaling hooks for agent pools.

  * **AC:** Orchestrator exposes scaling signals (queue depth, workflow backlog) consumable by K8s HPA or an autoscaler controller.

* **FR-AGT-004 (MUST):** Versioned agent contracts.

  * **AC:** Agent API/SDK contracts are versioned and validated; incompatible versions are rejected or routed through a compatibility shim.

* **FR-AGT-005 (MUST):** Graceful shutdown and quarantine.

  * **AC:** Agents can be drained, quarantined, or decommissioned; state transitions are audited.

* **FR-AGT-006 (SHOULD):** Self-heal policy for unhealthy agents.

  * **AC:** System triggers restart/redeploy policies when liveness fails, with retry limits and audit.

---

## 9. Data requirements

### 9.1 Postgres

* MUST store tenants, principals, workflow metadata, outbox events, tool registry versions, settings metadata, collaboration threads/messages.
* MUST support migrations (Alembic now; Django migrations for v2 control-plane).

### 9.2 Vector store

* **Now:** Qdrant client exists in common libs.
* **Target:** Milvus collections for `memory`, `capsule_runs`, `artifacts_index`.

### 9.3 Object store

* MinIO/S3 used for artifacts, capsule outputs, large payloads, and **conversation digests**.
* Upload pipeline MUST include metadata-first, hash-dedup, malware scan (ClamAV) before availability.

### 9.4 Eventing

* Kafka topics: `somaagent.<domain>.<event>` (canonical convention).
* Outbox ensures publish-after-commit.

### 9.5 Conversation and collaboration storage (A2A)

* **Postgres (source-of-truth):**

  * `conversation_threads` (tenant_id, thread_id, title, workflow_id, session_id, created_by, created_at, status)
  * `conversation_participants` (thread_id, participant_type, participant_id, role, joined_at)
  * `conversation_messages` (thread_id, seq, sender_type, sender_id, kind, content_json, artifact_refs_json, correlation_id, created_at)
  * `conversation_digests` (thread_id, workflow_id, digest_artifact_uri, digest_hash, created_at)

* **Kafka (optional but recommended):** `somaagent.collab.message` for event-driven fanout and analytics.
* **ClickHouse (optional):** materialized views for message volume, latency, per-tenant usage.

---

## 10. Non-functional requirements

### 10.1 Performance

* **NFR-PERF-001 (MUST):** p95 simple API latency < 50ms (excluding upstream calls).
* **NFR-PERF-002 (SHOULD):** WS fanout ≥ 10k connections per node (console events).
* **NFR-PERF-003 (SHOULD):** A2A message end-to-end latency p95 < 250ms within a region (broker → consumer).
* **NFR-UI-001 (MUST):** UI performance SHALL meet SUIDS targets (FCP < 1.5s, TTI < 3s, CLS < 0.1, theme switch < 100ms).
* **NFR-UI-002 (SHOULD):** UI bundle budgets SHALL align to SUIDS (CSS and JS size targets); any deviation must be recorded in Appendix F.

### 10.2 Reliability

* **NFR-REL-001 (MUST):** 99.5% availability for Tier-0 APIs.
* **NFR-REL-002 (MUST):** graceful degradation when non-critical deps fail (analytics, optional providers).

### 10.3 Security

* **NFR-SEC-001 (MUST):** TLS everywhere; secure headers; CSP for console.
* **NFR-SEC-002 (MUST):** rate limits; abuse detection.
* **NFR-SEC-003 (MUST):** PII/secret detection on ingest paths; block or redact per policy.
* **NFR-SEC-004 (MUST):** A2A thread/message access is tenant-isolated and authorization-checked (SpiceDB + OPA).

### 10.4 Observability
!!!

* **NFR-OBS-001 (MUST):** Prometheus metrics in every Tier-0 service.
* **NFR-OBS-002 (MUST):** OTEL traces across service boundaries; correlation IDs.

### 10.5 Operability

* **NFR-OPS-001 (MUST):** Runbooks for backup/restore, incident response, upgrades.
* **NFR-OPS-002 (MUST):** Health/readiness semantics standardized.

### 10.6 Engineering integrity (anti-drift)

* **NFR-ENG-001 (MUST):** CI blocks merge if any Tier-0 service does not compile.
* **NFR-ENG-002 (MUST):** Docs truthfulness: any ✅ claim must be backed by CI artifact.
* **NFR-ENG-003 (MUST):** Pre-commit hooks block non-printable characters, mixed tabs/spaces, and invalid unicode hyphens in code files.
* **NFR-ENG-004 (MUST):** CI SHALL include lint, typecheck, unit, integration, security scan, contract tests, and chaos tests for fail-closed behavior.

### 10.7 Scalability and high-throughput operations

* **NFR-SCALE-001 (MUST):** Gateway tier SHALL be stateless and horizontally scalable.

  * **AC:** All session state stored in shared services (Redis/Postgres); gateway can scale without data loss.

* **NFR-SCALE-002 (MUST):** Event-driven backbone for state-changing operations.

  * **AC:** State mutations publish via Outbox to Kafka; consumers are decoupled from producers.

* **NFR-SCALE-003 (SHOULD):** Durable storage SHALL support partitioning by tenant and time.

  * **AC:** Core high-volume tables are partitioned by `tenant_id` and date; hot-spotting is mitigated.

* **NFR-SCALE-004 (MUST):** Temporal worker pools SHALL be horizontally scalable.

  * **AC:** Worker deployments scale based on task queue lag and queue depth metrics.

* **NFR-SCALE-005 (SHOULD):** Caching tier SHALL reduce hot-read load.

  * **AC:** Redis caches sessions/auth, OPA decisions, hot vector results, and recent A2A messages.

* **NFR-SCALE-006 (MUST):** Observability SHALL detect saturation before failure.

  * **AC:** Metrics for RPS, p95 latency, queue lag, and DB pool usage are tracked with alerts.

* **NFR-SCALE-007 (SHOULD):** Infrastructure automation SHALL support safe scale-out and rollback.

  * **AC:** Helm values expose replica counts and autoscaling policies; GitOps deploys are repeatable.

---

## 11. Verification and validation plan

### 11.1 Test strategy

* Unit tests (pure functions, models, validators)
* Integration tests (service-to-service with Compose)
* Contract tests (OpenAPI + event schemas)
* E2E tests (console + gateway critical flows)
* Chaos tests (dependency outages; fail-closed verification)
* **A2A tests:**

  * thread create/join/leave
  * message write/read with SpiceDB + OPA enforcement
  * WS/SSE stream resume from cursor
  * workflow-bound thread creation and final digest artifact generation

### 11.2 Release gates

A release is allowed only if:

1. Tier-0 compiles and unit tests pass
2. Compose smoke test passes (gateway→identity→policy→orchestrator→temporal)
3. Policy fail-closed test passes
4. Audit trail test passes (mutation emits audit)
5. A2A smoke test passes (thread + message + replay)

---

## 12. Deployment and operations

### 12.1 Environments

* Dev: Docker Compose profiles
* Staging/Prod: Kubernetes + Helm, per-tenant config

### 12.2 Secrets

* Vault is the only secret store in prod.
* No plaintext secrets in env files in prod.

### 12.3 Backups and DR

* Postgres: PITR snapshots
* Object store: versioned buckets + replication option
* Vector DB: periodic snapshots
* ClickHouse: table backups

---

## 13. Refactor + migration roadmap (with exit criteria)

### Phase 0 — Stabilization

**Milestones**

* Fix syntax/indentation errors in all Tier-0 services.
* Isolate lab services (`services/labs/*`) from CI and packaging.
* Align Docker Compose/Helm ports to the 20xxx confirmatory scheme.
* Add pre-commit hooks and CI compile gate.
* Replace Compose "worker" with `orchestrator-worker` running the Temporal worker.

**Success criteria**

* `docker compose up` brings up gateway-api, orchestrator, identity-service, policy-engine, temporal worker.
* A sample workflow completes successfully.

### Phase 1 — Core SaaS foundations

**Milestones**

* Implement SpiceDB + OPA integration in gateway and orchestrator.
* Enforce Outbox for every publish (Kafka and audit).
* Add audit logger to all state-mutating endpoints.
* Deploy A2A MVP (thread table, message API, WS stream).

**Success criteria**

* Tier-0 functional tests pass.
* Policy fail-closed test succeeds.
* A2A smoke tests (create thread, send message, replay) pass.

### Phase 2 — Autonomous agent lifecycle

**Milestones**

* Build Agent Registry (Postgres + Redis cache) with heartbeat endpoints.
* Introduce `agent_instance_id` and `tenant_id` propagation in all calls.
* Autoscale agent pools via K8s HPA signals.
* Versioned Agent contracts in shared SDK/contracts.

**Success criteria**

* Agents can register, send heartbeats, and be discovered by orchestrator.
* Scaling reacts to load without duplicate registrations.

### Phase 3 — Vector memory & SomaBrain

**Milestones**

* Deploy Milvus cluster; enable dual-write from Qdrant during migration.
* Implement SomaBrain proxy (memory-gateway thin wrapper) with authz + audit.
* Add RAG retrieval endpoint with OPA gating.
* Migrate existing vectors with checksum verification.

**Success criteria**

* Recall latency < 200ms (p95) under target load.
* Audit entries exist for every `/memory/*` call.
* Dual-write rollback window validated.

### Phase 4 — Tool & capability marketplace

**Milestones**

* Refactor tool-service for semantic versioning and health probes.
* Add tool-invocation outbox events.
* Implement tool-registry UI (Lit) with role-based visibility.

**Success criteria**

* New tool versions can be added without downtime.
* Every invocation is logged and observable.

### Phase 5 — Analytics & UI v2

**Milestones**

* Bring up Kafka → Flink → ClickHouse pipeline with materialized views.
* Deploy Django Ninja `/api/v2` with contract parity to `/api/v1`.
* Switch console to Lit components conforming to SUIDS with WS live updates.

**Success criteria**

* Dashboards show real-time metrics.
* `/api/v2` passes contract tests.
* UI meets WCAG AA and SUIDS performance budgets.

### Phase 6 — Full SaaS release

**Milestones**

* Decommission legacy FastAPI `/api/v1` after sunset window.
* Enable feature-flag driven rollout of autonomous agent scaling.
* Blue/green deployment with traffic split.

**Success criteria**

* SLA ≥ 99.5% sustained during rollout.
* No regression in functional tests.
* All docs reflect true ✅ status (CI-verified).

---

## 14. SomaBrain integration (canonical cognitive resource)

### 14.1 Purpose

SomaAgentHub (SAH) SHALL integrate with **SomaBrain (SB)** as a first-class **cognitive memory + context resource**, using the same HTTP contract already used by SomaAgent01 (SA01). SAH MUST NOT re-implement agent memory semantics (embedding, recall, scoring, tiered memory) inside SAH services; SAH delegates those semantics to SB and enforces SaaS-grade governance around its use.

This section clarifies the architectural boundary:

* **SA01 (agent runtime)** owns semantics (how/when to ask, how to reason, how to converse).
* **SAH (platform)** owns SaaS correctness (tenant isolation, authn/authz, audit, replay, orchestration).
* **SB (cognitive resource)** owns memory + context building + adaptation.

### 14.2 SomaBrain runtime facts (current contract)

* SB is a FastAPI service (default bind `:9696`).
* SB enforces Bearer auth and expects `X-Tenant-ID` for tenancy.
* Canonical endpoints consumed by upstream agents:
  * `GET /health`
  * `POST /memory/remember`
  * `POST /memory/recall`
  * `POST /plan/suggest`
  * `POST /context/evaluate`
  * `POST /context/feedback`

### 14.3 Where SomaBrain integrates into SomaAgentHub

#### 14.3.1 Data-plane: Memory and context for sessions

1. **Gateway/API**
   * SAH Gateway (FastAPI /v1, Django Ninja /v2) SHALL expose memory and context surfaces for UI and operators.
   * Implementation SHALL call SB to perform remember/recall and context evaluate/feedback.
2. **Orchestrator (Temporal workflows)**
   * Workflows SHALL call SB for recall context, to remember salient outputs, and to request plan suggestions when configured.
3. **Memory Gateway service**
   * SAH Memory Gateway SHALL become a thin proxy/adapter over SB.
   * The proxy exists for backward compatibility and policy/audit enforcement at the SAH boundary.
   * SB remains the canonical semantic memory implementation.

#### 14.3.2 Control-plane: Governance + audit for SB usage

Every call from SAH to SB MUST be governed by:

1. **AuthN**: caller identity (service token or user token)
2. **AuthZ**: SpiceDB relationship checks (resource-level) and OPA contextual policy checks (budget/safety)
3. **Audit**: record the fact of the SB call (who/tenant/intent/latency/outcome) without duplicating SB internal logs

### 14.4 Integration contract (SAH -> SB)

#### 14.4.1 Required headers

* `Authorization: Bearer <token>`
* `X-Tenant-ID: <tenant_id>`
* Optional: `X-Request-ID`, `X-Session-ID` for trace correlation

#### 14.4.2 Required configuration (SAH)

* `SOMA_BRAIN_BASE_URL` (example: `http://somabrain:9696`)
* `SOMA_BRAIN_TOKEN` (service token OR pass-through user JWT)
* `SOMA_BRAIN_TIMEOUT_S` (default 10s)
* `SOMA_BRAIN_HEALTH_TTL_S` (default 5s)

#### 14.4.3 Client library requirement

SAH SHALL implement a strict SB client in `services/common` that provides:

* Health-aware gating (`GET /health` cached with TTL)
* Explicit failure semantics (no silent empty returns)
* Timeouts, circuit breaker, and bounded retries

### 14.5 Required refactors in SomaAgentHub (to use SomaBrain)

#### 14.5.1 Replace Qdrant/OpenAI embedding memory paths

* `services/common/memory_gateway.py` currently uses Redis + Qdrant + embeddings.
* This SHALL be replaced with an SB-backed implementation:
  * short-term memory may remain Redis (optional)
  * long-term recall/remember delegates to SB
  * embedding generation is NOT performed inside SAH

#### 14.5.2 Update orchestrator workflows that call Memory Gateway

* `services/orchestrator/app/workflows/*` SHALL call SB directly or via the SAH proxy that delegates to SB.
* Workflows MUST pass tenant identity and request/session IDs to ensure correct isolation and replay.

#### 14.5.3 Remove semantic duplication in SAH Memory Gateway

* Any SAH code that implements a full semantic memory system SHALL be removed or converted into SB delegation after parity is validated.

### 14.6 Multi-agent conversation requirement (A2A + Memory)

SAH SHALL support expert-to-expert conversations as a workflow capability:

* **Conversation storage (system-of-record):** SAH Postgres stores A2A thread messages/events with replay.
* **Semantic recall:** salient messages, summaries, and decisions are mirrored into SB via `/memory/remember`.
* **Context build:** each agent turn MAY call SB `/memory/recall` (and optionally `/context/evaluate`) to enrich the message with relevant memories.

### 14.7 Failure modes and degradation policy

If SB is unavailable:

* SAH MUST NOT silently degrade to "no memory".
* SAH returns an explicit degraded-mode flag in API responses.
* Workflows either fail fast (policy-dependent) or continue with memory-disabled mode with explicit audit and operator visibility.
* Health gating uses SB `/health` and a circuit breaker.

### 14.8 Acceptance criteria

SAH can run a workflow that:

1. stores a memory into SB (`/memory/remember`)
2. recalls it (`/memory/recall`)
3. records an audit event for both calls
4. enforces SpiceDB + OPA before the calls
5. replays the workflow deterministically without losing traceability

### 14.9 Migration note (current SAH -> SB-backed memory)

* Phase 1: Add SB client + config; proxy existing SAH Memory Gateway endpoints to SB.
* Phase 2: Refactor orchestrator workflows to call SB-backed adapter only.
* Phase 3: Remove SAH semantic memory code paths (Qdrant/embeddings) once parity is validated.

---

## 15. Traceability (minimum viable)

### 15.1 Requirement → service mapping (starter)

| Requirement                       | Services                                    | Evidence (to be CI artifacts)         |
| --------------------------------- | ------------------------------------------- | ------------------------------------- |
| FR-GW-003 OPA before side effects | gateway-api, policy-engine                  | integration test `policy_fail_closed` |
| FR-ORC-003 Worker deployment      | orchestrator, orchestrator-worker, Temporal | compose smoke workflow test           |
| FR-AUD-001 Audit trail            | orchestrator, common/audit_logger           | audit mutation test                   |
| FR-A2A-002 A2A message send       | collaboration/orchestrator, gateway-api     | integration test `a2a_send_enforced`  |
| FR-A2A-004 Replay                 | collaboration/orchestrator, postgres        | integration test `a2a_replay_cursor`  |

---

## Appendix A — Canonical service catalog

### A.1 Tier-0 (ship)

* gateway-api
* orchestrator (API)
* orchestrator-worker (Temporal worker; deployment target)
* identity-service
* policy-engine
* collaboration (A2A threads/messages; may start embedded, but must behave as Tier-0)
* redis, postgres, temporal

### A.2 Tier-1 (after stabilization)

* memory-gateway
* tool-service
* settings-service
* notification-service
* billing-service
* analytics-service
* airflow-service (batch/ETL only)

### A.3 Labs (do not ship until rewritten)

* mao-engine (until compiling + tested)
* marketplace (until cleaned)
* evolution-engine (until cleaned)

---

## Appendix B — Known baseline defects (examples, actionable)

1. Many services contain indentation / non-printable characters that break import.
2. Docs claim full coverage/compliance without verifiable CI.
3. Compose worker is not the orchestrator Temporal worker.
4. Ray usage in session workflow is not wired/configured.
5. Env vars inconsistent across Makefile, docs, and services.

---

## Appendix C — Configuration standard (canonical)

* All runtime env vars MUST be prefixed with `SOMA_AGENT_HUB_`.
* Legacy aliases are allowed only behind a single compatibility module and must be removed by Phase 1 exit.

---

## Appendix D — “What we know about the code” (validated module memory)

* `services/common`: env resolver, OPA/Vault/Kafka/MinIO clients, OTEL/Prom, audit logger, outbox model.
* `services/gateway-api`: request context middleware, moderation guard, region routing, forwarding.
* `services/orchestrator`: FastAPI APIs + Temporal workflows + saga/circuit-breaker patterns, outbox publisher startup, persona handling.
* `services/identity-service`: Redis-backed identity store, key rotation, ClickHouse audit logger.
* `services/policy-engine`: OPA evaluate endpoint + local evaluation helpers.
* **A2A foundation exists:** orchestrator contains an A2A protocol module with agent card/registry structures; must be productized into tenant-isolated, auditable conversation threads.

---

## Appendix E — A2A collaboration protocol (minimum standard)

### E.1 Thread lifecycle

* A thread is created by a principal or workflow.
* Participants join via explicit invite or role-based membership.
* Thread status: `active | archived | locked`.

### E.2 Message ordering and idempotency

* Messages are assigned a **monotonic `seq`** per thread.
* Clients may retry `POST message` with an idempotency key; server must deduplicate.

### E.3 Security requirements

* Read/write checks use SpiceDB.
* Contextual allow/deny uses OPA.
* All messages are audit-logged; sensitive fields redacted per policy.

### E.4 Workflow binding and digest

* Workflows must attach `workflow_id` and `session_id` to the thread.
* On workflow completion, the system generates:

  * a **conversation digest** (summary + citations to messages/artifacts)
  * stored in object store with hash
  * referenced from `conversation_digests`

---

## Appendix F — UI Design System conformance (SUIDS)

SomaAgentHub UI requirements SHALL conform to `docs/SRS_SomaStack_UI.md`. The table below summarizes the minimum conformance scope and the approved deviation(s) specific to SomaAgentHub.

### F.1 Conformance scope (minimum)

| SUIDS Area | Required in SomaAgentHub | Notes |
| --- | --- | --- |
| Design tokens (colors, spacing, typography) | Yes | Tokens must be available as CSS custom properties and applied across components. |
| Role-based UI (Admin/Operator/Viewer) | Yes | Roles are enforced via JWT claims and UI visibility rules. |
| Core components (navigation, tables, cards, modals, toasts) | Yes | Implemented as Lit components with the same behaviors. |
| Accessibility (WCAG 2.1 AA) | Yes | Required for public SaaS. |
| UI performance budgets (FCP/TTI/CLS, theme switch) | Yes | Targets defined in SUIDS remain binding. |
| Settings, status indicators, dashboards | Yes | Must align with SUIDS definitions. |

### F.2 Deviation register (SomaAgentHub only)

| ID | SUIDS Constraint | SomaAgentHub Decision | Rationale | Status |
| --- | --- | --- | --- | --- |
| DEV-UI-001 | Alpine.js + no build step | Lit Web Components + build pipeline allowed | Platform standard requires Lit for UI; behavior and tokens remain identical to SUIDS | Approved |

---

---

## Appendix G — SomaStack Unified UI Design System (Full Text)

This appendix embeds the approved SUIDS specification for completeness. Source of truth remains the SUIDS document version noted in its header.
**Completeness note:** The current SUIDS source file includes a placeholder line indicating missing sections; the remaining text must be supplied to make this appendix fully complete.

# Software Requirements Specification

## SomaStack Unified UI Design System

---

## Document Control

| Field | Value |
|-------|-------|
| **Document ID** | SRS-SOMASTACK-UI-2025-001 |
| **Version** | 1.0.0 |
| **Classification** | Internal |
| **Status** | APPROVED |
| **Effective Date** | 2025-12-22 |
| **Review Date** | 2026-06-22 |
| **Owner** | SomaStack Platform Team |
| **Standard** | ISO/IEC/IEEE 29148:2018 |

### Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 0.1.0 | 2025-12-22 | Kiro AI | Initial draft |
| 1.0.0 | 2025-12-22 | Kiro AI | Approved for implementation |

### Approval Signatures

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | _________________ | _________________ | ________ |
| Technical Lead | _________________ | _________________ | ________ |
| QA Lead | _________________ | _________________ | ________ |
| Security Officer | _________________ | _________________ | ________ |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [Specific Requirements](#3-specific-requirements)
4. [System Features](#4-system-features)
5. [External Interface Requirements](#5-external-interface-requirements)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [Security Requirements](#7-security-requirements)
8. [Data Requirements](#8-data-requirements)
9. [Constraints](#9-constraints)
10. [Assumptions and Dependencies](#10-assumptions-and-dependencies)
11. [Acceptance Criteria](#11-acceptance-criteria)
12. [Traceability Matrix](#12-traceability-matrix)
13. [Appendices](#13-appendices)

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) document provides a complete and comprehensive description of the requirements for the **SomaStack Unified UI Design System**. This document serves as the authoritative source for all functional, non-functional, and interface requirements governing the design, development, testing, and deployment of the unified user interface framework across the SomaStack platform.

The intended audience for this document includes:
- Software Architects and Developers
- UI/UX Designers
- Quality Assurance Engineers
- Project Managers
- Security Auditors
- Operations Teams
- External Auditors and Compliance Officers

### 1.2 Scope

#### 1.2.1 System Name
**SomaStack Unified UI Design System** (SUIDS)

#### 1.2.2 System Overview
The SomaStack Unified UI Design System is a comprehensive, standardized visual language and component library that provides consistent theming, role-based access controls, real-time status indicators, and a modern glassmorphism aesthetic across all SomaStack platform applications.

#### 1.2.3 In-Scope Applications
| Application | Description | Port |
|-------------|-------------|------|
| SomaAgent01 | AI Agent Orchestration Platform | 21016 |
| SomaBrain | Cognitive Memory Runtime | 9696 |
| SomaFractalMemory | Fractal Memory Storage System | 9595 |
| AgentVoiceBox | Voice Interface System | 25000 |

#### 1.2.4 Out of Scope
- Backend API implementations (covered by separate SRS documents)
- Database schema design (covered by separate DDS documents)
- Infrastructure provisioning (covered by IaC specifications)
- Mobile native applications
- Third-party integrations not listed in Section 10

### 1.3 Definitions, Acronyms, and Abbreviations

#### 1.3.1 Definitions

| Term | Definition |
|------|------------|
| Design Token | A named entity that stores a visual design attribute (color, spacing, typography) as a CSS custom property |
| Glassmorphism | A design style featuring frosted glass effects with subtle transparency, blur, and layered surfaces |
| Component | A reusable, self-contained UI element with defined behavior and styling |
| Store | An Alpine.js reactive state container shared across components |
| Theme | A collection of design tokens that define the visual appearance of the application |
| Role | A named set of permissions that determines UI element visibility and functionality |
| Tenant | An isolated organizational unit within the multi-tenant SomaStack platform |

#### 1.3.2 Acronyms

| Acronym | Expansion |
|---------|-----------|
| SUIDS | SomaStack Unified UI Design System |
| CSS | Cascading Style Sheets |
| JWT | JSON Web Token |
| WCAG | Web Content Accessibility Guidelines |
| ARIA | Accessible Rich Internet Applications |
| API | Application Programming Interface |
| SRS | Software Requirements Specification |
| UI | User Interface |
| UX | User Experience |
| SSE | Server-Sent Events |
| WebSocket | Full-duplex communication protocol |
| OPA | Open Policy Agent |
| RBAC | Role-Based Access Control |

#### 1.3.3 Abbreviations

| Abbreviation | Meaning |
|--------------|---------|
| req. | requirement |
| sec. | section |
| fig. | figure |
| tbl. | table |
| ms | milliseconds |
| px | pixels |
| rem | root em (CSS unit) |

### 1.4 References

| ID | Document | Version | Date |
|----|----------|---------|------|
| REF-001 | ISO/IEC/IEEE 29148:2018 - Systems and software engineering — Life cycle processes — Requirements engineering | 2018 | 2018-11 |
| REF-002 | WCAG 2.1 - Web Content Accessibility Guidelines | 2.1 | 2018-06 |
| REF-003 | Alpine.js Documentation | 3.x | 2024 |
| REF-004 | SomaAgent01 Product Requirements Document | 1.0 | 2025-12 |
| REF-005 | SomaBrain Technical Manual | 1.0 | 2025-12 |
| REF-006 | SomaFractalMemory API Specification | 1.0 | 2025-12 |
| REF-007 | AgentVoiceBox Architecture Document | 1.0 | 2025-12 |
| REF-008 | VIBE Coding Rules | 1.0 | 2025-12 |
| REF-009 | Material Design 3 Guidelines | 3.0 | 2024 |
| REF-010 | Geist Font License | 1.0 | 2024 |

### 1.5 Document Overview

This SRS is organized according to ISO/IEC/IEEE 29148:2018 structure:

- **Section 1** provides introduction, scope, and definitions
- **Section 2** describes the overall system context and constraints
- **Section 3** specifies detailed functional requirements
- **Section 4** describes system features and use cases
- **Section 5** defines external interface requirements
- **Section 6** specifies non-functional requirements (performance, reliability, etc.)
- **Section 7** details security requirements
- **Section 8** describes data requirements
- **Section 9** lists constraints and limitations
- **Section 10** documents assumptions and dependencies
- **Section 11** defines acceptance criteria
- **Section 12** provides requirements traceability matrix
- **Section 13** contains appendices with supplementary information

---

## 2. Overall Description

### 2.1 Product Perspective

#### 2.1.1 System Context

The SomaStack Unified UI Design System operates as a shared foundation layer across all SomaStack platform applications. It provides the visual language, component library, and state management infrastructure that ensures consistency and maintainability across the platform.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SOMASTACK PLATFORM                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ SomaAgent01 │  │  SomaBrain  │  │ SomaFractal │  │AgentVoiceBox│           │
│  │   WebUI     │  │   WebUI     │  │   Memory    │  │   WebUI     │           │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘           │
│         │                │                │                │                   │
│         └────────────────┴────────────────┴────────────────┘                   │
│                                   │                                             │
│                                   ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                 SOMASTACK UNIFIED UI DESIGN SYSTEM                      │   │
│  ├─────────────────────────────────────────────────────────────────────────┤   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│  │  │   Design    │  │  Component  │  │    State    │  │ Integration │    │   │
│  │  │   Tokens    │  │   Library   │  │   Stores    │  │    Layer    │    │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                   │                                             │
│                                   ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        BACKEND SERVICES                                  │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │   │
│  │  │   JWT   │  │  Health │  │Settings │  │   OPA   │  │  WebSocket│      │   │
│  │  │  Auth   │  │  APIs   │  │  APIs   │  │ Policies│  │   APIs   │       │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### 2.1.2 System Interfaces

| Interface | Type | Description |
|-----------|------|-------------|
| SI-001 | REST API | Health check endpoints for status monitoring |
| SI-002 | REST API | Settings persistence endpoints |
| SI-003 | JWT | Authentication token parsing |
| SI-004 | WebSocket | Real-time updates for voice interface |
| SI-005 | SSE | Server-sent events for status updates |
| SI-006 | localStorage | Client-side preference persistence |

#### 2.1.3 Hardware Interfaces

The system has no direct hardware interfaces. All hardware interaction occurs through the browser's standard APIs.

#### 2.1.4 Software Interfaces

| Interface | Software | Version | Purpose |
|-----------|----------|---------|---------|
| SWI-001 | Alpine.js | 3.x | Reactive component framework |
| SWI-002 | Modern Browsers | ES2020+ | Runtime environment |
| SWI-003 | CSS Custom Properties | Level 1 | Design token implementation |
| SWI-004 | Web Audio API | Standard | Voice waveform visualization |
| SWI-005 | Intersection Observer | Standard | Lazy loading |
| SWI-006 | ResizeObserver | Standard | Responsive behavior |

#### 2.1.5 Communication Interfaces

| Interface | Protocol | Port | Purpose |
|-----------|----------|------|---------|
| CI-001 | HTTPS | 443 | Secure API communication |
| CI-002 | WSS | 443 | Secure WebSocket communication |
| CI-003 | HTTP | 80 | Development only (redirects to HTTPS) |

### 2.2 Product Functions

The SomaStack Unified UI Design System provides the following major functions:

| ID | Function | Description |
|----|----------|-------------|
| PF-001 | Design Token Management | Centralized CSS custom properties for visual consistency |
| PF-002 | Theme Switching | Light/dark/system theme support with persistence |
| PF-003 | Role-Based UI Control | Dynamic UI element visibility based on user roles |
| PF-004 | Component Library | Reusable UI components with consistent styling |
| PF-005 | State Management | Alpine.js stores for shared application state |
| PF-006 | Status Monitoring | Real-time service health visualization |
| PF-007 | Accessibility Support | WCAG 2.1 AA compliant interface |
| PF-008 | Responsive Layout | Adaptive layouts for all screen sizes |
| PF-009 | Form Handling | Validated form inputs with feedback |
| PF-010 | Notification System | Toast notifications and alerts |

### 2.3 User Classes and Characteristics

#### 2.3.1 User Class: Administrator

| Attribute | Description |
|-----------|-------------|
| **Role ID** | UC-ADMIN |
| **Description** | System administrators with full platform access |
| **Technical Expertise** | High |
| **Frequency of Use** | Daily |
| **Primary Tasks** | System configuration, user management, monitoring, troubleshooting |
| **UI Permissions** | Full access to all UI elements and controls |

#### 2.3.2 User Class: Operator

| Attribute | Description |
|-----------|-------------|
| **Role ID** | UC-OPERATOR |
| **Description** | Day-to-day operators managing agent workflows |
| **Technical Expertise** | Medium |
| **Frequency of Use** | Daily |
| **Primary Tasks** | Agent management, conversation monitoring, task execution |
| **UI Permissions** | View, create, edit, execute operations |

#### 2.3.3 User Class: Viewer

| Attribute | Description |
|-----------|-------------|
| **Role ID** | UC-VIEWER |
| **Description** | Read-only users for monitoring and reporting |
| **Technical Expertise** | Low to Medium |
| **Frequency of Use** | Occasional |
| **Primary Tasks** | Dashboard viewing, report generation, status monitoring |
| **UI Permissions** | View-only access |

### 2.4 Operating Environment

#### 2.4.1 Supported Browsers

| Browser | Minimum Version | Support Level |
|---------|-----------------|---------------|
| Google Chrome | 90+ | Full |
| Mozilla Firefox | 88+ | Full |
| Microsoft Edge | 90+ | Full |
| Safari | 14+ | Full |
| Safari iOS | 14+ | Full |
| Chrome Android | 90+ | Full |

#### 2.4.2 Screen Resolutions

| Category | Width Range | Layout |
|----------|-------------|--------|
| Mobile | < 640px | Single column, bottom navigation |
| Tablet | 640px - 1023px | Two column, collapsed sidebar |
| Desktop | 1024px - 1439px | Multi-column, full sidebar |
| Wide | ≥ 1440px | Multi-column, expanded layout |

#### 2.4.3 Network Requirements

| Requirement | Specification |
|-------------|---------------|
| Minimum Bandwidth | 1 Mbps |
| Recommended Bandwidth | 10 Mbps |
| Latency Tolerance | < 200ms for interactive operations |
| Offline Support | Limited (cached assets only) |

### 2.5 Design and Implementation Constraints

#### 2.5.1 Technical Constraints

| ID | Constraint | Rationale |
|----|------------|-----------|
| TC-001 | No build step required | Simplify deployment and reduce toolchain complexity |
| TC-002 | Vanilla JavaScript only | Avoid framework lock-in and reduce bundle size |
| TC-003 | Alpine.js 3.x for reactivity | Lightweight, declarative, HTML-first approach |
| TC-004 | CSS Custom Properties for theming | Native browser support, no preprocessing required |
| TC-005 | Maximum 100KB CSS (minified) | Performance budget for initial load |
| TC-006 | Maximum 50KB JS (minified) | Performance budget for initial load |

#### 2.5.2 Regulatory Constraints

| ID | Constraint | Standard |
|----|------------|----------|
| RC-001 | WCAG 2.1 AA compliance | Accessibility |
| RC-002 | GDPR compliance for user preferences | Data protection |
| RC-003 | No third-party tracking | Privacy |

#### 2.5.3 Development Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-001 | VIBE Coding Rules compliance | REF-008 |
| DC-002 | No mocks or placeholders | VIBE Rule #1 |
| DC-003 | Real implementations only | VIBE Rule #4 |
| DC-004 | Complete context required | VIBE Rule #6 |

### 2.6 Assumptions and Dependencies

See Section 10 for detailed assumptions and dependencies.

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 Design Token System

##### FR-DT-001: Token Definition
| Attribute | Value |
|-----------|-------|
| **ID** | FR-DT-001 |
| **Title** | CSS Custom Property Token Definition |
| **Priority** | P0 - Critical |
| **Description** | THE Design_System SHALL define all visual attributes as CSS custom properties in a single `somastack-tokens.css` file. |
| **Rationale** | Centralized tokens enable consistent theming and easy maintenance. |
| **Source** | Requirement 1.1 |
| **Verification** | Inspection of CSS file; automated token validation test |

##### FR-DT-002: Token Propagation
| Attribute | Value |
|-----------|-------|
| **ID** | FR-DT-002 |
| **Title** | Token Value Propagation |
| **Priority** | P0 - Critical |
| **Description** | WHEN a token value changes at `:root` level THEN the Design_System SHALL propagate the change to all components using that token without code modifications. |
| **Rationale** | CSS cascade ensures automatic propagation. |
| **Source** | Requirement 1.2 |
| **Verification** | Property-based test: change token, verify all usages update |

##### FR-DT-003: Color Palettes
| Attribute | Value |
|-----------|-------|
| **ID** | FR-DT-003 |
| **Title** | Color Palette Definition |
| **Priority** | P0 - Critical |
| **Description** | THE Design_System SHALL define 5 color palettes: neutral (10 shades), primary (5 shades), success (3 shades), warning (3 shades), error (3 shades). |
| **Rationale** | Comprehensive palette covers all UI states and semantic meanings. |
| **Source** | Requirement 1.3 |
| **Verification** | CSS inspection; color contrast validation |

##### FR-DT-004: Spacing Scale
| Attribute | Value |
|-----------|-------|
| **ID** | FR-DT-004 |
| **Title** | Spacing Scale Definition |
| **Priority** | P0 - Critical |
| **Description** | THE Design_System SHALL define 8 spacing scale values: 4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px as CSS custom properties. |
| **Rationale** | Consistent spacing creates visual rhythm and hierarchy. |
| **Source** | Requirement 1.4 |
| **Verification** | CSS inspection |

##### FR-DT-005: Typography Scale
| Attribute | Value |
|-----------|-------|
| **ID** | FR-DT-005 |
| **Title** | Typography Scale Definition |
| **Priority** | P0 - Critical |
| **Description** | THE Design_System SHALL define 6 typography scale values: xs (12px), sm (14px), base (16px), lg (18px), xl (20px), 2xl (24px). |
| **Rationale** | Limited scale ensures typographic consistency. |
| **Source** | Requirement 1.5 |
| **Verification** | CSS inspection |

##### FR-DT-006: Font Family
| Attribute | Value |
|-----------|-------|
| **ID** | FR-DT-006 |
| **Title** | Primary Font Family |
| **Priority** | P0 - Critical |
| **Description** | THE Design_System SHALL use Geist font family as primary with system-ui, -apple-system, sans-serif as fallback chain. |
| **Rationale** | Geist provides modern, readable typography; fallbacks ensure graceful degradation. |
| **Source** | Requirement 1.6 |
| **Verification** | CSS inspection; visual verification |

##### FR-DT-007: Elevation Levels
| Attribute | Value |
|-----------|-------|
| **ID** | FR-DT-007 |
| **Title** | Shadow Elevation Levels |
| **Priority** | P1 - High |
| **Description** | THE Design_System SHALL define 3 elevation levels using box-shadow: sm (subtle), md (medium), lg (prominent). |
| **Rationale** | Elevation creates depth hierarchy without heavy visual weight. |
| **Source** | Requirement 1.7 |
| **Verification** | CSS inspection; visual verification |

##### FR-DT-008: Border Radius Tokens
| Attribute | Value |
|-----------|-------|
| **ID** | FR-DT-008 |
| **Title** | Border Radius Token Definition |
| **Priority** | P1 - High |
| **Description** | THE Design_System SHALL define border-radius tokens: none (0), sm (4px), md (8px), lg (12px), full (9999px). |
| **Rationale** | Consistent border radius creates cohesive component appearance. |
| **Source** | Requirement 1.8 |
| **Verification** | CSS inspection |

#### 3.1.2 Glassmorphism Surface System

##### FR-GL-001: Backdrop Blur
| Attribute | Value |
|-----------|-------|
| **ID** | FR-GL-001 |
| **Title** | Glassmorphism Backdrop Blur |
| **Priority** | P0 - Critical |
| **Description** | THE Design_System SHALL implement glassmorphism surfaces with `backdrop-filter: blur(12px)`. |
| **Rationale** | Blur effect creates frosted glass appearance. |
| **Source** | Requirement 2.1 |
| **Verification** | CSS inspection; visual verification |

##### FR-GL-002: Surface Levels
| Attribute | Value |
|-----------|-------|
| **ID** | FR-GL-002 |
| **Title** | Surface Level Definition |
| **Priority** | P0 - Critical |
| **Description** | THE Design_System SHALL define 3 surface levels: surface-1 (cards, 100% opacity), surface-2 (modals, 80% opacity), surface-3 (overlays, 60% opacity). |
| **Rationale** | Layered surfaces create depth without obscuring content. |
| **Source** | Requirement 2.2 |
| **Verification** | CSS inspection |

##### FR-GL-003: Surface Borders
| Attribute | Value |
|-----------|-------|
| **ID** | FR-GL-003 |
| **Title** | Surface Border Styling |
| **Priority** | P1 - High |
| **Description** | WHEN displaying a surface THEN the Design_System SHALL apply a subtle border with 10% opacity. |
| **Rationale** | Subtle borders define surface boundaries without harsh lines. |
| **Source** | Requirement 2.3 |
| **Verification** | CSS inspection |

##### FR-GL-004: WCAG Contrast
| Attribute | Value |
|-----------|-------|
| **ID** | FR-GL-004 |
| **Title** | WCAG AA Contrast Compliance |
| **Priority** | P0 - Critical |
| **Description** | THE Design_System SHALL maintain minimum 4.5:1 contrast ratio for normal text and 3:1 for large text on all surfaces. |
| **Rationale** | WCAG 2.1 AA compliance ensures accessibility. |
| **Source** | Requirement 2.4 |
| **Verification** | Automated contrast ratio testing |

##### FR-GL-005: Hover States
| Attribute | Value |
|-----------|-------|
| **ID** | FR-GL-005 |
| **Title** | Interactive Surface Hover |
| **Priority** | P1 - High |
| **Description** | WHEN a surface contains interactive elements THEN the Design_System SHALL apply hover state with 5% opacity increase. |
| **Rationale** | Subtle hover feedback indicates interactivity. |
| **Source** | Requirement 2.6 |
| **Verification** | Visual verification; E2E test |

#### 3.1.3 Role-Based Access Control

##### FR-RBAC-001: Access Levels
| Attribute | Value |
|-----------|-------|
| **ID** | FR-RBAC-001 |
| **Title** | User Access Level Support |
| **Priority** | P0 - Critical |
| **Description** | THE Role_Manager SHALL support 3 access levels: Admin (full access), Operator (operational access), Viewer (read-only access). |
| **Rationale** | Role-based access ensures appropriate UI visibility. |
| **Source** | Requirement 3.1 |
| **Verification** | Unit test; E2E test |

##### FR-RBAC-002: Admin UI Visibility
| Attribute | Value |
|-----------|-------|
| **ID** | FR-RBAC-002 |
| **Title** | Admin Role UI Elements |
| **Priority** | P0 - Critical |
| **Description** | WHEN a user has Admin role THEN the UI SHALL display all management controls including create, edit, delete, and approve actions. |
| **Rationale** | Admins require full control capabilities. |
| **Source** | Requirement 3.2 |
| **Verification** | E2E test with admin JWT |

##### FR-RBAC-003: Operator UI Visibility
| Attribute | Value |
|-----------|-------|
| **ID** | FR-RBAC-003 |
| **Title** | Operator Role UI Elements |
| **Priority** | P0 - Critical |
| **Description** | WHEN a user has Operator role THEN the UI SHALL display operational controls including view, execute, and monitor actions, but NOT delete or approve actions. |
| **Rationale** | Operators need operational access without destructive capabilities. |
| **Source** | Requirement 3.3 |
| **Verification** | E2E test with operator JWT |

##### FR-RBAC-004: Viewer UI Visibility
| Attribute | Value |
|-----------|-------|
| **ID** | FR-RBAC-004 |
| **Title** | Viewer Role UI Elements |
| **Priority** | P0 - Critical |
| **Description** | WHEN a user has Viewer role THEN the UI SHALL display read-only views with view and monitor actions only. |
| **Rationale** | Viewers should not have access to modify operations. |
| **Source** | Requirement 3.4 |
| **Verification** | E2E test with viewer JWT |

##### FR-RBAC-005: JWT Role Extraction
| Attribute | Value |
|-----------|-------|
| **ID** | FR-RBAC-005 |
| **Title** | JWT Token Role Parsing |
| **Priority** | P0 - Critical |
| **Description** | THE Role_Manager SHALL retrieve role information from the `role` claim in the JWT token payload. |
| **Rationale** | JWT provides secure, stateless role transmission. |
| **Source** | Requirement 3.5 |
| **Verification** | Unit test with various JWT payloads |

##### FR-RBAC-006: Default Role Fallback
| Attribute | Value |
|-----------|-------|
| **ID** | FR-RBAC-006 |
| **Title** | Missing Role Default Behavior |
| **Priority** | P0 - Critical |
| **Description** | WHEN role information is unavailable or JWT is invalid THEN the UI SHALL default to Viewer mode with read-only access. |
| **Rationale** | Fail-safe default prevents unauthorized access. |
| **Source** | Requirement 3.6 |
| **Verification** | Unit test with invalid/missing JWT |

##### FR-RBAC-007: Alpine Store Integration
| Attribute | Value |
|-----------|-------|
| **ID** | FR-RBAC-007 |
| **Title** | Role State in Alpine Store |
| **Priority** | P0 - Critical |
| **Description** | THE Role_Manager SHALL cache role state in Alpine.js store (`$store.auth`) for reactive UI updates. |
| **Rationale** | Alpine store enables reactive role-based rendering. |
| **Source** | Requirement 3.7 |
| **Verification** | Unit test; integration test |

##### FR-RBAC-008: Admin Control Directive
| Attribute | Value |
|-----------|-------|
| **ID** | FR-RBAC-008 |
| **Title** | Admin-Only Control Visibility |
| **Priority** | P1 - High |
| **Description** | WHEN displaying admin-only controls THEN the UI SHALL use `x-show="$store.auth.isAdmin"` Alpine directive. |
| **Rationale** | Declarative visibility simplifies role-based UI. |
| **Source** | Requirement 3.8 |
| **Verification** | Code inspection; E2E test |

... (rest of provided UI SRS continues unchanged)

---

## Appendix H — Implementation backlog (short-term, informative)

This appendix lists concrete implementation tasks derived from the roadmap. It is informative and does not change normative requirements.

* Create Django Ninja skeleton (`/api/v2`) and Channels WS endpoints for:
  * Workflow status updates
  * A2A thread streaming
* Add Milvus Helm chart under `helm/` and create a migration script (example invocation):
  * `python scripts/migrate_vectors.py --src qdrant --dst milvus --batch 5000`
* Deploy SpiceDB in dev compose and wire a minimal schema with a simple check call from gateway.
* Implement Outbox pattern in common libs and replace direct Kafka publish calls in services.
* Add audit middleware capturing: `tenant_id`, `principal_id`, `action`, `resource`, `decision`, `correlation_id`.
* Expose `/metrics` on every Tier-0 service and wire OTEL exporters.
* Write A2A MVP:
  * models (threads, messages)
  * APIs (create thread, post message, stream messages)
  * WS endpoint `/ws/a2a/{thread_id}`
* CI updates:
  * lint (ruff), type-check (mypy), security scan (trivy)
  * unit tests + integration tests
  * compose smoke tests
* Documentation sync:
  * auto-generate OpenAPI docs into `docs/`
  * remove any ✅ not backed by CI

---

## Appendix I — Long-term vision (informative)

* Self-optimizing workflows: Temporal activities can request RAG-enhanced suggestions from SomaBrain and adapt execution paths based on policy feedback.
* Dynamic tool discovery: agents publish capability descriptors; hub auto-registers them in the tool registry.
* Policy-driven budget enforcement: OPA rules read real-time usage metrics and throttle agents exceeding budgets.
* Multi-region federation: replicate Postgres and Milvus across regions; use SpiceDB relationships for cross-region tenancy.
* Zero-touch upgrades: blue/green deployments with canary traffic routing and automated schema migrations.

---

## Appendix J — Scalability pillars and concrete actions (informative)

### J.1 Core scaling pillars

| Pillar | What it solves | Recommended patterns |
| --- | --- | --- |
| Stateless front-end | Unlimited request concurrency, no state loss | Gateway as stateless reverse proxy; HPA; per-tenant rate limits |
| Event-driven backbone | Decouple producers/consumers, smooth spikes | Kafka with Outbox; Kafka Streams/Flink for materialized views |
| Durable storage | Persist billions of rows without hot-spotting | Partition by tenant/date; distributed SQL options where required |
| Workflow engine | Scale long-running orchestrations | Temporal worker pools; autoscale on queue lag |
| A2A collaboration | High-volume inter-agent traffic | Postgres append-only log + Kafka fan-out + WS/SSE |
| Caching layer | Reduce DB load for hot reads | Redis cluster for sessions, OPA cache, vector hot cache, recent A2A |
| Observability & alerting | Detect bottlenecks early | Prometheus/Grafana/OTEL + SLO alerts |
| Infrastructure automation | Repeatable scaling | Helm + GitOps + chaos testing |

### J.2 Concrete actions (next 4 weeks)

* Deploy Envoy/NGINX edge proxy with TLS termination.
* Enable per-tenant rate-limits using Redis-backed token bucket.
* Provision Kafka with replication factor 3 and enable idempotent producers.
* Partition core tables by tenant/date and configure connection pooling.
* Containerize Temporal workers and scale via HPA on queue lag.
* Move A2A fan-out to Kafka; keep Postgres as system-of-record.
* Deploy Redis cluster for caches (OPA, sessions, hot vectors, recent A2A).
* Install Prometheus Operator + Grafana and set alert thresholds.
* Add load-test stage in CI (k6/locust) and chaos experiments (broker loss, worker pause).

---

## Appendix K — Long-term scaling roadmap (informative)

| Milestone | Target | Success metric |
| --- | --- | --- |
| Multi-region replication | Cross-region Kafka + logical DB replication | < 5% cross-region latency for reads; zero data loss on failover |
| Hot-cold vector store | Hot vectors in RAM, cold shards in object store | Recall latency < 150ms (hot), < 500ms (cold) |
| Serverless tool execution | Offload heavy tool invocations | Tool p95 ≤ 2s; cost per call < $0.001 |
| Dynamic autoscaling | KEDA on Kafka lag/queue length | Scaling reacts < 30s, lag < 5s |
| Zero-downtime deploys | Canary + automated rollback | 99.9% deploy success, < 30s rollback |
| Immutable audit log | Tamper-evidence in ClickHouse | > 10M events query < 2s, proof of integrity |

---

## Appendix L — Quick-start checklist for millions of transactions (informative)

* Deploy stateless gateway + per-tenant rate-limits.
* Switch state changes to Outbox → Kafka flow.
* Partition/shard Postgres tables by tenant/date and enable pooling.
* Scale Temporal workers via HPA based on queue lag.
* Store A2A messages in Kafka and stream via WS/SSE.
* Use Redis cluster for OPA cache, sessions, and hot vector results.
* Wire Prometheus + Grafana and set SLO alerts.
* Run load tests (10k RPS) and chaos experiments before production rollout.

---

**End of document**
