# SomaAgentHub - Task Backlog (Derived from SRS)

**Document ID:** SAH-TASKS-2025-12-22
**Version:** 1.0 (draft)
**Date:** 2025-12-22
**Source:** `docs/SRS_SomaAgentHub.md`

---

## 1. How to use this backlog

- Each task has an ID and acceptance criteria.
- Tasks are grouped by phase and pillar.
- Dependencies are listed to keep sequence clear.
- CI gates apply to all Tier-0 changes.

---

## 2. Phase 0 - Stabilization

### P0-A: Compile and health baseline

- **T0-001: Inventory compile errors**
  - **Scope:** Scan all Tier-0 services for syntax/indentation errors.
  - **Dependencies:** None.
  - **Acceptance:** All Tier-0 services import cleanly.

- **T0-002: Isolate lab services**
  - **Scope:** Move broken prototypes to `services/labs/` or exclude from CI packaging.
  - **Dependencies:** T0-001.
  - **Acceptance:** CI excludes labs and passes for Tier-0.

- **T0-003: Align env var prefix**
  - **Scope:** Enforce `SOMA_AGENT_HUB_*` and add a legacy alias layer.
  - **Dependencies:** T0-001.
  - **Acceptance:** New services use only canonical prefix; alias layer documented.

### P0-B: Worker wiring and baseline workflow

- **T0-004: Add orchestrator-worker container**
  - **Scope:** Compose and Helm run Temporal worker from orchestrator.
  - **Dependencies:** T0-001.
  - **Acceptance:** Worker polls Temporal task queue; sample workflow completes.

- **T0-005: Compose smoke test**
  - **Scope:** Compose up gateway, orchestrator, identity, policy, worker.
  - **Dependencies:** T0-004.
  - **Acceptance:** End-to-end workflow start -> complete is verifiable.

### P0-C: CI and guardrails

- **T0-006: Pre-commit hooks**
  - **Scope:** Add ruff, mypy, formatting, unicode guard.
  - **Dependencies:** None.
  - **Acceptance:** Pre-commit fails on invalid unicode and style violations.

- **T0-007: CI compile gate**
  - **Scope:** CI fails if any Tier-0 service fails import/compile.
  - **Dependencies:** T0-006.
  - **Acceptance:** CI blocks merge on compile failure.

- **T0-008: Helm lint + worker template sanity**
  - **Scope:** Helm chart must lint and render successfully with worker enabled/disabled; no optional probe/port errors.
  - **Dependencies:** T0-004.
  - **Acceptance:** `helm lint k8s/helm/soma-agent` passes; `helm template` renders without missing fields.

- **T0-009: Compose smoke script**
  - **Scope:** Add `scripts/smoke_compose.sh` to start Tier-0 (gateway, orchestrator, worker, identity, policy, temporal, redis, postgres) and run a sample workflow curl.
  - **Dependencies:** T0-004.
  - **Acceptance:** Script exits 0 after workflow completes; used in CI smoke job (`Smoke test Tier-0 with docker-compose`).

- **T0-010: CI workflow alignment**
  - **Scope:** All GitHub Actions jobs use `compile-tier0` + smoke script; labs excluded; memory-gateway not built.
  - **Dependencies:** T0-007, T0-009.
  - **Acceptance:** CI green on Tier-0; no lab services pulled or built.

- **T0-011: Pre-commit hooks (Tier-0 scope)**
  - **Scope:** Add `.pre-commit-config.yaml` with ruff/formatting/yamllint + safety hooks; provide Makefile target `pre-commit-install`.
  - **Dependencies:** None.
  - **Acceptance:** `make pre-commit-install` installs hooks; `pre-commit run --all-files` passes on Tier-0 code.

---

## 3. Phase 1 - Core SaaS foundations

### P1-A: Policy + authz enforcement

- **T1-001: Deploy SpiceDB (dev)**
  - **Scope:** Add SpiceDB service in compose + Helm with initial schema.
  - **Dependencies:** T0-007.
  - **Acceptance:** Basic relationship check works from gateway.

- **T1-002: Wire OPA checks (gateway)**
  - **Scope:** Ensure OPA evaluated before side effects.
  - **Dependencies:** T0-007.
  - **Acceptance:** Fail-closed behavior verified with integration test.

