# Engineering Playbook (Canonical)

> Shared norms for development velocity, quality, and architectural integrity.

## Core Coding Standards
- Python 3.11+ only; prefer modern features (match, dataclasses where appropriate, but Pydantic models for contracts).
- Time: always `datetime.now(UTC)`; never naive datetimes.
- Logging: use `logging` with structured context (`extra={}`) – no `print`.
- Imports: no `# noqa: E402` – resolve by refactoring to factories/DI.
- Error handling: catch narrowly; log unexpected exceptions with stack (`logger.exception`).
- Config access: only via Settings object; avoid direct `os.getenv` in business logic.
- Avoid premature abstraction; introduce Protocols after 2+ concrete implementations.

## Architecture Rules
- FastAPI apps created via `create_app` (bootstrap with observability + lifespan).
- Service boundaries exchange Pydantic contract models only (no raw dicts, no ORM models).
- Domain logic separated from I/O (adapters and repositories).
- Event publishing uses Outbox pattern for durability (Phase 3+).
- SPIFFE/TLS initialization done in lifespan startup.

## Branching & Git Workflow
- `main`: always deployable; passes CI gates.
- Feature branches: `feat/<short-desc>`.
- Refactors: `refactor/<scope>`.
- Fixes: `fix/<issue-id-or-short-desc>`.
- Docs: `docs/<topic>`.
- Pull Requests: reference roadmap phase and link related contracts.

## Commit Hygiene
- Conventional style (not enforced yet): `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`.
- Keep commits focused; avoid mixing refactor + feature + formatting.

## CI Quality Gates (Target Phase 5)
1. Formatting: `black --check .`
2. Lint: `ruff check .`
3. Typing: `mypy services/common services/pricing-service services/gateway-api`
4. Tests: `pytest -q --maxfail=1 --disable-warnings`
5. Coverage threshold: 75% (raise gradually to 85%).
6. No new TODOs without issue link.

## Testing Strategy
- Unit: pure functions, protocol implementations – fast, isolated.
- Contract: schema snapshots (`model_dump()` round‑trip validation).
- Integration: docker-compose multi-service interactions (gateway ↔ pricing ↔ orchestrator).
- Load: scenario harness after baseline stability (Phase 5+).
- Resilience: targeted chaos experiments (adapter latency, Redis outage) (Phase 6+).

## Dependency Management
- Pin critical infra libs (temporalio, opentelemetry) with compatible semver ranges.
- Avoid heavy optional deps in core path; lazy import in adapters.
- Security updates: monthly sweep (`pip-audit` planned Phase 5).

## Observability Practices
- Include `tenant_id`, `trace_id`, `workflow_id` in structured log context where available.
- Metrics naming: `service.subsystem.metric_name` (e.g., `pricing.adapter.latency_ms`).
- Histogram preferred for latency; counter for occurrences; gauge for current state.
- Trace spans wrap external calls (HTTP, DB, Kafka publish).

## Performance Guidelines
- Cache external pricing lookups (TTL) – done.
- Use async clients for network-bound operations (httpx, aioredis).
- Avoid blocking CPU tasks inside async endpoints; offload to workers.

## Security & Compliance
- Secrets through Vault (future) or env mounted files; never committed.
- No plaintext tokens in logs; mask sensitive fields.
- Policy decisions logged with outcome + rule id (no full PII).

## Release & Deployment
- Semantic version increments per roadmap phase completion.
- Changelog curated from merged PR titles.
- Tagged images: `service_name:vX.Y.Z` + `service_name:latest`.

## Vibe & Culture Rules (Explicit)
- Clarity over cleverness; minimal magic.
- Incremental improvements – avoid large unreviewable diffs.
- Explicit boundaries – contracts first, implementations second.
- Respect latency budgets – instrument before optimizing.
- Leave modules cleaner than you found them.

## Adoption Checklist (New Service)
1. Create settings subclass extending `BaseServiceSettings`.
2. Implement routes via factory and wire with `create_app`.
3. Define contract models for external responses.
4. Add observability (automatic via bootstrap) + initial metrics.
5. Provide health/readiness endpoints.
6. Add unit tests for contracts and critical logic.
7. Document service purpose in `docs/`.

## Continuous Improvement Backlog
- Enforce conventional commits (pre-commit hook) – Phase 5.
- Introduce automatic dependency update bot – Phase 6.
- Add security scanning (SAST/secret scan) – Phase 5.
- Chaos experiment suite – Phase 6.

_Last updated: 2025-11-08_
