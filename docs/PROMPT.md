# SomaStack Master Prompt

Use this prompt to regain full project context after a reset. It captures the architecture, repo structure, key services, deployment defaults, and current roadmap milestones.

---

## High-Level Vision
- **SomaStack** = SomaGent (agent orchestration) + SomaBrain (memory/RAG) + SomaFractalMemory (vector store layer) + supporting infra (Kafka/KRaft, Postgres, Redis, Quadrant, Prometheus/Grafana).
- Goal: Persona-driven AI agents with constitutional governance, observable memory, explainability, and multi-channel delivery (web, IDE, mobile, voice).

## Repository Layout
```
apps/
  admin-console/           # Vite + React + Storybook skeleton
    src/App.tsx            # Placeholder shell
    stories/               # Storybook stories
    .storybook/            # Storybook config

services/
  gateway-api/             # Entry point, context middleware
  orchestrator/            # Conversation engine (stub)
  mao/                     # Multi-Agent Orchestrator scaffold
  constitution-service/    # SomaBrain constitution proxy w/ Redis cache
  policy-engine/           # Policy evaluation service (stub)
  settings-service/        # Tenant config + model profiles (stub)
  identity-service/        # Auth/training locks (stub)
  slm-service/             # Sync fallback, provider stubs, metrics
  memory-gateway/          # SomaBrain memory proxy (remember/recall/RAG)
  tool-service/            # Tool adapters (stub)
  task-capsule-repo/       # Capsule metadata (stub)

libs/python/
  somagent_common/         # Shared logging utils
  somagent_eventbus/       # Event schemas
  somagent_somabrain/      # NEW async SomaBrain client

infra/
  docker/                  # python-service Dockerfile
  local/prometheus.yml     # Prometheus scrape config

docs/
  SomaGent_Architecture.md # Architecture blueprint (now includes SomaStack overview)
  SomaGent_Roadmap.md      # Phase roadmap
  SomaGent_SLM_Strategy.md # Model roles, scoring math, audio pipeline
  SomaGent_Security.md     # Security & moderation playbook
  design/UIX_Experience.md # UI/UX blueprint
  development/Developer_Setup.md        # Local setup + default ports
  development/Implementation_Roadmap.md # Parallel workstreams & timeline
  development/Sprint_Milestones.md      # Sprint-by-sprint deliverables
  legal/SomaGent_Default_Terms.md       # Draft terms (needs lawyer review)
  PROMPT.md                               # This file

inspiration/
  SomaAgentPrototype.tsx    # Persona-driven UI mock (React)
```

## Default Service Ports

## Deployment Modes
- `developer-light`: minimal local stack (SomaBrain stub, mocks) with training enabled by default.
- `developer-full`: full compose stack (Postgres/Redis/Kafka/SomaBrain/SLM) mirroring prod topology.
- `test`: deterministic CI profile; personas frozen, training disabled.
- `test-debug`: test + verbose telemetry, used to reproduce CI failures.
- `production`: strict budgets, full auditing, training closed by default.
- `production-debug`: temporary incident mode with debug telemetry, alerts when active.

## Standard Headers
- Tenant ID header: `X-Tenant-ID` (configurable per service); defaults to `demo`.
- User header: `X-User-ID`.
- Capabilities: `X-Capabilities` (comma separated, e.g., `training:manage,capsule:install`).
- Client type: `X-Client-Type` (web, ide, mobile, cli, bot).
- Deployment mode: `X-Deployment-Mode`.
- Request ID: `X-Request-ID` (auto-generated if missing).

## Key Environment Variables
- `SOMAGENT_DEPLOYMENT_MODE` – selects the mode above.
- `SOMAGENT_GATEWAY_ORCHESTRATOR_URL`, etc. – point services at each other.
- `SOMAGENT_MEMORY_*` – SomaBrain URL, tenant header, Redis URL, default tenant.
- `SOMAGENT_MAO_DATABASE_URL`, `SOMAGENT_MAO_ORCHESTRATOR_URL`, `SOMAGENT_MAO_KAFKA_BOOTSTRAP_SERVERS` for workflow execution.
- `SOMAGENT_CONSTITUTION_*` – SomaBrain base URL, Redis URL, cache TTL, timeout.
- `SOMAGENT_SLM_DEFAULT_PROVIDER`, `SOMAGENT_SLM_METRICS_NAMESPACE`.
- `SOMAGENT_SLM_ASR_URL`, `SOMAGENT_SLM_TTS_URL`, `SOMAGENT_SLM_VOICE_API_KEY` for the voice pipeline.
- `SOMAGENT_GATEWAY_*` – header names + defaults for context middleware.
- Provider secrets: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.

