# Detailed Sprint Plan

This file contains a sprint-by-sprint breakdown derived from the canonical roadmap. Each sprint is ~2 weeks. Owners and JIRA/GitHub issues can be linked per task.

### Sprint 0 (Foundations) — Weeks 0–1
- Repo scaffold, developer docs, docker-compose stack (Kafka/Redis/Postgres/SomaBrain), SomaBrain client library, SLM fallback HTTP endpoints.
- Acceptance: local compose up; health endpoints green; README + Quickstart validated.
- **Tasks**:
  - Initialize repository, CI workflow, and basic Docker‑Compose.
  - Verify all services start with health checks.

### Sprint 1 (Execution & Policy) — Weeks 2–3
- Async SLM queue + provider adapters.
- Policy Engine MVP + constitution fetching/caching.
- Identity & settings CRUD APIs.
- Acceptance: `POST /v1/sessions/start` enforces policy check; SLM requests surface in `slm.metrics`.
- **Tasks**:
  - Implement real `POST /v1/sessions/start` (policy call, JWT issuance, SLM Kafka publish).
  - Add environment‑var configuration for Policy Engine and Identity Service URLs.
  - Write integration tests for session start (services/orchestrator/tests).
  - Ensure CI runs these tests on every push.

### Sprint 2 (Turn Loop & Kafka Events) — Weeks 4–5
- Turn‑loop SSE endpoint, audit & conversation Kafka publishing.
- Background consumer that logs audit events.
- Acceptance: SSE stream delivers three events; each event appears in Kafka topics.
- **Tasks**:
  - Implement `GET /v1/turn/{session_id}` with real Kafka publishing.
  - Add background Kafka consumer on startup.
  - Write end‑to‑end tests for the turn stream.
  - Extend CI to run orchestrator turn‑stream tests.

### Sprint 2‑5 (Testing & QA) — Weeks 6–7
- Write end‑to‑end pytest suites covering Policy Engine → Orchestrator → SLM pipeline.
- Add contract tests for all public HTTP endpoints.
- Integrate tests into GitHub Actions CI pipeline.
- Acceptance: CI passes on every PR; coverage ≥ 80 %.
- **Tasks**:
  - Create `tests/` for each service (policy‑engine, orchestrator, slm‑service).
  - Add coverage reporting step in CI.

### Sprint 2‑6 (Documentation & Release Prep) — Weeks 8–9
- Update `README.md`, `Quickstart.md`, and API reference docs with the new endpoints.
- Create release‑candidate playbook and launch‑readiness checklist.
- Conduct a dry‑run release in a staging environment.
- Acceptance: documentation builds without errors; release checklist signed off.
- **Tasks**:
  - Add usage examples for `/v1/sessions/start`, `/v1/turn`, marketplace and job APIs.
  - Verify docs render correctly with MkDocs.

### Sprint 3 (Marketplace Alpha) — Weeks 10–11
- Capsule marketplace full CRUD, attestation flows, MAO template import, billing hooks.
- Acceptance: publish capsule → tenant installs → analytics billing event recorded.
- **Tasks**:
  - Implement real marketplace endpoints (`/marketplace/publish`, `/marketplace/capsules`).
  - Add in‑memory store now, plan migration to Postgres.
  - Write tests for marketplace CRUD.

### Sprint 4 (Durable Jobs) — Weeks 12–13
- Job start endpoint, async background processing, result retrieval.
- Acceptance: job runs, status transitions from running → completed.
- **Tasks**:
  - Implement `/jobs/start` and `/jobs/{job_id}` with async worker.
  - Add unit tests for job lifecycle.

### Sprint 5 (Hardening & Launch Readiness) — Weeks 14–15
- Security hardening (mTLS, Vault), CI/CD pipeline, load & chaos tests, runbooks.
- Acceptance: RC pipeline passes, runbooks validated.
- **Tasks**:
  - Stub out mTLS config (future), add security headers.
  - Add load‑test scripts (locust) to CI.

### Sprint 6 (AppSec & Compliance) — Weeks 16–17
- Capability‑scoped JWTs, moderation, sandboxed tool adapters, OTEL + Prometheus dashboards.
- Acceptance: kill‑switch tested, moderation metrics appear.
- **Tasks**:
  - Extend JWT claims with capabilities.
  - Add Prometheus metrics for policy decisions and job executions.

### Sprint 7 (Analytics & Insights) — Weeks 18–19
- Capsule analytics dashboards, persona regression automation, anomaly detection.
- Acceptance: regression runs, results visible.
- **Tasks**:
  - Add basic analytics endpoint (`/analytics/capsules`).
  - Write tests for analytics aggregation.

### Sprint 8 (Scalability & Multi‑region) — Weeks 20–21
- Multi‑region helm overlays, DR drills, QoS lanes, autoscaling policies.
- Acceptance: failover drill completes, observability federated.
- **Tasks**:
  - Add Helm chart skeleton.
  - Write integration test that simulates region failover.

### Sprint 9 (Launch Readiness) — Weeks 22–23
- Final performance tuning, security audit remediation, docs polish, GA playbook.
- Acceptance: GA checklist signed off.
- **Tasks**:
  - Run performance benchmarks, update docs.

### Sprint 10 (KAMACHIQ Mode Automation) — Weeks 24–25
- Planner/governance capsules, provisioning harness, end‑to‑end automation pilot.
- Acceptance: pilot executed end‑to‑end with governance report.
- **Tasks**:
  - Prototype KAMACHIQ planner capsule.
  - Add end‑to‑end test covering full pipeline.

---
**Note:** Every sprint now includes a dedicated set of unit/integration tests that run automatically in the GitHub Actions CI workflow (`.github/workflows/ci.yml`). The CI pipeline ensures that code quality, test coverage, and linting are verified on each push.

Sprint checklists live in `docs/sprints/` and will be instantiated as sprints begin.
