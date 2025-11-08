# SomaAgentHub Architecture Overview

## Purpose
This document captures the current architectural state, pain points, and the Phase 1 evolution plan to simplify the system while preserving capability and enabling rapid future growth.

## Current Service Topology
- gateway-api: Front door / user-facing orchestration entrypoints
- orchestrator: Temporal workflows (session, MAO, capsule)
- pricing-service: Live pricing ingestion + budget evaluation
- memory-gateway: KV & vector memory / retrieval
- tool-service: External tool adapters
- identity-service: Token issuance + training lock + OIDC discovery
- billing-service: Payment intent + usage summary
- analytics-service: Benchmark & capsule run telemetry aggregation
- policy-engine: Evaluation harness + OPA integration
- slm-service: Model/adapter layer for language operations
- mao-service: Multi-agent orchestration helpers
- capsule-service: Persona/capsule synthesis utilities
- self-provisioning: Terraform + K8s environment bootstrap (future automation)

Common utilities under `services/common`: observability, Redis/Qdrant/OpenAI clients, OPA client, audit logging, etc.

## Key Architectural Pain Points
1. Fragmented configuration across services (duplicate env parsing).
2. Inconsistent app bootstrap (logging, tracing, metrics differ).
3. Dynamic/late imports (`noqa: E402`) to dodge circular dependencies.
4. Lack of formal interfaces (e.g., tool adapters, repository layer).
5. Domain leakage: persistence models returned directly by HTTP handlers.
6. Loose contracts between pricing ↔ gateway ↔ orchestrator (dict-shaped responses).
7. Observability fragmentation: correlation IDs and structured logging not unified.
8. Event-driven patterns (Kafka/Temporal signals) underutilized; synchronous coupling.
9. Testing path shims add cognitive overhead.
10. Mixed dataclasses, pydantic models, ad-hoc DTO conversions.

## Guiding Principles for Evolution
- Single source of truth for settings + bootstrap.
- Strong, typed contracts at service boundaries.
- Protocol-driven abstractions (adapters, repositories, policy client).
- Event-first integration where latency tolerance exists.
- Observability uniformity (tracing + metrics + structured logs).
- Incremental strict typing (MyPy) starting with common contracts.
- Dependency injection over dynamic imports.

## Phase 1 Goals (Foundations)
1. Shared settings base (pydantic Settings) reusable by all services.
2. Unified FastAPI bootstrap helper (logging, tracing, metrics init).
3. Typed contract models for pricing decisions & build precheck.
4. Architecture documentation (this file) + roadmap clarity.
5. Begin tightening MyPy configuration (select modules strict).

## Implementation Plan (Phase 1)
- `services/common/config/base_settings.py`: Define `BaseServiceSettings`.
- Service-specific settings classes extend base and are loaded via `load_settings(service)`.
- `services/common/fastapi/bootstrap.py`: `create_app(service_name, settings, routes_factory, instrumentation=True)`.
- Refactor one pilot service (`pricing-service`) to use bootstrap.
- Add contract models under `services/common/contracts/pricing.py`.
- Update MyPy config: remove broad `ignore_missing_imports` for internal packages; enable `disallow_incomplete_defs` & `warn_unused_configs` for contracts modules.

## Future Phases (Summary)
See full roadmap in `docs/roadmap-somagenthub.md` for detailed scope.

Phase 2 (Interfaces & DI): Adapter Protocol, repository Protocols, PolicyClient abstraction.
Phase 3 (Events & Workflow): Domain events + outbox + async coupling.
Phase 4 (Observability & Guardrails): Structured logging + SLOs + cost + moderation.
Phase 5 (Full Strictness & Docs): MyPy strict expansion; CI gating; developer handbook.
Phase 6 (Data & Analytics): Query abstraction, performance trends, forecasting.
Phase 7 (Security & Compliance): Vault workflows, SPIFFE enforcement, RBAC formalization.

## Metrics of Success
- Reduced bootstrap duplication (LOC comparison pre/post).
- MyPy error count stable or decreasing as strictness increases.
- Elimination of new `noqa E402` occurrences after DI refactor.
- Faster onboarding: single documented bootstrap & settings path.
- Clear evolution path for adding new services (copy minimal template).

## Next Actions
Proceed with creating shared settings & bootstrap modules and refactor `pricing-service` as an exemplar.

---
*Last updated: 2025-11-08*
