# Centralization Status — Truthful Report (Nov 11, 2025)

This document reflects the current, verified state of configuration centralization across SomaAgentHub. Claims below are based on code present in the repository, not projections.

## Canonical Approach
- Prefix: `SOMA_AGENT_HUB_` with fallbacks to `SOMAGENT_`, `SOMASTACK_`, then raw name.
- Resolver: `services/common/config/base_settings.py: resolve_env(name, default)` is the only approved way to read env values.
- Modes: Exactly two — `DEV` and `PROD`. DEV mirrors PROD code paths; only data sources differ (local/env vs. real services).
- Secrets: `services/common/vault_client.py` provides real Vault in PROD and env/in‑memory fallbacks in DEV without changing call sites.

## Completed Migrations
- Gateway API: `services/gateway-api/app/core/config.py` uses `resolve_env` and Vault fallback for `JWT_SECRET`.
- LLM Hub: `services/llm-hub/app/config.py` uses `resolve_env` and Vault fallback for API keys.
- Memory Gateway: `services/memory-gateway/app/config.py` now centralized; Qdrant key via env → Vault fallback.
- Policy Engine: `services/policy-engine/app/config.py` centralized; OPA and cache flags via `resolve_env`.
- Common Providers/Clients:
  - OpenAI provider and OPA client use `resolve_env`.
  - Vault client enforces DEV/PROD parity and uses resolver for settings.
  - NEW: Redis, Kafka, MinIO, and Qdrant common clients now read config via `resolve_env`.

## Removed/Deprecated (Do not use)
The following modules are deprecated and intentionally raise on import:
- `services/common/config/unified_settings.py`
- `services/common/registry/service_registry.py`
- `services/common/deployment/deployment_strategy.py`
- `services/common/secrets/vault_manager.py`
- `services/common/session/session_manager.py`
- `scripts/migration/migrate_service.py` — replaced with a RuntimeError and guidance.

## What’s Pending
- Services pending full migration to `resolve_env` patterns: orchestrator, pricing-service, identity-service, settings-service, and others under `services/*` not listed above.
- Many direct `os.getenv` usages remain in service code (e.g., Temporal workers, observability, dashboards). These need systematic replacement with `resolve_env` plus consistent defaults.
- Compose/Helm values: should prefer `SOMA_AGENT_HUB_*` vars; legacy fallbacks remain temporarily.

## Verification Snapshot
- Docker compose config check under DEV: OK (ran `docker compose config --quiet`).
- Tests referencing deprecated modules are marked skipped to avoid misleading results.
- Repository sweep confirms remaining direct `os.getenv` usage across multiple services; migration in progress.

## Migration Checklist (Active)
- Common clients: use `resolve_env` (Redis, Kafka, MinIO, Qdrant) — DONE.
- Orchestrator and workers: centralize Temporal, Redis, URLs, and observability envs — TODO.
- Observability: standardize OTEL/LOKI/PROM flags via resolver across services — TODO.
- Compose/Helm: set first-class `SOMA_AGENT_HUB_*` envs; keep fallbacks during transition — TODO.
- Docs: keep this summary aligned with real code; avoid aspirational claims — ONGOING.

## Policy
- Only two modes (DEV, PROD). No additional environments or strategies.
- No new abstraction layers unless strictly necessary; prefer small, surgical refactors.
- Truth over templates: documentation must reflect the repository’s current state.

If you find a module reading envs directly with `os.getenv`, replace with `resolve_env` and preserve existing defaults. For secrets, follow env‑first, Vault‑second pattern used in Gateway/LLM Hub.