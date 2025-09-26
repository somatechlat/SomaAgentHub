# Detailed Sprint Plan

This file contains a sprint-by-sprint breakdown derived from the canonical roadmap. Each sprint is ~2 weeks. Owners and JIRA/GitHub issues can be linked per task.

### Sprint 0 (Foundations) — Weeks 0–1
- Repo scaffold, developer docs, docker-compose stack (Kafka/Redis/Postgres/SomaBrain), SomaBrain client library, SLM fallback HTTP endpoints.
- Acceptance: local compose up; health endpoints green; README + Quickstart validated.

### Sprint 1 (Execution & Policy) — Weeks 2–3
- Async SLM queue + provider adapters.
- Policy Engine MVP + constitution fetching/caching.
- Identity & settings CRUD APIs.
- Acceptance: `POST /v1/sessions/start` enforces policy check; SLM requests surface in `slm.metrics`.

### Sprint 2 (Benchmarks & Observability) — Weeks 4–5
- Benchmark harness, scoring job, Agent One Sight dashboard basics.
- Notification orchestrator v1 and websocket hub.
- Acceptance: nightly benchmark run persists scores; dashboard shows model quality/latency.

### Sprint 2‑5 (Testing & QA) — Weeks 6–7
- Write end‑to‑end pytest suites covering Policy Engine → Orchestrator → SLM pipeline.
- Add contract tests for all public HTTP endpoints.
- Integrate tests into GitHub Actions CI pipeline.
- Acceptance: CI passes on every PR; coverage ≥ 80 %.

### Sprint 2‑6 (Documentation & Release Prep) — Weeks 8–9
- Update `README.md`, `Quickstart.md`, and API reference docs with the new endpoints.
- Create release‑candidate playbook and launch‑readiness checklist.
- Conduct a dry‑run release in a staging environment.
- Acceptance: documentation builds without errors; release checklist signed off.

### Sprint 3 (Advanced Orchestration) — Weeks 10–11
- MAO workflow integration (Temporal scaffold), voice/audio pipeline integration (ASR/TTS), marketplace builder alpha.
- Acceptance: import a capsule, instantiate a simple DAG, observe events in `project.events`.

### Sprint 4 (Hardening & Launch Readiness) — Weeks 12–13
- Security hardening (mTLS plan, Vault integration), CI/CD pipeline, load & chaos tests, and runbooks validated.
- Acceptance: RC pipeline passes, release checklist items met.

### Sprint 5 (AppSec & Compliance) — Weeks 14–15
- Capability-scoped JWTs, moderation-before-orchestration, sandboxed tool adapters, OTEL + Prometheus dashboards.
- Acceptance: kill-switch tested, moderation metrics appear and escalate.

### Sprint 6 (Marketplace & Automation) — Weeks 16–17
- Capsule marketplace full CRUD, attestation flows, MAO template import, billing hooks and exports.
- Acceptance: publish capsule → tenant installs → analytics billing event recorded.

### Sprint 7 (Analytics & Insights) — Weeks 18–19
- Capsule analytics dashboards, persona regression automation, anomaly detection.
- Acceptance: run persona regression; regressions are queued and visible in dashboard.

### Sprint 8 (Scalability & Multi-region) — Weeks 20–21
- Multi-region helm overlays, DR drills, QoS lanes, autoscaling policies.
- Acceptance: failover drill completes, CR observability shows federated metrics.

### Sprint 9 (Launch Readiness) — Weeks 22–23
- Final performance tuning, security audit remediation, documentation polish, GA playbook executed.
- Acceptance: GA checklist (docs/release/Launch_Readiness_Checklist.md) signed off.

### Sprint 10 (KAMACHIQ Mode Automation) — Weeks 24–25
- Planner/governance capsules, provisioning harness, end-to-end automation pilot.
- Acceptance: pilot project executed end-to-end with governance report and spending under budget.

---

Sprint checklists live in `docs/sprints/` and will be instantiated as sprints begin.
