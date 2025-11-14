# Centralization Summary – Final State (Nov 11 2025)

## Core Rules
* **Prefix:** Every runtime environment variable is read through `services/common/config/base_settings.py::resolve_env(name, default)` which prepends `SOMA_AGENT_HUB_`. No other prefixes (`SOMAGENT_*`, `SOMASTACK_*`, etc.) are permitted in services/**.
* **Modes:** Deployment mode is strictly `DEV` or `PROD`; `BaseServiceSettings` shares this contract and drives observability toggles.
* **Secrets:** All secret IO happens via `services/common/vault_client.py`. DEV falls back to env/in‑memory stores derived from `SOMA_AGENT_HUB_<PATH>_…`, and PROD relies on Vault (k8s/SPIFFE auth paths).
* **Enforcement:** `scripts/centralize_env.py` and the CI lint rule raise errors when raw `os.getenv`/`os.environ[` appear outside the resolver/vault. `ruff` enforces import hygiene and unused symbols; test-suite prints are allowed via `pyproject.toml` per-file ignore rules.

## Completed Centralizations
| Service | Key files using `resolve_env` only | Notes |
| --- | --- | --- |
| **Gateway API** | `app/core/config.py`, `app/somagent_secrets.py`, `app/observability.py` | JWT secrets, external URLs, OTEL flags all resolved centrally.
| **LLM Hub** | `app/config.py` | Model/vector store endpoints read through the resolver.
| **Memory Gateway** | `app/config.py`, `app/vector_store.py` | Redis, MinIO/Kafka, and Ray settings resolve via the shared helper.
| **Policy Engine** | `app/config.py`, `app/observability.py`, `app/redis_client.py`, `app/policy_rules.py`, tests under `services/policy-engine/tests/` | OTEL/LOKI flags now centralized; integration tests set `SOMA_AGENT_HUB_` prefixed envs.
| **Jobs Service** | `app/main.py` | `REDIS_URL` resolved via `resolve_env`.
| **Constitution Service** | `app/core/config.py` | All service URLs and signing paths use the resolver.
| **Gateway Secrets Loader** | `app/somagent_secrets.py` | Strictly raises when required secrets are missing.
| **Common clients** | Redis/Kafka/MinIO/Qdrant/OPA/OpenAI clients import `resolve_env` directly (see `services/common/*`).
| **Observability modules** | `services/*/app/observability.py` | `ENABLE_OTLP`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_INSECURE` read through the resolver across services.

## Standardized Flags (used today)
* `SOMA_AGENT_HUB_REDIS_URL`, `SOMA_AGENT_HUB_DATABASE_URL`, `SOMA_AGENT_HUB_KAFKA_BOOTSTRAP_SERVERS`, `SOMA_AGENT_HUB_VAULT_ADDR`, etc.
* Service-specific URLs such as `SOMA_AGENT_HUB_GATEWAY_ORCHESTRATOR_URL`, `SOMA_AGENT_HUB_POLICY_ENGINE_URL`, `SOMA_AGENT_HUB_LLM_HUB_URL`.
* Observability toggles: `SOMA_AGENT_HUB_ENABLE_OTLP`, `SOMA_AGENT_HUB_OTEL_EXPORTER_OTLP_ENDPOINT`, `SOMA_AGENT_HUB_OTEL_INSECURE`, `SOMA_AGENT_HUB_ENABLE_PROMETHEUS`.
* Secret path tokens follow the prefix plus path tokens derived from the vault - see `vault_client._dev_mode`.

## Active Enforcement & Tooling
* **Black/ruff:** `black` is run on affected files, and `ruff check`/`ruff format` cover `services/` and `tests/` to keep import blocks and unused identifiers clean. Targeted `ruff check services/policy-engine/tests/test_integration_flow.py tests/test_unified_config.py services/analytics-service/app/api/routes.py` currently passes after the adjustments documented here.
* **Scripts:** `scripts/centralize_env.py` now accepts `--dry-run`, `--include`, `--exclude`, and `--root` flags (the default scope is `services`). Run it as `scripts/centralize_env.py --dry-run --include services --exclude "**/tests/**"` before committing so CI is guaranteed to find stray `os.getenv` uses as soon as they appear.
* **Tests:** `pytest -q tests/test_unified_config.py` passes (some warnings about legacy `return bool` tests persist). Integration tests now set `SOMA_AGENT_HUB_` envs before spinning up containers.

## Roadmap (next steps)
1. **Document canonical flags per service** in this file and/or README sections for each stack (Gateway, Policy, Orchestrator, etc.).
2. **Sweep `.env`/compose**: all compose files already declare `SOMA_AGENT_HUB_` vars; keep new variables aligned when adding services and service tokens.
3. **CI hooks:** continue running `scripts/centralize_env.py --dry-run --include services` and `ruff format` on `services/ tests/` via `Makefile` targets.
4. **Secret additions:** when adding new secrets, encode them as `SOMA_AGENT_HUB_<PATH>_<KEY>` and read through `vault_client`. Document the expected vault path (e.g., `database/postgres` → `SOMA_AGENT_HUB_DATABASE_POSTGRES_PASSWORD`).
5. **Completion checklist:** once every service uses `resolve_env` (checked via `rg -n "os\.getenv" services`), update this table and remove the migration warnings from `docs/ROAMDPs`.

## Summary
The `services/` hierarchy now has one resolver, one prefix, two deployment modes, and one secret path. CI enforces these rules through linting, black/ruff formatting, and the `scripts/centralize_env.py` utility. Keep this file in sync whenever the environment logic shifts.
