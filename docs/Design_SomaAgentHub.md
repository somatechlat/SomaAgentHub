# SomaAgentHub - Design Specification

**Document ID:** SAH-DESIGN-2025-12-22
**Version:** 1.0 (draft)
**Date:** 2025-12-22
**Owner:** Agent Zero (SomaTech LAT)
**Derived from:** `docs/SRS_SomaAgentHub.md`

---

## 1. Purpose

This document translates the SRS into a concrete technical design for a production-grade, multi-tenant SomaAgentHub. It focuses on architecture, data flow, service boundaries, and implementation choices required to meet the SRS requirements.

---

## 2. Design goals

- Preserve a stable v1 FastAPI surface while adding v2 Django Ninja + Channels.
- Make Temporal the single source of truth for workflow execution.
- Enforce policy gating (OPA) and relationship authorization (SpiceDB) before side effects.
- Provide durable A2A collaboration with replay and audit.
- Scale to millions of transactions/day with strong consistency and observability.
- Conform UI to SUIDS while implementing components in Lit.

---

## 3. Architecture overview

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
  GW --> MEM[Memory Gateway Proxy]
  MEM --> SB[SomaBrain]
  SB --> VDB[(Milvus / Qdrant)]
  ORC --> COLLAB[A2A Collaboration]
  COLLAB --> PG
  COLLAB --> KAF
  KAF --> FLK[Flink Jobs]
  FLK --> CH[(ClickHouse)]
  ALL[All Services] --> OBS[OTEL + Prometheus + Grafana]
  ALL --> VAULT[Vault]
  ALL --> AUTHZ[SpiceDB]
  ALL --> KC[Keycloak OIDC]
```

---

## 4. Service boundaries

### 4.1 Gateway API

- Stateless ingress and routing layer.
- JWT validation via Identity service.
- OPA policy checks before side effects.
- Rate limiting per tenant and principal.
- Exposes v1 endpoints and routes to v2 control-plane when enabled.

### 4.2 Orchestrator API

- Submits workflows to Temporal.
- Provides workflow status, cancel, retry, and compensation operations.
- Emits audit and outbox events for state changes.

### 4.3 Orchestrator Worker

- Temporal worker executing workflows and activities.
- Scaled horizontally based on task queue lag.

### 4.4 Identity Service

- Issues and validates JWTs.
- Rotation and key management.
- OIDC federation optional via Keycloak.

### 4.5 Policy Engine (OPA)

- Centralized policy evaluation endpoint.
- Fail-closed behavior when unavailable.
- Decision caching in Redis.

### 4.6 Collaboration Service (A2A)

- Postgres system-of-record for threads/messages.
- Kafka fan-out for real-time UI and analytics.
- WS/SSE streaming via Channels.

### 4.7 Memory Gateway (Proxy)

- Thin proxy to SomaBrain for /memory endpoints.
- Enforces tenancy, authz, and audit at SAH boundary.

### 4.8 Tool and Capability Registry

- CRUD tools/models/capabilities.
- Semantic versioning and health probes.
- OPA/SpiceDB gated invocation.

### 4.9 Analytics

- Kafka -> Flink -> ClickHouse pipeline.
- Materialized views for latency, throughput, audit queries.

---

## 5. Data model overview

### 5.1 Core tables (Postgres)

- tenants
- principals
- roles
- agent_registry
- workflow_instances
- workflow_events
- outbox_events
- audit_log
- settings
- feature_flags
- conversation_threads
- conversation_participants
- conversation_messages
- conversation_digests

### 5.2 A2A message schema (minimum)

- tenant_id
- thread_id
- sender_type (agent|user|system)
- sender_id
- recipient_scope (thread|direct|role)
- workflow_id (optional)
- session_id (optional)
- message_kind (question|answer|plan|critique|artifact_ref|status|tool_result)
- content (text/structured JSON)
- artifact_refs (object-store URIs + hashes)
- created_at, correlation_id, causation_id

### 5.3 Outbox

- Outbox events created within the same transaction as state changes.
- Async publisher flushes events to Kafka with idempotence.

---

## 6. Workflow design

### 6.1 Workflow lifecycle

- Start: POST /sessions/start -> Temporal workflow created, workflow_id returned.
- Status: GET /sessions/{id} -> workflow status from Temporal history.
- Cancel/Retry: explicit endpoints with audit trail.
- Compensation: saga steps and compensators logged and replayable.

### 6.2 A2A workflow binding

- Workflow can create/join a thread.
- Messages posted during execution are bound to workflow_id.
- Workflow produces a digest artifact on completion.

---

## 7. Security and authorization

- AuthN: JWT via Identity service.
- AuthZ: SpiceDB relationship checks before privileged operations.
- Policy: OPA contextual checks before any side effect.
- Fail-closed behavior on authz/policy errors.
- Secrets: Vault for all sensitive data.

---

## 8. Observability and SLOs

- Prometheus metrics in all Tier-0 services.
- OTEL traces across gateway -> orchestrator -> temporal -> Kafka -> DB.
- Core metrics: request latency, error rate, queue lag, audit volume, A2A throughput.
- Alerts: CPU, Kafka lag, DB pool saturation, worker liveness.

---

## 9. UI design

- Must conform to SUIDS (tokens, components, accessibility, performance).
- Lit Web Components implementation.
- WS/SSE for live updates (workflow status, A2A threads).
- Admin console screens: tenants, agents, workflows, tools, policies, audit, analytics.

---

## 10. Scalability design

- Stateless gateway with autoscaling (HPA).
- Kafka as event backbone for all state changes.
- Partition Postgres by tenant/date for high volume.
- Redis cluster for hot reads and decision caches.
- Temporal worker pools scale on queue lag.

---

## 11. Deployment model

- Dev: Docker Compose profiles.
- Prod: Helm + K8s with GitOps (ArgoCD).
- Blue/green and canary deployments supported.

---

## 12. Migration strategy

- Keep v1 FastAPI during v2 rollout.
- Introduce Django Ninja v2 control-plane with Channels.
- Dual-write Qdrant + Milvus during migration window.
- Remove legacy v1 after verified parity.

---

## 13. Open items

- Complete SUIDS appendix in SRS (placeholder remains).
- Implement Agent Registry service.
- Implement collaboration service (A2A threads/messages).