- **T1-003: Wire SpiceDB checks (gateway/orchestrator)**
  - **Scope:** Relationship checks for privileged operations.
  - **Dependencies:** T1-001.
  - **Acceptance:** Forbidden access returns 403; audited.

### P1-B: Outbox and audit

- **T1-004: Outbox library**
  - **Scope:** Implement Outbox repository and publisher in common libs.
  - **Dependencies:** T0-007.
  - **Acceptance:** Events publish only after DB commit.

- **T1-005: Replace direct Kafka publishes**
  - **Scope:** All services emit through Outbox only.
  - **Dependencies:** T1-004.
  - **Acceptance:** No direct producer usage remains in Tier-0.

- **T1-006: Audit middleware**
  - **Scope:** Record tenant/principal/action/resource/decision/correlation_id.
  - **Dependencies:** T1-004.
  - **Acceptance:** All mutations create audit entries.

### P1-C: A2A MVP

- **T1-007: A2A models and migrations**
  - **Scope:** Thread, participant, message, digest tables.
  - **Dependencies:** T0-007.
  - **Acceptance:** Migrations apply cleanly.

- **T1-008: A2A API**
  - **Scope:** Create/join/leave thread, post message, replay.
  - **Dependencies:** T1-007.
  - **Acceptance:** CRUD flows pass integration tests.

- **T1-009: A2A streaming**
  - **Scope:** WS/SSE for thread updates with cursor resume.
  - **Dependencies:** T1-008.
  - **Acceptance:** Reconnect resumes from cursor; no loss.

- **T1-010: Kafka fan-out for A2A**
  - **Scope:** Publish A2A events via Outbox to Kafka.
  - **Dependencies:** T1-004, T1-007.
  - **Acceptance:** Consumers receive messages; UI stream works.

---

## 4. Phase 2 - Autonomous agent lifecycle

### P2-A: Agent registry

- **T2-001: Agent registry models**
  - **Scope:** agent_instance_id, tenant_id, principal_id, capabilities, status.
  - **Dependencies:** T1-006.
  - **Acceptance:** Migrations applied, CRUD works.

- **T2-002: Agent registration API**
  - **Scope:** Register/update agent instances.
  - **Dependencies:** T2-001.
  - **Acceptance:** Registry lists active agents by tenant.

- **T2-003: Heartbeat and liveness**
  - **Scope:** Heartbeat endpoint + stale agent detection.
  - **Dependencies:** T2-002.
  - **Acceptance:** Stale agents marked unhealthy.

- **T2-004: Quarantine and decommission**
  - **Scope:** Transition states with audit.
  - **Dependencies:** T2-003.
  - **Acceptance:** Quarantined agents blocked by policy.

### P2-B: Autoscaling

- **T2-005: HPA signals**
  - **Scope:** Expose queue depth/lag metrics for autoscaling.
  - **Dependencies:** T2-002.
  - **Acceptance:** HPA can scale worker pools.

- **T2-006: Agent contract package**
  - **Scope:** Shared SDK/contracts for agent schema.
  - **Dependencies:** T2-001.
  - **Acceptance:** Versioned contracts used by SA01 + SAH.

## 5. Phase 3 - Vector memory, SomaBrain, analytics

### P3-A: SomaBrain integration

- **T3-001: SomaBrain client adapter**
  - **Scope:** Implement `services/common/somabrain_client` with health gating, retries, headers, audit hooks.
  - **Dependencies:** T1-006.
  - **Acceptance:** `/memory/*` calls execute circuit-breaker bounded retries, record audit rows.

- **T3-002: Memory gateway proxy**
  - **Scope:** Route legacy `/memory` endpoints through the new SomaBrain client while enforcing authz/policy.
  - **Dependencies:** T3-001.
  - **Acceptance:** Proxy respects tenant `X-Tenant-ID`, rejects missing tokens with 401.

- **T3-003: Workflow refactor**
  - **Scope:** Update orchestrator workflows to call the SomaBrain client rather than Qdrant internals.
  - **Dependencies:** T3-002.
  - **Acceptance:** Temporal sessions/MAO/capsule flows log somaBrain calls and pass tenant context.

### P3-B: Vector and analytics pipeline

