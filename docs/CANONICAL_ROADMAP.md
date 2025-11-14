# Canonical Roadmap Map – Final State (Nov 11 2025)

## Core Policy
* **Environment‑variable prefix** – **only** `SOMA_AGENT_HUB_`. No fall‑backs to `SOMAGENT_` or `SOMASTACK_` are allowed.
* **Resolver** – `services/common/config/base_settings.py::resolve_env(name, default)` is the *sole* entry point for reading configuration values.
* **Deployment modes** – Exactly two: `DEV` and `PROD`. The code base contains no other mode switches, feature‑flags, or shim layers.
* **Secrets** – All secret access goes through `services/common/vault_client.py`. In `DEV` the client falls back to plain environment variables; in `PROD` it talks to Vault. No manual `os.getenv` calls for secrets remain.

## Completed Centralizations (no mocks, no bypasses)
The following services now **exclusively** use `resolve_env` (or the Vault client for secrets) and have had every legacy shim removed:
| Service | Files Updated |
|---------|----------------|
| **Gateway API** | `app/core/config.py`, `app/observability.py`, `app/somagent_secrets.py` |
| **LLM Hub** | `app/config.py` |
| **Memory Gateway** | `app/config.py`, `app/vector_store.py` |
| **Policy Engine** | `app/config.py`, `app/observability.py`, `app/redis_client.py`, `app/policy_rules.py` |
| **Jobs Service** | `app/main.py` |
| **Constitution Service** | `app/core/config.py` |
| **Common Clients** | Redis, Kafka, MinIO, Qdrant, OPA, OpenAI – all now import `resolve_env` directly |
| **Observability Modules** | All services (`gateway-api`, `identity-service`, `orchestrator`, `policy-engine`, `analytics-service`, etc.) use `resolve_env` for OTEL/LOKI/Prometheus flags |

All previous `try/except` shims, lambda fall‑backs, and duplicated `os.getenv` calls have been removed. The code compiles and the test suite passes.

## Verification
* `docker compose config` runs cleanly in both `DEV` and `PROD` modes.
* Full repository scan shows **zero** occurrences of `os.getenv(` or `os.environ[` outside of the Vault client and the resolver implementation.
* All unit and integration tests execute without skipping due to deprecated modules.

## No Remaining Work
All services under `services/` now conform to the centralization policy. No legacy environment‑variable prefixes, no mock resolvers, and no shim code remain.

## Documentation Policy
* This file must always reflect the *actual* state of the code base. Any future change that introduces a direct `os.getenv` call must be accompanied by an immediate update to this summary.
* New services should be added to the **Completed Centralizations** table after they adopt `resolve_env`.

---

**Enforcement** – The CI pipeline includes a lint step that fails if `os.getenv` or `os.environ[` is detected outside of `services/common/config/base_settings.py`. This guarantees that the repository stays shim‑free.
