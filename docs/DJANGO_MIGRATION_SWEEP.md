# Django Migration Sweep — Violations and Remediation Backlog

**Document ID:** SAH-DJANGO-SWEEP-2025-12-22
**Version:** 0.1 (working draft)
**Date:** 2025-12-22
**Owner:** Assistant (dev + QA + security + performance + UX)

---

## 1. Critical Violations (must fix first)

- **No Django project present** — entire stack is FastAPI-based; no Ninja/Channels scaffold exists.
  - Impact: Blocks any Django-only policy; no `/api/v2` surface.
- **Gateway FastAPI surface** — `services/gateway-api/app/api/routes.py`, `capsules.py`, `dashboard.py`, `app/main.py`, `region_router.py`, middleware/auth/context.
  - Action: Recreate in Django/Ninja (`/api/v2`), add Channels, maintain auth/context, OPA checks.
- **Orchestrator FastAPI surface** — `services/orchestrator/app/api/*.py`, `router.py`, tenants router, planner, registry, conversation, training, memory, capsules, roles, tasks, tools, evaluations, RL, HITL, roles, health.
  - Action: Port control-plane endpoints to Django apps; keep Temporal worker in-process but driven by Django configs; preserve outbox publishing.
- **Identity-service FastAPI** — `services/identity-service/app/main.py`, `app/api/routes.py`, `app/core/*`.
  - Action: Django auth app for JWT issuance/validation; reuse storage/audit logic.
- **Policy-engine FastAPI** — `services/policy-engine/app/main.py`, `app/api/routes.py`, `app/policy_app.py`.
  - Action: Django policy app delegating to OPA; fail-closed middleware.
- **Other FastAPI services** — memory-gateway, notification-service, tool-service, settings-service, analytics-service, pricing-service, llm-hub, model-proxy, constitution-service, mao-engine, billing-service, marketplace, task_capsule_repo.
  - Action: Evaluate which become Django apps vs. pure workers; all control-plane APIs must be Ninja.
- **Vector store drift** — Qdrant still referenced in Helm (`k8s/helm/soma-agent/templates/qdrant*.yaml`) and values; Milvus is required.
  - Action: Remove Qdrant templates/values; wire Milvus endpoints consistently.
- **Message catalog missing** — no `admin.common.messages` or `get_message` usage in repo.
  - Action: Introduce centralized message catalog; refactor user-facing strings.
- **UI framework drift** — React/Alpine present (`services/static-templates/react`, Alpine mentions).
  - Action: New UI work must be Lit; migrate touched components.

---

## 2. High-Priority Remediation Tasks

1. Create Django 5 project with Ninja + Channels skeleton; add Postgres settings, Redis cache, Kafka client, Milvus client, Vault/OPA config.
2. Implement `/api/v2` Gateway equivalents (status, aggregate-status, agents/crews/workflows/HITL/capsules, health/metrics) with OPA + RBAC gates.
3. Implement `/api/v2` Orchestrator control-plane (projects/registry/planner/conversation/training/memory/capsules/tasks/tools/evaluations/RL/HITL/roles/tenants/health) backed by Django ORM + Temporal client + outbox.
4. Port Identity and Policy surfaces into Django apps (JWT, keys, policy eval) with fail-closed behavior.
5. Replace Qdrant with Milvus in code/config/Helm; ensure `services/common/milvus_client.py` is the single vector adapter.
6. Add message catalog module and refactor user-facing strings to `get_message(...)`.
7. Stand up Lit UI shell consuming Channels/SSE for realtime updates (workflows, HITL, A2A, analytics).

---

## 3. Inventory by Service (evidence)

- `services/gateway-api/` — FastAPI routers, middleware, auth, otel, redis, context. No Django code.
- `services/orchestrator/app/api/` — FastAPI routers; Temporal worker code lives separately. Uses `services/common/contracts`, outbox, Kafka, Prom.
- `services/identity-service/app/` — FastAPI API + core storage/audit.
- `services/policy-engine/app/` — FastAPI policy evaluator wrapping OPA.
- `services/memory-gateway/app/` — FastAPI memory endpoints; embeddings/vector_store with Qdrant pathing; no Django.
- `services/tool-service/app/` — FastAPI routes, adapters; no Django.
- `services/settings-service/app/` — FastAPI routes; no Django.
- `services/notification-service/app/` — FastAPI routes; no Django.
- `services/analytics-service/app/` — FastAPI routes; no Django.
- `services/pricing-service/app/` — FastAPI routes/providers; no Django.
- `services/llm-hub/app/` — FastAPI routes; no Django.
- `services/model-proxy/app.py` — FastAPI.
- `k8s/helm/soma-agent/templates/qdrant*.yaml` — Qdrant deployment present.
- `services/common/openai_provider.py` — legacy OpenAI provider; assess deprecation per migration.

---

## 4. Required New Components

- Django project root (manage.py, settings, urls, asgi/wsgi, Channels).
- Django apps: gateway, authn_authz, orchestration, memory, catalog (tools/LLMs/models), settings_flags, collaboration, audit_analytics.
- Message catalog (`admin/common/messages.py`) + helper `get_message`.
- Milvus adapter integrated into Django settings; Kafka/Flink connectors; Temporal client bindings.
- Channels routing for WS/SSE streams; OTEL/Prometheus instrumentation.

---

## 5. Open Questions / Blockers

- gpubroker and voyant repos are not present in workspace; integration points and APIs cannot be validated yet.
- Decision on single Django project vs. multiple Django services (default assumed: single control-plane with modular apps).
- Data migration strategy from existing Postgres schemas (SQLAlchemy) to Django ORM needs schema mapping and migration scripts.

---

## 6. Next Steps (execution-ready)

- Stand up Django skeleton with Ninja/Channels and shared settings (Postgres/Redis/Kafka/Milvus/Vault/OPA).
- Draft parity contracts for Gateway `/api/v2` and Orchestrator `/api/v2`; generate OpenAPI spec.
- Begin refactor of gateway/orchestrator handlers into Django views using existing business logic where possible.
- Remove Qdrant templates and wire Milvus in Helm/compose; update config defaults.
- Add message catalog and refactor first set of endpoints to use `get_message`.