## Core External APIs
- SomaBrain: `/remember`, `/recall`, `/rag/retrieve`, `/wm/*`, `/link`, `/persona/{pid}`, `/constitution/version|validate|checksum|load`, `/metrics`.
- SLM fallback: `/v1/infer_sync`, `/v1/embedding`, `/v1/health`.
- Upcoming MAO + notification endpoints documented in respective service stubs.

| Service | Port |
|---------|------|
| SomaBrain | 9696 |
| SLM HTTP fallback | 9697 |
| Gateway API | 8080 |
| Orchestrator | 8100 |
| MAO | 8200 |
| Constitution | 8300 |
| Policy Engine | 8400 |
| Settings | 8500 |
| Identity | 8600 |
| SLM Service | 8700 |
| Memory Gateway | 8800 |
| Tool Service | 8900 |
| Task Capsule Repo | 8910 |
| Admin Console | 3000 |

## Docker Compose Stack
- `docker-compose.stack.yml` launches Kafka/KRaft (9092), Postgres (5432), Redis (6379), SomaBrain (9696), Prometheus (9090), Grafana (3000).
- Prometheus scrapes SomaBrain + placeholders for core services; Grafana login admin/admin.

## Key Integrations
- **SomaBrain client** (`somagent_somabrain`) handles `/remember`, `/recall`, `/rag/retrieve`, `/link`, `/persona`, `/constitution/*` with tenant headers, async httpx.
- **Memory Gateway** proxies SomaBrain; uses Redis for offline buffering (future) and accepts `default_tenant_id` fallback.
- **Constitution Service** caches `/constitution/version` via Redis, proxies `/validate` and `/checksum` with error handling.
- **SLM Service** exposes `/v1/infer_sync`, `/v1/embedding`, `/v1/health`, pluggable provider registry (`StubProvider` default), Prometheus metrics for requests/latency.
- **Gateway API** now has ContextMiddleware extracting tenant/user/capabilities/client-type/deployment-mode from headers; per-request context accessible via dependency.

## Documentation Highlights
- Architecture doc: describes SomaStack layers, data flow, infra requirements, deployment modes.
- SLM Strategy: role-based models (dialogue, planning, code, embeddings, speech recognition/synthesis), scoring formula, audio vector modeling, pipeline steps, benchmark methodology.
- UI/UX blueprint: conversational UI, Admin console, Agent One Sight dashboard, notification system, marketplace, responsive/theming, analytics.
- Security playbook: identity, moderation, strike tracking, tool sandboxing, observability, governance workflows, testing, compliance.
- Implementation roadmap: workstreams (memory, SLM, orchestration, settings/identity, UI, infra) with phased tasks and timeline.
- Sprint milestones: Sprint 0 done, Sprints 1–4 planned with focus areas.
- Developer Setup: prerequisites, ports, compose usage, env vars, troubleshooting.

## Current State (Sprint 0 Complete)
- SomaBrain client ready; constitution caching integrated.
- SLM fallback HTTP endpoints implemented with stub provider + metrics.
- Gateway context middleware + dependency in place.
- Development compose stack available; admin console skeleton ready with Vite + Storybook.

## Next Milestone (Sprint 1)
- Async SLM queue + provider adapters.
- Policy engine MVP.
- Identity/settings CRUD APIs.
- Storybook component groundwork.

Use this prompt to reload context, restore priorities, and continue execution without re-reading every doc.

## Next Milestones
- Sprint 3 completed: MAO workflows, voice pipeline, marketplace builder alpha.
- Sprint 4 focuses on security hardening, deployment automation, load/chaos tests, docs polish.

## Deployment Automation
- Helm/Terraform automation to deploy services with cert-secret mounts, config maps, autoscaling.
- GitHub Actions pipeline: lint, tests, build, security scans, docker/helm publish.
- Load/chaos tests (k6 stress tests, planned chaos scenarios).