- **T3-004: Milvus deployment**
  - **Scope:** Helm chart addition for Milvus, dual-write scripts, and Helm values for resource sizing.
  - **Dependencies:** T0-007, infrastructure readiness.
  - **Acceptance:** Dual-write script (`scripts/migrate_vectors.py`) finishes with checksum verification and rollback flag.

- **T3-005: Kafka → Flink → ClickHouse**
  - **Scope:** Build Flink job that consumes Kafka topics (`somaagent.*`), enriches metrics, writes to ClickHouse tables.
  - **Dependencies:** T1-004, T3-004.
  - **Acceptance:** Materialized views show p95 latency and audit counts.

- **T3-006: Observability dashboards**
  - **Scope:** Create Grafana dashboards for workflow latency, A2A throughput, vector search, Auto-scaler signals.
  - **Dependencies:** T3-005.
  - **Acceptance:** Dashboards render with real data; alerts fire when thresholds exceeded.

## 6. Phase 4 - Tool & capability marketplace + UI

### P4-A: Tool platform

- **T4-001: Tool registry refactor**
  - **Scope:** Introduce semantic versioning metadata + health probe definitions for each tool/service.
  - **Dependencies:** T1-004.
  - **Acceptance:** CRUD UI/API surfaces expose `version`, `health`, `capabilities`.

- **T4-002: Tool invocation outbox**
  - **Scope:** Emit audited events via Outbox for every tool call; add circuit-breakers per provider.
  - **Dependencies:** T4-001, T1-004.
  - **Acceptance:** Every completed invocation has audit + Kafka event; failing tool triggers compensation/log.

### P4-B: UI / SUIDS compliance

- **T4-003: Lit console scaffolding**
  - **Scope:** Build Lit components for layout, dashboards, data tables, status indicators using SUIDS tokens.
  - **Dependencies:** T1-009, `docs/SRS_SomaStack_UI.md`.
  - **Acceptance:** PoC screens (agents, workflows, A2A, policies, audit) pass axe-core scans and meet theme budgets.

- **T4-004: WebSocket/SSE integration**
  - **Scope:** Channels backend streams workflow/A2A updates to Lit client; supports cursor resumption.
  - **Dependencies:** T1-009, T1-010.
  - **Acceptance:** UI reflects live updates; reconnect resumes without duplication.

## 7. Phase 5 - API v2 + analytics UI

### P5-A: Django Ninja migration

- **T5-001: Django Ninja skeleton**
  - **Scope:** Create `/api/v2/` service with Django 5, Ninja routers, Channels layer, matching `/api/v1` contract.
  - **Dependencies:** T1-004, T1-006.
  - **Acceptance:** OpenAPI spec generated; contract tests pass against legacy clients.

- **T5-002: Navigation of Legacy APIs**
  - **Scope:** Nginx/router splits `/v1` (FastAPI) vs `/v2` to allow phased traffic (feature flag for routing).
  - **Dependencies:** T5-001.
  - **Acceptance:** Canary release route works with no downtime; `/api/v2` logged to audit.

### P5-B: UI metrics + analytics views

- **T5-003: Analytics console**
  - **Scope:** Lit dashboards display ClickHouse metrics (p95 latency, error-rate, throughput) and allow drill-down.
  - **Dependencies:** T3-005, T4-003.
  - **Acceptance:** Dashboards update via streaming data, pass accessibility tests.

- **T5-004: Feature flag rollout UI**
  - **Scope:** Settings page exposes feature profiles (minimal, standard, enhanced, max) with gating for ADM.
  - **Dependencies:** T4-003, FR-SET-003.
  - **Acceptance:** Selecting profile toggles flags and emits `settings.changed` events.

## 8. Phase 6 - Full SaaS release

- **T6-001: Sunset FastAPI /v1**
  - **Scope:** After 2-month parity, decommission FastAPI endpoints; update docs + clients to `/api/v2`.
  - **Dependencies:** T5-001, T5-002.
  - **Acceptance:** `/api/v1` returns 404 with migration guidance; traffic completely on `/api/v2`.

- **T6-002: Feature-flag agent scaling**
  - **Scope:** Roll out self-healing/autoscaling via feature flags and service mesh policies.
  - **Dependencies:** T2-006, T5-004.
  - **Acceptance:** Scaling toggled per tenant; SLA ≥ 99.5% maintained during rollout.

