# SomaGent Architecture Blueprint

This document captures the canonical, end-to-end architecture for SomaGent. It expands on the Master Plan, going deep on services, data flows, orchestration patterns, and the pathway to fully autonomous project execution ("Jarvis mode").

---

## 1. System Overview

```
+------------------------+        +-------------------------+
|  Identity & Access     |        |  Operator Console       |
|  (AuthN/AuthZ, SSO)    |        |  (Admin UI, CLI)        |
+-----------+------------+        +-----------+-------------+
            |                                 |
            v                                 v
+-------------------------+        +---------------------------+
| Gateway API (FastAPI)   |<------>| Settings/Marketplace APIs |
|  - Auth middleware      |        |  - Managed configs        |
|  - Rate limits          |        |  - Persona marketplace    |
+------------+------------+        +------------+--------------+
             |                                 |
             v                                 |
+-------------------------+                    |
| Orchestrator Service    |                    |
|  - Constitution guard   |                    |
|  - Dialogue loop        |                    |
+------+------------------+                    |
       |                                       |
       v                                       v
+------+-------------------+     +-----------------------------+
| Multi-Agent Orchestrator |---->| Task Capsule Repository     |
|  (MAO)                   |     | (SomaBrain + Postgres)      |
|  - Task graphs / Temporal|     |  - Persona shots            |
|  - Scheduler             |     |  - Tool bundles             |
|  - Workspace manager     |     |  - Capsule templates        |
+------+-------------+------+     +-------------+---------------+
       |             |                       |
       |             +-----------------------+
       |                                     |
       v                                     v
+------+------+        +----------------------+       +-------------------+
| SLM Service  |        | Tool Service /      |       | Memory Gateway    |
| (Async workers)       | Integrations Hub    |       | (SomaBrain bridge)|
|  - SomaBrain /stream  |  - REST/CLI adapters|       |  - /remember      |
|  - Provider adapters   |  - Plane, VSCode,   |       |  - /rag/retrieve  |
+------------+----------+    GitHub, etc.      +-------+------------------+
             |                                  
             v
+--------------------------+
| Observability & Audit    |
|  - Kafka topics          |
|  - Prometheus/Grafana    |
|  - SIEM logs             |
+--------------------------+
```

All services are containerized, deployed on Kubernetes (or equivalent), communicating over mTLS (SPIFFE/SPIRE) with JWT capability claims. Kafka provides the event backbone; Postgres and Redis handle state; SomaBrain remains the immutable knowledge authority.

---

## 2. Core Services

### Constitution Service & Policy Propagation
- SomaBrain is the canonical, encrypted home for the constitution. Downstream services never persist it to disk; they fetch it over mTLS APIs, verify the signature in-memory, and cache only the hash/version in Redis for fast validation.
- Constitution changes require a multi-party governance capsule; once approved, a freshly signed version is stored in SomaBrain and `constitution.updated` events fan out so orchestrators and the policy engine reload the hash.
- Any service that cannot verify the signature immediately refuses requests, ensuring no action runs under an unknown or tampered constitution.

### 2.1 Identity & Access
- Supports guest sessions, OAuth/OIDC, SAML SSO.
- Issues JWTs containing tenant, user, roles (e.g., `AgentAdmin`, `Operator`, `Observer`) and capability claims (`training:manage`, `capsule:install`).
- Integrates with Secrets Manager (Vault/KMS) to supply service credentials.

### 2.2 Gateway API
- Entry point for UI/CLI/Integrations.
- Validates JWT, constitution hash, rate limits, and forwards to orchestrator or admin services.
- Logs requests to Kafka (`gateway.audit`).

### 2.3 Orchestrator Service
- Houses the conversation engine, constitution enforcement, SLM invocation routing, memory interactions.
- Each user interaction is enriched with contextual metadata (persona, tool context, capsule id).
- For single-agent tasks, orchestrator may complete the job without MAO.

