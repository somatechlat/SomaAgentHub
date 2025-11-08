# 90-Day Delivery Plan

> Time-bound execution schedule aligned with roadmap phases and sprint waves.

## Guiding KPIs
- Bootstrap Adoption Coverage: % services using `create_app`.
- Contract Coverage: # boundary endpoints returning typed models / total.
- MyPy Strict Coverage: % of targeted modules with zero errors under strict flags.
- Mean Approval Latency (wizard budget precheck): p95 < 400ms.
- Pricing Adapter Reliability: < 2% failed fetch attempts (rolling 7d).
- Temporal Workflow Success Rate: > 99% without manual intervention.

## Weekly Cadence
- Monday: Sprint planning & KPI review.
- Wednesday: Mid-sprint checkpoint; adjust backlog if blockers.
- Friday: Demo + retro; roadmap doc update.

## Wave Breakdown
### Weeks 1–3 (Wave 1: Foundations & Contracts)
Goals:
- Complete bootstrap refactors for gateway, pricing, orchestrator.
- Introduce pricing/gateway contract models and adopt in wizard precheck.
- Engineering playbook published; canonical roadmap integrated.
Metrics:
- Bootstrap Adoption Coverage >= 30% of services (3 pilot services).
- Contract Coverage (pricing/gateway) endpoints = 100% typed.
Deliverables:
- `services/common/contracts/pricing.py`
- Refactored orchestrator main to bootstrap.
- `engineering-playbook.md` and `roadmap-somagenthub.md` updates.

### Weeks 4–6 (Wave 2: Interfaces & Protocols)
Goals:
- ToolAdapter Protocol + registry.
- Repository Protocols for BuildRun & PricingSnapshot.
- Initial event schema definitions.
Metrics:
- Contract Coverage >= 50%.
- Protocol Implementations: ≥ 2 adapters validated.
Deliverables:
- `tool_service/adapters/protocols.py`
- `services/common/contracts/orchestrator.py` (workflow start DTOs).
- Event schema markdown in `docs/events.md`.

### Weeks 7–9 (Wave 3: Events & Guardrails)
Goals:
- Outbox pattern for pricing snapshots and wizard approvals.
- Structured logging with correlation IDs.
- Budget guardrail metrics exported.
Metrics:
- Event Delivery Success > 99.9%.
- Mean Approval Latency p95 < 400ms.
Deliverables:
- `services/common/events/publisher.py` (Kafka + in-memory).
- Logging context middleware enhancement.
- Extended pricing precheck metrics.

### Weeks 10–12 (Wave 4: CI Strictness & Load Profiles)
Goals:
- CI gate enforcement (ruff, black, mypy, pytest, coverage).
- Load test harness scenarios (campaign burst, pricing ingestion spike).
- Cost guardrail dashboards (Grafana still deferred for full integration; proto metrics only).
Metrics:
- MyPy Strict Coverage >= 70% of targeted modules.
- Coverage >= 75%.
Deliverables:
- Pre-commit hook config.
- `tests/load/` scenarios.
- CI pipeline updates (`.github/workflows/build.yml`).

## Risk Mitigation Actions
| Risk | Wave | Mitigation |
|------|------|-----------|
| Temporal connection instability | 1–3 | Retry/backoff wrapper + startup health gating |
| Adapter protocol churn | 4–6 | Version interfaces and provide shim layer |
| Event duplication | 7–9 | Idempotent consumer keys in outbox design |
| Strict typing slowdown | 10–12 | Stagger enabling by directory, publish schedule |

## Escalation Path
- Blockers > 24h: escalate to architecture lead; adjust sprint scope.
- KPI regression: immediate investigation; add remediation task to backlog.

## Reporting
- Update `docs/roadmap-somagenthub.md` after each wave.
- Maintain KPI table in weekly standup notes (future: automate).

_Last updated: 2025-11-08_
