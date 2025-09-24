# SomaStack Implementation Roadmap

This plan translates the master roadmap into actionable, parallel workstreams. It assumes SomaStack = SomaGent + SomaBrain + SomaFractalMemory + supporting infra (Kafka/KRaft, Postgres, Redis, Quadrant, Prometheus/Grafana).

## Guiding Principles
- **Math-first**: measure everything (latency, tokens, WER/MOS, recall precision) and adjust via benchmarks/telemetry.
- **Simplicity**: prefer clear interfaces, idempotent APIs, well-scoped services.
- **Observability**: every feature ships with metrics, traces, and audit trails.
- **Parallelism**: decompose work into independent tracks so multiple contributors can move concurrently.

## Workstreams Overview
1. **Core Memory & Constitution** – wiring SomaBrain + SomaFractalMemory, constitution validation, sync safety.
2. **SLM Execution** – async workers, HTTP fallback, provider scoring, benchmarks.
3. **Agent Orchestration & Policy** – gateway, orchestrator, MAO, policy enforcement.
4. **Settings, Identity, Notifications** – tenant management, deployment modes, notification orchestrator.
5. **UI/Experience** – admin console, conversational workspace, Agent One Sight dashboard.
6. **Infrastructure & Ops** – Kafka/Postgres/Redis/Quadrant setup, CI/CD, observability.

Each workstream below lists milestones, dependencies, and parallelizable subtasks.

---

## 1. Core Memory & Constitution
**Goal**: reliable read/write to SomaBrain, constitution enforcement, offline sync.

### 1.1 Client Libraries (Run in parallel)
- Implement `somagent_memory` client (Python) to wrap `/remember`, `/recall`, `/rag/retrieve`, `/wm/*`, `/link` with tenant headers, retries, idempotent IDs.
- Implement constitution client hitting `/constitution/version|load|validate|checksum` with Redis caching.

### 1.2 Service Integration
- Wire Memory Gateway to SomaBrain client (read/write, offline buffer via Redis streams).
- Constitution service: signature verification, checksum publishing (`constitution.updated` Kafka event).

### 1.3 Sync & Resilience
- Implement transactional outbox pattern for memory writes (Postgres table + background dispatcher to SomaBrain).
- Background reconciler draining offline buffer after outages; emit metrics (backlog age, replay rate).

### 1.4 Testing & Benchmarks
- Memory regression capsule: insert set of docs, recall with cues, assert ranking & latency thresholds.
- Constitution integration test: load > validate > orchestrator hits `/v1/sessions/start` and blocks on invalid hash.

**Dependencies**: SomaBrain running (9696); Redis, Kafka, Postgres available.

---

## 2. SLM Execution
**Goal**: hybrid async/sync inference with model scoring + telemetry.

### 2.1 HTTP Fallback Routes
- Implement `/infer_sync` and `/embedding` handlers in `services/slm-service`, aligning with OpenAPI.
- Add provider adapters (OpenAI, Anthropic, Llama local) with token/latency logging.

### 2.2 Async Workers
- Define request queue schema (Kafka topic `slm.requests`, dead-letter queue).
- Worker service consuming requests, calling providers, streaming responses to orchestrator.

### 2.3 Metrics & Benchmark Harness
- Emit `slm.metrics` events containing tokens, latency, refusal rate.
- Temporal workflow to run nightly benchmark capsules; store results in Postgres + SomaBrain.
- Notification orchestrator: Kafka consumer + websocket (`/ws/notifications/{tenant}`) broadcasting alerts.
- MAO service uses Postgres tables + worker to execute workflows via orchestrator `/v1/sessions/start`.
- Benchmark service (FastAPI) hitting SLM HTTP fallback, persisting results in Postgres (`benchmark_results`), exposing `/v1/run` and `/v1/scores` for scoring service.

### 2.4 Model Profiles & Scoring
- Extend settings service with `model_profiles` table & API (chat/planning/code/embedding/voice).
- Scoring service implementing `score(model, task)`; auto-suggest promotions.

**Parallel tasks**: adapters independent from queue plumbing; benchmarks can start once sync endpoints exist.

---

## 3. Agent Orchestration & Policy
**Goal**: enforce constitution, manage sessions, integrate MAO.

### 3.1 Gateway & Orchestrator Foundation
- Implement JWT/capability middleware, request context (tenant, user, deployment mode).
- `POST /v1/sessions/start` orchestrator flow: policy check → memory call → SLM request.
- Integrate two-key approval logic (policy + human) hooking into notification system.

### 3.2 Policy Engine
- Implement scoring weights, connection to constitution service.
- Expose `/v1/evaluate` returning score + reason codes; orchestrator attaches to tool actions.

### 3.3 Multi-Agent Orchestrator (Temporal)
- Define workflow schema for capsules (plan → tasks → approvals).
- Add connectors to notification orchestrator for wait states.

### 3.4 Offline Sync
- Ensure request context includes `client_type` so local/offline devices queue operations properly.
- Document outbox replay API for clients (UI/CLI/IDE).

**Dependencies**: Memory Gateway (for recall), SLM fallback (for quick responses).

---

## 4. Settings, Identity, Notifications
**Goal**: configurable multi-tenant controls, deployment modes, notification feeds.