### 2.4 Conversational Experience Service
- Hosts the real-time conversation surfaces: web chat, CLI, and voice channels; maintains WebSocket/Server-Sent-Events streams so responses feel immediate.
- Provides audio pipelines: integrates ASR (speech-to-text) and TTS (text-to-speech) adapters, normalizes transcripts, attaches timestamps, and forwards clean intents to the orchestrator.
- Performs feature extraction on audio streams (log-mel, MFCC, RMS energy) and writes encrypted embeddings to SomaBrain/Quadrant so downstream components can reason over vectors instead of raw waveforms.
- Applies persona tone shaping and safety filters before handing requests to the orchestrator; emits interaction-level audits (`conversation.events`).
- Notification orchestration hooks into the Web UI, pushing banner/toast updates when `notifications.events` fire; the service exposes subscription endpoints for in-app and mobile channels.
- Supports biometric/voice enrollment for enterprises, but always routes policy decisions through the orchestrator/policy engine.

### 2.5 Multi-Agent Orchestrator (MAO)
- Built on top of Temporal (recommended) for durable, observable workflows.
- Responsibilities:
  1. **Task Planning** – Converts intents into DAGs (either via SLM-based planner or predefined Capsule templates).
  2. **Resource Allocation** – Assigns personas, tool suites, and workspaces to each task node.
  3. **Scheduling** – Runs tasks sequentially or in parallel, ensuring dependencies, budgets, and policies are satisfied.
  4. **Workspace Management** – Provisions environment (VSCode dev containers, Git repos, design canvases).
  5. **Review Gates** – Pauses tasks pending approval (human or persona) when required.
  6. **Telemetry** – Streams task state to Kafka (`project.events`).

### 2.6 Task Capsules Repository
- Stored in SomaBrain (knowledge graph) with Postgres indices for quick lookup.
- Each Capsule consists of:
  - Metadata: name, version, owner, category.
  - Persona mold: references persona shot IDs.
  - Tool suite: list of tool adapters and configurations.
  - Knowledge snapshots: memory nodes to preload.
  - Guardrails: budget, policies, review requirements.
  - Lifecycle hooks: pre/post scripts, event triggers.
- Capsules can be marketplace assets or tenant-private.

### 2.7 SLM Service
- Asynchronous worker cluster using asyncio queue or Celery-style workers.
- Supports streaming results via `/slm/stream` -> orchestrator -> UI.
- Tracks token usage, latency, cost per tenant/persona.
- Exposes metrics for forecasting engine.

### 2.8 Tool Service / Integrations Hub
- Adapter framework; each adapter defines: `connect()`, `execute(action, payload)`, `health()`, `audit(event)`.
- Runs tool interactions in sandboxed containers where needed (Docker/K8s jobs) or via SaaS APIs.
- Standard connectors include: Plane.so, GitHub, VSCode.dev, Penpot, Slack, Jira, cloud providers, etc.
- Output logged to Kafka (`tool.events`) including context for post-analysis.
- Vector-heavy tools (recommendation engines, semantic search) can delegate to managed Quadrant clusters when low-latency, multi-tenant similarity search is needed without maintaining FAISS/pgvector infrastructure manually.

### 2.9 Memory Gateway
- Primary interface to SomaBrain: handles recall, remember, linking, persona CRUD.
- Also supports local dev via `/mem` sidecar on port 9596.
- Ensures constitution hash is attached to every request.
- For high-scale semantic workloads, memory recall can leverage Quadrant as a managed vector backend alongside SomaBrain’s graph—useful for cross-tenant recommendations or marketplace search.

### 2.10 Settings & Marketplace APIs
- Manage configuration data, marketplace listings, token budgets, persona installations.
- Exposed to Admin UI; uses Postgres for persistence and Vault/KMS for secrets.

