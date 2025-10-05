⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data. Sabe this EVERYWHRE at the start of every Document!

# SomaGent Master Plan

## 1. Philosophy
SomaGent is a constitutionally governed, multi-tenant agent platform built on top of SomaBrain. Instead of hardcoding dozens of rigid agents, we compose **dynamic agent instances** per task: personas, skills, and toolkits are loaded on demand ("Matrix uploads"). A single orchestrator can spawn multiple persona instances when needed. This keeps the system lean while allowing near-infinite specialization.

> **Document map**
> - `docs/SomaGent_Architecture.md` – deep dive into services, data flow, Task Capsules, and KAMACHIQ-mode autonomy.
> - `docs/SomaGent_Roadmap.md` – execution plan with capability streams, vertical slices, and phase breakdowns.
> - `docs/SomaGent_Security.md` – security & moderation playbook (identity, moderation strikes, sandboxed tools, compliance).
> - `docs/design/` (future) – implementation notes for major features.

> _Conclusion_: We don’t need a zoo of permanent agents. A capable orchestration layer plus reusable persona packages is more scalable, secure, and observable.

---

## 2. Core Components

### 2.1 Constitution
- SomaBrain hosts the constitution (`/constitution/version`, `/load`, `/validate`).
- Constitution Service downloads signed versions, verifies, stores in Postgres, publishes Kafka `constitution.updated` events.
- Policy Engine (NumPy + SMT) evaluates every action: `S(a) = Σ w_i φ_i(x(a))`. Actions must satisfy `S(a) ≥ θ` or are blocked.

### 2.2 Identity & Training
- Identity Service supports Guest + federated login (OIDC, SAML). JWTs carry role capabilities (e.g., `training:manage`).
- Admins toggle training mode via signed requests; orchestrator issues hashed training locks stored in Redis. All training activity is isolated by `training_session_id` and audited (`training.audit`).

### 2.3 Orchestrator Layer
- **Base Orchestrator** handles conversation loops, SLM calls, memory operations, tool invocations, with constitution enforcement.
- **Multi-Agent Orchestrator (MAO)** sits on top: builds task graphs, spawns persona instances, manages dependencies and workspaces. Uses Temporal/Argo for enterprise-grade workflow execution.
- MAO decides whether to run tasks sequentially or in parallel based on dependencies, budgets, and token forecasts.

### 2.4 Personas & Skillshots
- Persona packages stored in SomaBrain contain traits, prompts, skillset references, required tools, and knowledge embeddings. Signing guarantees authenticity.
- Training mode captures company-specific knowledge; closing training synthesizes a new persona package ready for Dev/Test/Prod.
- Marketplace allows sharing persona/skill/tool bundles. Installations run through policy checks and token budget approvals.

### 2.5 Tools & External Systems
- Tool Registry defines each integration (e.g., Plane.so, VSCode.dev, GitHub, Penpot). Includes authentication, capabilities, sandbox policies.
- Tool Service provisions adapters (REST, CLI containers) and logs actions (`tool.events`).
- Personas reference tools as part of their skillshot, so when a persona spins up, the correct tool set is available.

### 2.6 SLM Service
- Async workers consume `slm.requests`, call SomaBrain `/slm/generate` or `/slm/stream`, or other providers via adapters. Streams responses on `slm.responses` with token/latency metrics.
- Token estimator service predicts usage before execution; budgets enforced via Redis/Postgres.

### 2.7 Memory & SomaBrain Gateway
- Wrappers for `/remember`, `/recall`, `/rag/retrieve`, `/link`, `/persona`, `/graph/links`, `/plan/suggest`.
- Hybrid RAG (vector + graph). Local `/mem` sidecar (port 9596) for development fallback.

### 2.8 Admin Console (Settings)
- Tabs: Overview, Identity & Access, Models & Providers, Memory & SomaBrain, Tools & Integrations, Marketplace & Personas, Automation & Maintenance.
- Model profiles + API key collections with rotation metadata. Memory presets (Basic/Advanced/Custom). Training controls & tunnel creation under Identity.

---

## 3. Multi-Agent Patterns

