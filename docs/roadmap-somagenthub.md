# SomaAgentHub Integrated Development Roadmap (Canonical)

> Source of truth for architecture direction, progress, and delivery plan. This document merges prior analysis (architecture, flow, patterns) with the pragmatic execution roadmap. Keep this file updated; link here from other docs.

## Vision
Deliver a modular, event-aware agent orchestration platform with strong contracts, predictable latency, and transparent cost governance. All services share consistent startup semantics, observability, security posture, and development ergonomics.

## Strategic Pillars
1. Configuration & Bootstrap Unification
2. Typed Service Contracts & Domain Isolation
3. Interface-Driven Architecture (Adapters, Repositories, Policy Engine)
4. Event-Centric Communication & Auditability
5. Cost, Policy, & Safety Guardrails (Pricing + Policy + Moderation)
6. Observability & Operability (Metrics, Tracing, Structured Logs, SLOs)
7. Reliability & Performance (Caching, Backpressure, Circuit Breakers)
8. Testing & Quality Automation (CI Gates, Coverage, Load Profiles)
9. Developer Experience (Tooling, Docs, Templates, Local Environments)
10. Security & Compliance (Secrets, AuthN/Z, Data Boundaries)

---
## Context & Analysis (Session Summary)
> Consolidated overview of where we started and what we achieved so far.

- Current Mandates:
	- Add gateway + pricing tests (Grafana explicitly deferred for now).
	- Enforce UTC globally; standardize formatting (Black), linting (Ruff), typing (MyPy).
	- Refactor toward centralized, “architecturally perfect” bootstrap + config.
- Reliability & Modernization Delivered:
	- Pricing service: adapter failure handling, refresh loop, TTL caching.
	- Gateway: budget precheck integration path prepared via contracts.
	- FastAPI lifespan adoption and Pydantic v2 migration begun.
	- System-wide switch to `datetime.now(UTC)`.
- Static Quality Baseline:
	- Introduced Ruff + Black; eliminated major lint backlogs (print→logging, import order, unused vars). Intentional W293 ignores confined to templated examples.
	- MyPy baseline established; common, pricing, observability tightened and cleaned.
- Architecture Consolidation:
	- Shared `BaseServiceSettings` and `create_app` bootstrap for FastAPI.
	- Centralized observability initialization; optional Prometheus handled gracefully.
	- ClickHouse shim hardened to match production signatures for MyPy + tests.
	- Authored `ARCHITECTURE.md` and this unified roadmap.
- Phase 1 Execution (Exemplars):
	- Pricing-service refactored to shared bootstrap; gateway now migrated as well.
	- Preparing shared contract models and Protocols for broader adoption.
- Pending High-Value Work:
	- Shared contract models (budget decision, build precheck, snapshot types).
	- ToolAdapter Protocol; repository interfaces; event contracts.
	- Propagate bootstrap + contracts to orchestrator and identity.

Status Flags:
- Deferred: Grafana dashboards (per directive).
- Active: MyPy/CI hardening, contracts, DI patterns, event-first refactors.

---
## Phase 1 – Foundations (IN PROGRESS)
> Goal: Remove bootstrap fragmentation; establish baseline contracts; improve lint + typing health.

- Unified settings base (`BaseServiceSettings`) & central bootstrap (`create_app`).
- Pilot refactors: `pricing-service` and `gateway-api` moved to shared bootstrap and lifespan.
- Observability consolidation (OpenTelemetry tracing + metrics + FastAPI instrumentation) via shared module.
- MyPy baseline; selective strict modules (common, pricing, observability) clean.
- Initial shared contracts (pricing decisions, build precheck) – TO DO next.
- Architecture doc and this canonical roadmap established.

Success Criteria:
- New services start in < 5 min via template.
- 0 duplicated logging/tracing initialization blocks.
- MyPy errors limited to legacy modules only.

---
## Phase 2 – Interfaces & Contracts (PLANNED)
> Goal: Formalize boundaries; prevent domain leakage; enable easier substitution/testing.

Key Deliverables:
- `services/common/contracts/` package: pricing, gateway (wizard/budget), orchestrator workflow, identity tokens.
- ToolAdapter `Protocol` + adapter registry (introspection + health).
- Repository `Protocol`s (BuildRunRepo, PricingSnapshotRepo) decoupling persistence.
- PolicyClient abstraction wrapping OPA + fallback mock.
- Gateway & orchestrator refactors to return contract DTOs only.
- Event schema definitions (pricing snapshot created, build run queued, token issued).

Quality Gates:
- No dict-shaped responses leaking internal models.
- Adapter implementations unit-tested via protocol compliance tests.

---
## Phase 3 – Event & Workflow Layer
> Goal: Introduce domain events and asynchronous coupling where latency tolerance exists.

Actions:
- Kafka topics formalization + naming convention (`domain.event.version`).
- Outbox pattern (persist then publish) for critical events (pricing snapshots, workflow start, moderation strike triggered).
- Temporal signal/event integration mapping to domain events.
- Unified event publisher interface (Kafka + in-memory fallback for tests).