### 2.11 Observability & Audit
- Kafka topics:
  - `constitution.updated`, `training.audit`, `persona.switch`
  - `agent.events`, `project.events`
  - `slm.metrics`, `tool.events`, `gateway.audit`
- Prometheus scrapes service metrics; Grafana dashboards show health, token spend, task status.
- Agent health endpoints expose readiness/latency for SomaBrain, SomaFractal Memory, Kafka, Redis, Temporal; aggregated into the Agent One Sight dashboard with LED indicators.
- Logs forwarded to SIEM (Splunk/ELK) with trace IDs.

---

## SomaStack Overview

SomaStack combines SomaGent (agent orchestration), SomaBrain (memory & reasoning), and SomaFractalMemory (long-term vector storage) into a cohesive platform supported by Kafka/KRaft, Postgres, Redis, Quadrant, Prometheus/Grafana, and Temporal/Argo.

### High-Level Flow
1. **Gateway → Orchestrator** – Client requests hit the Gateway API, the orchestrator enforces constitution/policy, and forwards memory or SLM calls.
2. **Memory Operations** – Memory Gateway interacts with SomaBrain (`/remember`, `/recall`, `/rag/retrieve`, `/link`). SomaFractalMemory preserves large-scale embeddings; background jobs keep SomaBrain and Quadrant in sync.
3. **Event Backbone** – Kafka (with KRaft consensus) transports conversation events, capsule telemetry, benchmark metrics, notifications. Services use the transactional outbox pattern for durability.
4. **State Persistence** – Postgres stores tenant settings, personas, capsules, audit logs. Redis handles short-lived caches (constitution hash, training locks, offline buffers).
5. **Model Execution** – SLM Service routes to managed/local models, logging tokens/latency; embeddings feed SomaFractalMemory/Quadrant.
6. **Observability** – Prometheus scrapes all services (`/metrics`); Grafana aggregates dashboards (Agent One Sight).

### Core Components
- **SomaGent**: Gateway, Orchestrator, Multi-Agent Orchestrator, Tool Service, Settings, Identity, Constitution, Policy, Notification Orchestrator.
- **SomaBrain**: HRR memories, persona/constitution storage, typed graph links, RAG pipeline.
- **SomaFractalMemory**: Vector store tier (Quadrant/BGE) for long-term retrieval.

### Infrastructure Requirements
| Component | Purpose | Notes |
|-----------|---------|-------|
| Kafka w/ KRaft | Event backbone | Replication ≥3, schema registry optional, external connectors via Kafka Connect. |
| Postgres | Relational store | Row-level security per tenant, backups, PITR. |
| Redis | Cache + buffer | Redis Streams for offline outbox, TTL-based back-pressure. |
| Quadrant (or self-hosted vector DB) | Vector embeddings | Hosts SomaFractalMemory embeddings, multi-region ready. |
| Prometheus & Grafana | Monitoring | Collect metrics, drive Agent One Sight LED indicators. |
| Vault/KMS | Secrets | Store tool/model credentials, rotate automatically. |
| Temporal/Argo | Workflow | Drives MAO task graphs and benchmark automation. |

### Data Residency & Isolation
- Deploy SomaBrain and Quadrant per region; propagate tenant ID and region tags through events.
- Kafka/Postgres replicate across regions (MirrorMaker 2, logical replication) with documented failover.
- Audit logs capture tenant, actor, session IDs for every action.

### Deployment Modes
- `developer-light`: minimal local stack (SomaBrain stub, SQLite/Redis, single Kafka).
- `developer-full`: docker-compose stack with Kafka/KRaft, Postgres, Redis, SomaBrain, SLM fallback.
- `production`: Kubernetes deployment with managed Kafka, Postgres, Quadrant; mTLS and zero-trust networking.

An updated architecture diagram (to store in `docs/diagrams/`) should reflect these flows.

---

## 3. Data Stores
---

## 3. Data Stores

