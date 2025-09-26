# SomaStack Sprint Milestones

| Sprint | Focus | Key Deliverables |
|--------|-------|------------------|
| 0 (Completed) | Foundations | SomaBrain client library, constitution caching, SLM fallback HTTP routes, gateway request context middleware, docker-compose stack, admin console skeleton |
| 1 | Execution & Policy | Async SLM queue + provider adapters, policy engine MVP, identity/settings CRUD APIs, Storybook component groundwork |
| 2 | Benchmarks & Observability | Benchmark harness + scoring service, Agent One Sight dashboard, notification orchestrator v1 |
| 3 | Advanced Orchestration | MAO workflow integration, voice/audio pipeline, marketplace builder alpha |
| 4 | Hardening & Launch Readiness | Security hardening, deployment automation, load/chaos tests, documentation polish |
| 5 | AppSec & Compliance | Capability-scoped JWTs + MFA, moderation-before-orchestration, sandboxed tool adapters, OTEL/Prometheus dashboards, kill-switch runbooks |
| 6 | Marketplace & Automation | Marketplace attestation + approval flow (submissions/review APIs), MAO template import/scheduling (`POST /v1/templates/import`), billing ledgers/export (`POST /v1/billing/events`, `/v1/billing/ledgers`), capsule install/rollback endpoints (`POST /v1/installations`, `/v1/installations/{id}/rollback`), signed adapter releases |
| 7 | Analytics & Insights | Capsule analytics dashboards, persona regression automation (`/v1/persona-regressions/transition`), anomaly detection alerts (`/v1/anomalies/scan`), governance reports |
| 8 | Scalability & Multi-region | Multi-region deployment scripts, data residency enforcement, autoscaling benchmarks, DR drills (`dr_failover_drill`, `/v1/drills/disaster`, `/v1/drills/disaster/summary`) |
| 9 | Launch Readiness | Performance profiling script, security audit checklist, release candidate playbook, launch readiness checklist, community enablement |
| 10 | KAMACHIQ Mode Automation | Planner/governance capsules, provisioning harness prototype, MAO template orchestration (see `scripts/ops/schedule_dr_drill.py` pattern), analytics/governance reporting (`/v1/kamachiq/summary`), KAMACHIQ runbook |

Use this sheet alongside `Implementation_Roadmap.md` to track progress and assign owners.
