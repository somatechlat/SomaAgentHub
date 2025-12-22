# Canonical Roadmap – SomaAgentHub

_Last updated: 2025-12-22_

## Guiding Objectives
- Harden the production orchestration stack for autonomous agents.
- Migrate vector memory from Qdrant to Milvus while keeping Redis for KV/state.
- Standardize secret management through Vault across all services.
- Preserve Kafka as the event backbone for analytics and streaming.

## Current State (Dec 2025)
- Core services (gateway, orchestrator, identity, policy, memory, tool, pricing, notification) run with Kubernetes/Helm manifests.
- Memory Gateway code still uses Qdrant; Milvus migration is not yet implemented.
- Vault client wiring exists in `services/common/vault_client.py`; service-by-service adoption is partial.
- Analytics service entrypoint requires fixes before production use.
- CI now runs a Tier-0 docker-compose smoke (gateway, orchestrator, identity, policy, temporal, redis, postgres) via `scripts/smoke_compose.sh`; it tears down automatically.

## Milestones

### M1 — Stabilize Baseline (in progress)
- Fix analytics-service FastAPI bootstrap so health/metrics/router load correctly.
- Run and publish Postgres + ClickHouse migrations (`scripts/run-migrations.sh`).
- Clean README code fences and health-check defaults.

### M2 — Vault First (target: Jan 2026)
- Enforce Vault-backed secret loading for all services; remove legacy env fallbacks where feasible.
- Document canonical secrets per service and expected Vault paths.
- Add CI check to fail on direct `os.getenv` usage outside resolver/vault helpers.

### M3 — Milvus Migration (target: Feb 2026)
- Add Milvus client in `services/common` with health/metrics parity.
- Update Memory Gateway to prefer Milvus with Redis fallback; keep in-memory fallback for dev.
- Replace Qdrant-specific config/envs with Milvus equivalents; update Helm values and compose.
- Data migration plan: export Qdrant collections, import into Milvus, validate embeddings.

### M4 — Observability & Reliability (target: Mar 2026)
- Ensure OTEL/Prometheus wiring is consistent (gateway/orchestrator/identity/memory/policy/analytics).
- Add synthetic checks for Milvus/Kafka/Vault readiness to `/healthz` across services.
- Harden chaos scripts for Milvus and Vault outages.

### M5 — Governance & Release (target: Apr 2026)
- Final ISO-style SRS sign-off (see `docs/SRS_ISO.md`).
- Release playbooks and rollback for Milvus/Vault changes.
- Performance benchmarks for memory latency and policy throughput.

## Tracking & Reporting
- Roadmap owner: Architecture team.
- Updates are made here first; other docs should reference this file instead of duplicating timelines.
- Each milestone requires: design note, implementation PRs, migration runbook, verification checklist.