| Store      | Purpose                                 |
|------------|-----------------------------------------|
| Postgres   | Settings, personas, capsules, audits, budgets, training sessions, API keys, tool configs. |
| Redis      | Constitution hash cache, training locks, session tokens, rate limits, short-term task states. |
| Kafka      | Event bus for orchestration, audit, streaming updates. |
| SomaBrain  | Authoritative memory graph, persona knowledge, constitution, marketplace packages. |
| Vector DB (FAISS/pgvector/Quadrant) | Hybrid recall cache for text + audio embeddings; Quadrant stores conversation vectors (log-mel/MFCC) per tenant with encryption. |
| Object storage (S3/GCS)| Large artifacts (code bundles, design exports). |

---

## 4. Task Capsule Architecture

### 4.1 Definition
- YAML/JSON schema describing persona, tools, knowledge snapshots, policies, inputs/outputs.
- Example snippet:

```yaml
capsule_id: plane_project_starter
version: 1.2.0
persona_shot: pm_plane_guru_v1
tools:
  - adapter: plane
    actions: [create_project, add_member, seed_issue]
  - adapter: notion
    actions: [create_page]
knowledge:
  - node_id: somabrain://guidelines/project-management
policies:
  budget_tokens: 5000
  requires_review: true
execution:
  steps:
    - name: Create Plane project
      action: plane.create_project
      params: {name_template: "{{project_name}}"}
    - name: Seed backlog
      action: plane.seed_issue
      params: {...}
    - name: Publish summary
      action: notion.create_page
```

### 4.2 Lifecycle
1. **Authoring** – Created via admin UI or CLI (`somagent capsules create`). Auto-validated by Policy Engine.
2. **Storage** – Saved to SomaBrain, indexed via Postgres for search.
3. **Instantiation** – MAO loads capsule, creates Temporal workflow with child activities per step.
4. **Execution** – Each step uses persona-specific SLM prompts + tool actions. Constitution enforced at each boundary.
5. **Completion** – Produces artifact bundle, updates metrics, optionally proposes capsule improvements.

### 4.3 Capsule Marketplace
- Capsules published with metadata: cost estimates, required tools, persona dependencies, compliance scores.
- Tenants can install to private libraries; installations recorded in Postgres (who, when, version).

---

## 5. Autonomous Project Execution ("Jarvis Mode")

Goal: allow an operator to say “Create the SomaBrain Mobile App according to this roadmap” and have SomaGent handle end-to-end execution.

### 5.1 End-to-End Flow
1. **Intent Capture**: Operator issues command with attachments (roadmap, requirements, repository). Identity & gateway log the request.
2. **Planning Capsule**: MAO invokes a high-level capsule (`project_bootstrap_planner`) which:
   - Reads the roadmap with SLM summarizer.
   - Decomposes into deliverables (Backend API, Mobile UI, QA suite, Documentation).
   - Estimates token budgets per deliverable using token estimator and historical data.
3. **Workspace Provisioning**: Workspace manager creates Git repos, VSCode.dev environments, design boards.
4. **Task Capsules Activation**: For each deliverable, MAO instantiates appropriate capsules (e.g., `mobile_ui_dev`, `payments_backend`, `qa_pipeline_setup`). Each capsule autoloads personas (Developer, QA, PM) and toolkits.
5. **Parallel Execution**: Temporal orchestrates tasks; MAO ensures dependencies (e.g., API design before backend coding).
6. **Tools Interaction**: Tool service calls out to plane.so to create project boards, GitHub for repos/branches, CI/CD for pipelines.
7. **Review Persona**: Project Manager capsule reviews outputs, requests revisions if required. Documenter persona produces release docs.
8. **Knowledge Sync**: Final deliverables stored in Git, knowledge embeddings written to SomaBrain, persona memory snapshots updated.
9. **Completion Report**: Orchestrator returns summary, token spend, artifacts (links), and next steps.

