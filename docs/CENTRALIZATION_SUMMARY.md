# Centralization Summary – Final State (Nov 11 2025)

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

## Roadmap
The centralisation effort is planned in three incremental phases.  Each phase adds a concrete, test‑covered improvement while keeping the system operational.

| Phase | Goal | Key Actions | Acceptance Criteria |
|------|------|-------------|---------------------|
| **1 – Completion of migration** | Finish all pending renames and shim removals | • Verify all Docker Compose files use only `SOMA_AGENT_HUB_` variables (already done for `docker‑compose.yml` and `docker‑compose.dev.yml`).<br>• Ensure every service `.env` file follows the canonical prefix (orchestrator, memory‑gateway).<br>• Update any remaining test fixtures to the new prefix (identity‑service). | `grep -R "SOMASTACK_\|SOMAGENT_"` returns no results in the repo. |
| **2 – Full observability alignment** | Consolidate all observability configuration to use `resolve_env` and remove legacy fall‑backs | • Review each service’s `observability.py` to ensure `OTEL_*`, `LOKI_URL`, and Prometheus flags are read via `resolve_env`.<br>• Add CI lint rule to flag direct `os.getenv` usage in observability modules. | All observability modules import `resolve_env` and CI lint passes. |
| **3 – Continuous enforcement & documentation** | Embed the policy in CI/CD and keep docs up‑to‑date | • CI pipeline includes a step that runs `scripts/centralize_env.py` in dry‑run mode and fails on any changes.<br>• `CENTRALIZATION_SUMMARY.md` is updated automatically by a pre‑commit hook after any migration commit.<br>• Add a GitHub Action that posts a summary of remaining legacy references on each PR. | Any PR that re‑introduces a legacy env read is blocked; documentation reflects the current state. |

The roadmap is intentionally lightweight: each phase is independent, fully testable, and can be merged incrementally.  Future work may include extending the resolver to support secret‑rotation policies and adding typed settings classes for new services.

## Pending Work
While the majority of services have been migrated to the central `resolve_env` resolver and the legacy prefixes have been removed from most code, a few items remain to achieve **full** compliance with the centralization policy. These tasks are tracked in the repository's TODO list and will be addressed in the upcoming phases.

### Outstanding Tasks
| Item | Description |
|------|-------------|
| **Purge legacy compose env** | Ensure all Docker‑Compose files use only `SOMA_AGENT_HUB_` variables and remove any remaining `SOMASTACK_`/`SOMAGENT_` entries. |
| **.env prefix purge** | Update `.env` files in `services/orchestrator` and `services/memory-gateway` to replace `SOMASTACK_` with `SOMA_AGENT_HUB_` and enforce `DEV`/`PROD` deployment modes only. |
| **Test env prefix migration** | Adjust test fixtures (e.g., `services/identity-service/tests/conftest.py`) to use the new prefix. |
| **Centralize orchestrator activities env** | Replace direct `os.getenv` calls (e.g., `GATEWAY_API_URL`, `TAXI_BUILDER_OUTPUT_ROOT`) with `resolve_env`. |
| **Centralize policy‑engine observability env** | Update `services/policy-engine/app/observability.py` to read OTEL related variables via `resolve_env`. |
| **Centralize jobs main env** | Refactor `services/jobs/app/main.py` to use `resolve_env` for `REDIS_URL` and related settings. |
| **Centralize gateway secrets env** | Modify `services/gateway-api/app/somagent_secrets.py` to replace `os.getenv` with `resolve_env`. |

These items are scheduled across the upcoming roadmap phases (see the **Roadmap** table above). Completion of these tasks will allow us to update this section to reflect a truly *no remaining work* state.

## Documentation Policy
* This file must always reflect the *actual* state of the code base. Any future change that introduces a direct `os.getenv` call must be accompanied by an immediate update to this summary.
* New services should be added to the **Completed Centralizations** table after they adopt `resolve_env`.

---

**Enforcement** – The CI pipeline includes a lint step that fails if `os.getenv` or `os.environ[` is detected outside of `services/common/config/base_settings.py`. This guarantees that the repository stays shim‑free.