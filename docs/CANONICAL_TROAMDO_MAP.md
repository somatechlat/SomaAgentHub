# Canonical Troamdo Map – Current State (Nov 11 2025)

This document captures the **canonical roadmap** for the centralization effort, including all pending and completed items.

## Completed Items
- Remove legacy imports memory-gateway
- Refactor policy-engine config
- Deprecate migration script
- Roadmap + verification report
- Sweep raw os.getenv usages
- Plan Phase1 client patches
- Refactor redis client env
- Refactor kafka client env
- Refactor minio client env
- Refactor qdrant client env
- Refactor temporal worker env
- Refactor observability env
- Update CENTRALIZATION_SUMMARY doc
- Gateway observability resolver
- Identity observability resolver
- Remove shim in gateway config
- Remove shims gateway observability
- Remove shims orchestrator observability
- Canonicalize dashboard env
- Canonicalize wizard engine env
- Remove OPA shim fallback

## Pending Items
- Purge legacy compose env
- .env prefix purge (replace SOMASTACK_ with SOMA_AGENT_HUB_)
- Test env prefix migration (identity-service tests)
- Centralize orchestrator activities env
- Centralize policy-engine observability env
- Centralize jobs main env
- Centralize gateway secrets env

## Next Sprint (Parallel Mode)
1. **Delete backup/shim files** – remove all `*.backup` and legacy wrapper files.
2. **Replace `os.getenv` / `os.environ` calls** – use `services.common.config.base_settings.resolve_env` across all services.
3. **Update imports** – point to `services.common.config.settings` singleton.
4. **Adjust Docker Compose** – ensure only `SOMA_AGENT_HUB_` variables are referenced.
5. **Run verification** – lint step to ensure zero stray `os.getenv` usages.

The roadmap will be kept in sync with the todo list in the repository.