- **T6-003: Blue-green release drill**
  - **Scope:** GitOps + Helm orchestrate blue-green deployment; verify rollback triggers on SLO breach.
  - **Dependencies:** T5-002, `k8s/helm`.
  - **Acceptance:** Rollout completes without downtime; rollback reverts state within 30s on failure.

## 9. Compliance, security, and scaling guardrails

- **T9-001: Security matrix automation**
  - **Scope:** CI runs TLS checks, opa tests, SpiceDB schema validation, Vault injection verify, Trivy scans.
  - **Dependencies:** T0-007.
  - **Acceptance:** Pipeline fails on missing compliance steps; results posted to docs.

- **T9-002: Scalability checklist**
  - **Scope:** Document health gates for stateless services, partitioned storage, Kafka lag alerts.
  - **Dependencies:** T3-005, T5-003.
  - **Acceptance:** Checklist versioned in `docs/Tasks_SomaAgentHub.md` and referenced by runbooks.

- **T9-003: CI load + chaos stage**
  - **Scope:** Add k6 load test (10k RPS) and Chaos Mesh experiments (Kafka broker kill, Temporal pause) to GitHub Actions.
  - **Dependencies:** T5-001, T3-005.
  - **Acceptance:** Pipeline fails on SLO breach; experiments recorded in testing logs.

---

## 10. Deployment blueprint adoption

- **DBP-001: Compose parity with blueprint**
  - **Scope:** Align top-level `docker-compose.yml` with blueprint services (redis, postgres, kafka, temporal, milvus, vault, gateway, orchestrator, worker, identity, policy, authz, ui, airflow, observability).
  - **Dependencies:** T0-009.
  - **Acceptance:** `docker compose up -d` starts all services; health checks pass.

- **DBP-002: Helm values-prod**
  - **Scope:** Produce `values-prod.yaml` matching blueprint (replicas, autoscaling hints, TLS ingress, storage sizes).
  - **Dependencies:** T0-008.
  - **Acceptance:** `helm upgrade --install` with values-prod succeeds in test cluster.

- **DBP-003: Terraform modules wiring**
  - **Scope:** Ensure terraform modules for cluster, SQL, Kafka, Redis, Vault, DNS exist and output values for Helm.
  - **Dependencies:** T0-010.
  - **Acceptance:** `terraform apply` in sandbox succeeds; outputs feed Helm without manual edits.

- **DBP-004: GitOps pipeline**
  - **Scope:** ArgoCD/App-of-Apps for Helm chart; promote via Git tags.
  - **Dependencies:** DBP-002, DBP-003.
  - **Acceptance:** Git push updates cluster; rollbacks via Git revert.

- **DBP-005: Service mesh + mTLS**
  - **Scope:** Add Istio/Linkerd manifests to enforce mTLS between Tier-0 services.
  - **Dependencies:** DBP-001.
  - **Acceptance:** Traffic between services is mTLS; NetworkPolicies permit only required flows.

- **DBP-006: Observability stack**
  - **Scope:** Deploy Prometheus Operator, Grafana, Loki/EFK with dashboards/alerts from SRS.
  - **Dependencies:** DBP-001.
  - **Acceptance:** Dashboards show RPS, p95 latency, queue lag, DB pool usage; alerts fire on thresholds.

---

### 9.1 Observability

- **TX-OBS-001:** Add /metrics to all Tier-0 services.
- **TX-OBS-002:** OTEL tracing with correlation IDs.
- **TX-OBS-003:** Alert thresholds for CPU, lag, DB pools.

### 9.2 Security

- **TX-SEC-001:** Vault integration for all secrets.
- **TX-SEC-002:** CSP headers for console.
- **TX-SEC-003:** PII/secret detection on ingest paths.

### 9.3 Load testing

- **TX-LOAD-001:** k6/locust scenario for 10k RPS.
- **TX-LOAD-002:** Fail build if p95 > 300ms or error rate > 0.1%.

### 9.4 Chaos testing

- **TX-CH-001:** Kafka broker loss experiment.
- **TX-CH-002:** Temporal worker pause experiment.
- **TX-CH-003:** Network latency injection on gateway.

---

## 10. Notes

- This backlog is derived from the SRS and should be updated as requirements evolve.
- Task owners and estimates should be added in sprint planning.