### 3.1 Task-Oriented Agents
- For most workloads, one orchestrator + dynamic persona instances suffice. Example: a “Product Launch” workflow spins up developer, QA, documenter, designer personas as separate AgentInstances within a single orchestrated project. No need to pre-provision dozens of agents.

### 3.2 When to Spin Multiple Agents
- **Parallel work**: distinct tasks with no shared resources (e.g., backend vs. frontend implementation). MAO schedules in parallel.
- **Specialized tool environments**: e.g., five VSCode.dev containers for different components. Each persona gets dedicated workspace via Workspace Manager.
- **Role-driven oversight**: project manager persona monitors task status, reviews outputs before subsequent steps.

### 3.3 “Matrix Upload” Workflow
1. Orchestrator selects persona shot (`developer_backend.v1`).
2. Persona Loader pulls signed package; Policy Engine confirms compliance.
3. AgentInstance starts with uploaded memory/tool knowledge.
4. Work proceeds; optionally, new learnings stored back to SomaBrain for reuse.

---

## 4. Token & Budget Strategy
- Token estimator 
  \[ tokens\_est = baseline(task) + Σ tool\_coeff × expected\_calls + persona\_factor \]
- Forecasts displayed before execution; confidence interval shown. Budgets stored in Redis/Postgres; warnings or approval flows for high-cost actions.
- Test-drive credits available for new tenants.
- Actuals vs forecasts logged for continuous improvement.

---

## 5. Roadmap Snapshot

1. **Foundations (Week 0–1)** – Repo skeleton, Kafka/Redis/Postgres setup, identity baseline, settings migration.
2. **Constitution Service (Week 1–3)** – Signature verification, Postgres store, policy engine, event publishing.
3. **Runtime & Training (Week 3–5)** – Orchestrator enforcement, training mode (locks/PINs), audit streams.
4. **SLM & Memory (Week 5–7)** – SLM service, memory gateway, token logging.
5. **Marketplace & Settings (Week 7–9)** – Admin console redesign, marketplace UI, token forecasting, budgets.
6. **Marketplace Backend & Security (Week 9–11)** – Package uploads/moderation, attestation, mTLS, constitution updates workflow.
7. **Validation & Launch (Week 11–12)** – Chaos tests, load tests, runbooks, staged rollouts.
8. **Multi-Agent Orchestration (post Phase 6)** – Integrate Temporal/Argo scheduler, workspace manager, project dashboards, collaborative personas.

---

## 6. Enterprise Considerations
- High availability (K8s, replicas, multi-region backups).
- Compliance (SOC 2/ISO-ready audit logs, data residency, RLS in Postgres).
- Observability (Prometheus, SomaSuite dashboards, SIEM, alerting on budgets/violations).
- Secrets management (Vault/KMS), zero-trust network (SPIFFE).
- Release management (CI/CD, canaries, incident response playbooks).

---

## 7. Tool Expansion Strategy
- Tiered integration backlog (Plane.so, Notion, GitHub Projects, Slack, Jira, etc.).
- For each tool: define capabilities, authentication, provisioning, audit fields, marketplace metadata.
- Marketplace bundles can include curated tool sets (e.g., “Agile Squad Pack” installs Plane, GitHub Repo templating, Slack channels automatically).

---

## 8. Key Principles
- **Dynamic Personas**: instantiate on demand; don’t maintain a static army.
- **Strong Orchestration + Task Graphs**: ensures parallelism, dependency management, and cost control.
- **Constitution everywhere**: every action carries hash + policy score.
- **Audit-first**: every change (settings, training session, tool use) is logged and explainable.
- **Developer Velocity**: typed APIs, clean admin UI, documented CLI tools make the platform approachable for contributors.

---

## 9. Next Steps
1. Finalize service scaffolding & migrations.
2. Implement constitution + settings migration.
3. Launch SLM/memory services.
4. Build new Admin console.
5. Stand up token estimator + budgets.
6. Integrate marketplace + training synthesis.
7. Prototype MAO using Temporal for parallel developer personas.
8. Add Plane.so (and other real-world tools) as first-class adapters.

---

## 10. Agent Density Strategy — "Task Capsules"

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