### 5.2 Safety & Governance
- Constitution + Policy Engine validate each step.
- Token estimator enforces budgets; MAO pauses tasks exceeding thresholds.
- Audit logs allow after-the-fact traceability.
- Human override hooks exist (operators can intervene via Admin UI or CLI).

---

## 6. Deployment & Ops

### State Synchronization & Outage Recovery
- **Conversation Events**: Gateway and orchestrator back every inbound message with the transactional outbox pattern. Each message is written to Postgres alongside a durable outbox row, then fanned out to Kafka (`conversation.events`). If the broker is unavailable, the outbox keeps growing; once connectivity resumes, sidecars replay the backlog in order so no tenant loses messages.
- **Durable Queues & Checkpointing**: SLM requests, tool invocations, and capsule telemetry ship through Kafka partitions with replication factor ≥3 and min.insync.replicas set. Worker services persist consumer offsets and processing heartbeats in Postgres so they can resume exactly-once semantics after a crash.
- **Memory Writes & Back-pressure**: SomaBrain ingestion runs as batched upserts keyed by `(tenant_id, memory_id)`. During an outage the memory gateway writes to Redis streams with TTL-based back-pressure; once SomaBrain is reachable, a reconciler drains the stream, replays in timestamp order, and marks entries idempotently. Alerts fire if backlog age exceeds SLO.
- **Settings Sync & Cache Healing**: All configuration changes produce `settings.changed` events containing version numbers. Services keep an in-memory snapshot plus the latest version hash. After a restart they compare versions; if behind, they pull the delta via Settings API and confirm consistency before accepting new work.
- **Disaster Recovery Targets**: Baseline posture aims for <1 minute RPO (thanks to synchronous replication for Postgres and Kafka ISR) and <15 minute RTO. Regional failovers rely on warm SomaBrain replicas and Infrastructure-as-Code scripts described in runbooks. Regular chaos drills validate these metrics.


### Deployment Profiles (Docker)
- `developer-light` – single-service sandbox with mocked dependencies for quick feature spikes; defaults to permissive auth and enables training for fast iteration.
- `developer-full` – docker-compose stack (Postgres/Redis/Kafka/Temporal stubs) mirroring production topology; training opt-in per session.
- `test` – deterministic profile for CI pipelines, seeded data, no learning; personas run in frozen mode.
- `test-debug` – inherits `test` but raises log verbosity and trace exports for reproducing failures.
- `production` – hardened multi-tenant deployment with strict policy thresholds, full auditing, training closed by default.
- `production-debug` – temporary incident mode matching production while enabling deep telemetry; triggers alerts when activated.

All services consume the `SOMAGENT_DEPLOYMENT_MODE` environment variable so docker-compose, Helm charts, or Terraform can flip profiles consistently. Mode changes publish `mode.changed` events for cross-service coordination. Training vs learned persona states remain orthogonal and will be detailed in the training playbooks.

- **Kubernetes** for deployment (autoscaling, node pools). Helm charts per service.
- Temporal cluster or Argo Workflows for MAO.
- **CI/CD** pipeline: lint (ruff), type-check (mypy), tests (pytest), container build, vulnerability scan, deploy.
- **Chaos testing**: simulate loss of SLM provider, SomaBrain outage, network partitions.
- **Backups**: PostgreSQL WAL archiving, SomaBrain snapshot schedule, object storage versioning.

---

## 7. Security & Compliance

- mTLS everywhere; SPIFFE IDs for service auth.
- Row-level security in Postgres; encryption at rest (KMS-managed keys).
- Secret rotation handled via Vault/KMS; API keys stored encrypted with usage tracking.
- SOC2/ISO-ready logging: every settings change, capsule install, training event, tool action is auditable.
- Data residency: SomaBrain + Postgres deployments per region if required.

---

## 8. Developer Experience