### 4.1 Identity Service
- Build user/tenant models, capability claims, training lock flow (`/v1/training/start|stop`).
- Integrate with JWT signing (initial simple secret → move to JWKS later).

### 4.2 Settings Service
- CRUD for tenant settings, model profiles, notification preferences (`notification_preferences` table).
- Emit `settings.changed` Kafka events; provide version hashes.

### 4.3 Notification Orchestrator
- Service listening to `notifications.events`; pushes WebSocket updates, optional email/SMS connectors.
- Implement quiet hours, severity filters.

### 4.4 Deployment Mode Automation
- Settings endpoints to switch `SOMAGENT_DEPLOYMENT_MODE`, enforce guardrails per mode (mock providers in dev, strict audits in prod).

**Parallel tasks**: identity and settings can proceed concurrently; notification orchestrator depends on Kafka setup.

---

## 5. UI / Experience
**Goal**: deliver admin console, conversation workspace, Agent One Sight dashboard.

### 5.1 Component Library
- Scaffold React/Vite workspace (`apps/admin-console`), set up Tailwind + Radix + Storybook.
- Build shared components (`@somagent/uix` package) for buttons, cards, notification tray, conversation timeline.

### 5.2 Admin Console Modules
- Settings forms, model profile editor, deployment mode wizard.
- Agent One Sight dashboard: LED indicators, KPI tiles, anomaly timeline, benchmark charts.

### 5.3 Conversational Workspace
- WebSockets for live conversation, persona selector, tool trace, proof-of-thought, approvals.
- Voice controls: integrate WebRTC capture, streaming waveforms, connect to SLM audio endpoints.

### 5.4 Notification Center & Marketplace
- Implement notification tray, digest preferences.
- Persona/capsule gallery + builder with YAML preview.

**Parallel tasks**: component library + storybook can proceed while backend APIs land; conversation workspace awaits gateway/orchestrator endpoints.

---

## 6. Infrastructure & Ops
**Goal**: reliable local/prod environments with observability and CI/CD.

### 6.1 Local Compose Stack
- docker-compose including Kafka/KRaft, Postgres, Redis, SomaBrain, SLM fallback, Prometheus, Grafana.
- Provide seed scripts for demo data (tenants, personas, capsules).

### 6.2 CI/CD Pipeline
- GitHub Actions: lint (Ruff, ESLint), type check (mypy, tsc), tests (pytest, Playwright), Docker builds, vulnerability scan, optional dockerhub push.

### 6.3 Observability
- Standard metrics exporters for each service; dashboards (Agent One Sight, SomaBrain internals, SLM metrics).
- Alerting rules (Kafka lag, memory backlog, refusal spikes).

### 6.4 Security Hardening
- mTLS/SPIFFE integration plan, Vault secrets loader, dependency scanning, SAST/DAST integration.

**Dependencies**: baseline service implementations to emit metrics; security work ongoing parallel to features.

---

## Timeline Sketch (rolling 12 weeks)
- **Weeks 0–2**: SomaBrain client + constitution integration, SLM fallback endpoints, gateway scaffolding, local compose stack.
- **Weeks 3–5**: Async SLM workers, policy engine, identity/settings APIs, conversation workspace (text), basic notification feed.
- **Weeks 6–8**: Benchmarks, model profiles scoring, Agent One Sight dashboard, MAO workflow v1, audio pipeline integration.
- **Weeks 9–12**: Marketplace builder, notification orchestrator enhancements, deployment mode automation, security hardening, load/chaos tests.

Adjust timeline based on team capacity; workstreams allow for parallel squads (Memory/Policy, SLM, UI/Notifications, Infra).

---

## Immediate Next Steps (Sprint 0)
1. Finalize SomaBrain client + constitution caching (Memory Gateway).
2. Implement SLM `/infer_sync` & `/embedding` with provider adapters.
3. Scaffold Gateway auth middleware + request context.
4. Build docker-compose (Kafka/KRaft, Postgres, Redis, SomaBrain) and document usage.
5. Set up Storybook + component library skeleton for admin console.

After Sprint 0, evaluate telemetry and iterate on benchmarks + orchestration flows.

## Milestones

| Milestone | Target Sprint(s) | Deliverables |
|-----------|------------------|--------------|
| Sprint 0 | Week 0 | SomaBrain client, constitution caching, SLM fallback HTTP routes, gateway context, dev Compose stack, admin console skeleton |
| Sprint 1 | Weeks 1-2 | SLM async queue, provider adapters, policy engine MVP, identity settings CRUD, Storybook components |
| Sprint 2 | Weeks 3-4 | Benchmark harness, model scoring, Agent One Sight dashboard, notification orchestrator v1 |
| Sprint 3 | Weeks 5-6 | MAO workflow, voice pipeline integration, marketplace builder alpha |
| Sprint 4 | Weeks 7-8 | Security hardening, deployment automation, load/chaos tests, documentation polish |

Adjust timelines per capacity; each milestone maps to backlog items in the main roadmap.

### Sprint 4 – Hardening & Launch
- Security hardening (mTLS/SPIFFE, Vault integration, dependency scanning).
- Deployment automation (Helm charts, CI/CD pipelines).
- Load/chaos tests across SomaStack (k6, fault injection).
- Documentation polish and legal review.