Reliability Enhancements:
- Retry + DLQ strategy defined per topic.
- Consumer health & lag metrics exported.

Success Metrics:
- Reduction in cross-service synchronous calls for non-critical paths.
- Event delivery > 99.9% within SLA (e.g. < 2s end-to-end publish + consume). 

---
## Phase 4 – Observability & Guardrails
> Goal: Deep operational insights + proactive cost/security enforcement.

Deliverables:
- Structured logging (JSON) + correlation IDs (`trace_id`, `workflow_id`, `tenant_id`).
- SLO definitions (availability, p95 latency for critical endpoints, precheck decision time).
- Budget guardrail pipeline (pricing pre-evaluation + policy check + override audit trail).
- Moderation strike publisher + alerting integration.
- Distributed tracing sampling strategy (adaptive based on error rates).

Metrics Inventory:
- Gateway: request rate, auth failures, budgeting decisions within limit.
- Pricing: adapter fetch latency, cache hit ratio, failure counts.
- Orchestrator: active workflows, queue depth, Temporal error classifications.

---
## Phase 5 – Full Typing & CI Enforcement
> Goal: Harden quality gates and stabilize delivery.

Additions:
- Raise MyPy strict coverage to all `services/common` and contract packages.
- CI pipeline: `ruff`, `black --check`, `mypy`, `pytest --maxfail=1`, minimum coverage threshold.
- Pre-commit hooks distribution.
- Golden integration tests (gateway ↔ pricing ↔ orchestrator path).
- Load test harness scenario profiles (campaign launch, multi-agent burst, snapshot ingestion).

Exit Criteria:
- < 5% flaky test rate over rolling 30-day window.
- p95 latency targets met for gateway critical endpoints.

---
## Phase 6 – Data & Analytics Maturation
> Goal: Expand analytics while keeping isolation and contract integrity.

Plans:
- Introduce query service layer avoiding direct DB model leakage.
- Time-series aggregation for agent performance and cost trend lines.
- Pricing optimization hooks (dynamic rate adjustments).
- Forecasting pipeline (GPU hour projection) feeding budgeting advice.

---
## Phase 7 – Security & Compliance Enhancements
> Goal: Strengthen trust posture before broader external adoption.

Initiatives:
- Secret management consolidation (Vault workflows, rotation automation).
- SPIFFE/TLS strict enforcement across internal service calls (no plaintext fallbacks in production).
- Policy-as-code expansion (OPA bundles + versioned rules).
- Enhanced moderation workflow (appeals, audit trails).
- RBAC model formalization + contract tests for permission boundaries.

---
## Cross-Cutting Standards
- UTC everywhere (already enforced).
- No direct prints; structured logging only.
- Avoid E402 import ordering suppressions; use DI/factories.
- Pydantic v2 everywhere for models; `BaseModel` for contracts.
- Adopt `Protocol` for pluggable components.
- Environment derived only via Settings; no ad-hoc `os.getenv` in service logic except bootstrap.
 - Grafana dashboards are DEFERRED (explicitly out-of-scope for now).

---
## Testing Strategy Summary
| Layer | Approach | Tooling |
|-------|----------|---------|
| Unit | Pure functions, Protocol implementations | pytest + coverage |
| Contract | Request/response schema validation | pydantic models + snapshots |
| Integration | Multi-service (gateway ↔ pricing ↔ orchestrator) | docker-compose + pytest markers |
| Load | Scenario profiles (campaign bursts, ingestion) | locust / custom harness |
| Chaos (Future) | Fault injection (adapter latency, Redis down) | tox env / resiliency scripts |

---
## Delivery & Milestones (Rolling 90 Days)
1. Weeks 1–3: Finish Phase 1 (gateway, orchestrator refactors + initial contracts).
2. Weeks 4–6: Phase 2 adapter/repository Protocols + event schema draft.
3. Weeks 7–9: Implement event publisher + outbox + structured logging upgrade.
4. Weeks 10–12: CI strict gates + initial load profiles + budgeting guardrail metrics.

---
## Risk Register (Active)
| Risk | Impact | Mitigation |
|------|--------|------------|
| Legacy dynamic imports linger | Type instability | Incremental DI refactors per module |
| Adapter failures spike latency | Budgeting & orchestration delays | Circuit breaker + retry caps + metrics alarms |
| Event duplication (at-least-once) | Inconsistent state | Idempotent consumers keyed by `event_id` |
| Over-expansion of strict MyPy early | Velocity drag | Staged enablement per package |
| Grafana scope creep | Distracts from core goals | Keep dashboards deferred; revisit post-Phase 4 |

---
## Glossary (Selected)
- Contract: Typed boundary model exchanged between services.
- Adapter: Pluggable integration unit implementing a `Protocol`.
- Outbox: Reliable event publishing pattern ensuring atomicity.
- Guardrail: Policy or cost constraint enforced prior to action.

---
## Maintenance
- Update this file upon completion of each phase milestone.
- Link new contract definitions and event schemas.
- Reflect changes in `ARCHITECTURE.md` summary section.

---
_Last updated: 2025-11-08_