- **CLI (`somagent`)**: manage capsules, personas, tokens, training sessions.
- **SDKs**: Python/TypeScript clients for programmatic control.
- **Dev mode**: local docker-compose with mocks (Kafka, Redis, Postgres, local `/mem`).
- **Admin UI**: card-based, reactive configuration and monitoring.

---

## 9. Autonomous Capability Roadmap

1. **Phase Alpha**: Manual capsule execution + MAO scheduling.
2. **Phase Beta**: Autop-run workflows with optional human approvals.
3. **Phase Gamma**: Fully autonomous Jarvis mode with self-improvement loops (capsule refinement suggestions, persona tuning), subject to constitution.
4. **Phase Delta**: Marketplace-driven ecosystem—tenants/partners submit new capsules, tool adapters, persona shots.

---

## 10. Agent Density Strategy — Task Capsules

We do **not** need thousands of standing agents. Instead we introduce **Task Capsules**:

- A Task Capsule is a fully described job: intent, desired deliverable, persona template, tool stack, memory snapshots, guardrails, and budget. It’s a portable object stored in SomaBrain (or the marketplace) that any orchestrator can spin up on demand.
- When MAO decides work is required, it instantiates a Capsule → Persona Instance (just-in-time agent). When the task completes, the instance dissolves, leaving behind artifacts and a summarized memory replay.
- Capsules can be reused or parameterized (e.g., “Generate weekly analytics report” capsule runs every Monday with fresh data). The orchestrator simply drops in context and executes.
- Capsules combine the strength of workflows (repeatability) and agents (autonomy). They share three traits:
  1. **Persona mold** – which personality/skill shot to apply (Developer, QA, PM). 
  2. **Tool suite** – which integrations to mount (VSCode.dev, Plane.so, GitHub).
  3. **Constitutional policy** – what rules or budget limits are strict for this capsule.

### Why Capsules beat “lots of agents”
- **Scale** – One orchestrator could launch thousands of Capsule instances in parallel (each ephemeral), without the overhead of maintaining thousands of agent processes.
- **Updatability** – Modify the capsule template (better prompt, new tool) and all future runs benefit instantly—no retraining dozens of permanent agents.
- **Marketplace ready** – Capsules become marketplace assets: “Plane Project Starter,” “Bug Triage Sprint,” “Security Audit Sweep.” Users install them like workflows but with richer persona/tool context.
- **Explainability** – Capsules versioned like code; easy to audit who ran what, with which rules, at which time.

### Capsule Lifecycle
1. **Authoring** – Create from scratch or convert an existing training session/workflow. Define persona, tools, knowledge snapshots, expected outputs, review checkpoints.
2. **Event Trigger** – Manual command, schedule, or automated signal (e.g., new GitHub issue → run Capsule “Issue Classifier”).
3. **Instantiation** – Orchestrator loads persona shot, tools, and context; spins up SLM/memory sessions. Capsule ID attaches to all logs/audits.
4. **Execution** – Capsule agent works autonomously within its scope, coordinating sub-tasks if needed. Results persisted to SomaBrain or external systems (Plane project, code repo).
5. **Completion & Learning** – Capsule produces summary and optionally updates its own template (under governance) so future runs get smarter.

### Capsule Types
- **Atomic** – Single persona, simple deliverable (e.g., “Summarize meeting transcript”).
- **Composite** – Capsule that internally spins other capsules (like nested workflows): e.g., “Ship Mobile Release” orchestrates design, dev, QA capsules.
- **On-demand Utility** – Capsules representing single API tasks (create repo, provision server) that personas can call mid-conversation.

This model lets SomaGent scale to thousands of tasks without a permanent agent army: a lean set of persona templates + a library of Task Capsules + a strong orchestrator equals infinite flexibility.

SomaGent is designed to feel like handing Neo a new skill shot: the orchestrator spawns exactly the personas you need, gives them the tools and knowledge, coordinates them via modern workflow tech, and keeps everything constitutionally safe and observable.
