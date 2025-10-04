⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data. Sabe this EVERYWHRE at the start of every Document!

# SomaGent Development Roadmap

This roadmap merges everything discussed so far into a detailed execution plan. Each phase includes deliverables, success metrics, dependencies, and ideas for future expansion leveraging SomaBrain’s strengths.

---

## Development Strategy

To keep velocity high without sacrificing coordination, we structure delivery around three parallel **capability streams**, reinforced by vertical slices and shared design docs.

1. **Governance & Core** – constitution service, policy engine, identity, security, observability, API/event contracts.
2. **Runtime & Intelligence** – orchestrator, Multi-Agent Orchestrator (Temporal/Argo), SLM service, memory gateway, Task Capsule runtime.
3. **Experience & Ecosystem** – admin console, marketplace, capsule builder, tool adapters, documentation/SDKs.

Each significant feature ships with a short design note in `docs/design/` reviewed across streams. We prioritize “vertical slices” (e.g., training → persona synthesis → marketplace listing) so stakeholders see end-to-end value early. Governance tasks (mTLS, secrets, audits) and token logging start in the first slice and tighten over time. An innovation track (5–10% time) funds experiments (auto-generated adapters, UI co-pilots, ethics overlays) that can graduate into the roadmap.

---

## Phase 0 – Foundations (Weeks 0–1)
**Objectives**: Establish repo scaffolding, core infrastructure, and naming alignment.
- Create new SomaGent repository (services/, libs/, infra/, docs/, tests/).
- Set up docker-compose for local dev (Kafka, Redis, Postgres, vector DB, SomaBrain stub, local `/mem` API).
- Configure CI pipeline: lint (ruff), type-check (mypy), unit tests (pytest), build/push containers.
- Finalize SomaGent branding (docs, README, CONTRIBUTING) and migration notes from Agent Zero.
- Integrate Identity baseline (JWT issuance, guest limited mode).
- Success metric: Local dev stack spins up with `docker compose up`; base health endpoints green.

## Phase 1 – Constitution & Settings (Weeks 1–3)
**Objectives**: Constitutional enforcement, settings persistence, secure configuration.
- Constitution Service (FastAPI): poll `/constitution/version` & `/load`, verify signature, store in Postgres.
- Policy Engine (NumPy + SMT) ready for synchronous evaluation; expose `/policy/evaluate` API.
- Settings service & migration: import from legacy `settings.json`, store in Postgres (encrypted secrets via KMS/Vault).
- CLI utilities: `somagent constitution status`, `somagent settings export/import`.
- Success metric: constitution hash cached in Redis; policy evaluation < 10 ms; settings accessible via API.

## Phase 2 – Runtime Core & Training (Weeks 3–5)
**Objectives**: Orchestrator enforcement, training mode, audit streams.
- Orchestrator service: route interactions, attach constitution hash & policy verdict to each step.
- Conversational Experience service (text/WebSocket): stream partial tokens, enforce moderation before orchestrator, emit `conversation.events`.
- Training mode API: Admin-only start/stop, hashed training lock in Redis, `training.audit` events in Kafka.
- Persona synthesis placeholder: record training data, stub persona package generation.
- Observability baseline: Prometheus metrics (requests, latency, policy decisions), structured logging with trace IDs.
- Success metric: training mode UI toggles, audits captured, policy rejections seen in logs; real-time text chat functional.

## Phase 3 – SLM & Memory (Weeks 5–7)
**Objectives**: Language model backplane, memory integration, token accounting.
- SLM Service: connect to SomaBrain `/slm/generate` & `/slm/stream`, support streaming to UI; adapter interface defined.
- Audio pipeline: integrate ASR/TTS adapters, handle Opus/PCM streaming, emit log-mel/MFCC embeddings + energy analytics, and measure WER/MOS for governance.
- Memory Gateway: wrap `/remember`, `/recall`, `/rag/retrieve`, `/link`, `/persona`; fallback to `/mem` dev stub.
- Token logging: store per-call tokens/latency; `slm.metrics` Kafka topic.
- Workspace manager stub: allocate local scratch directories for future tool interactions.
- Success metric: full conversation loop (text + voice) using SLM + memory; tokens recorded per tenant and audio embeddings/energy metrics captured.

## Phase 4 – Admin Console & Token Forecasting (Weeks 7–9)
**Objectives**: Deliver new settings UI, integrate token estimator, marketplace stub.
- React/Vue Admin console with tabs: Overview, Identity & Access, Models & Providers, Memory & SomaBrain, Tools & Integrations, Marketplace & Personas, Automation & Maintenance.
- Model profiles + API key collections: create profile, assign to chat/util/embed/browser/voice roles.
- Token estimator service: baseline heuristics + historical data; show forecasts in UI.
- Marketplace UI stub: list curated persona/tool bundles with compliance badges, token estimates.
- Training mode controls, tunnel creation, budgets/test-drive buckets in Identity tab.
- Success metric: admin can configure entire stack via UI, including voice/LLM profiles; forecasts displayed before running tasks.

## Phase 5 – Marketplace Backend & Security Hardening (Weeks 9–11)
**Objectives**: Capsule publishing, moderation, strong security posture.
- Capsule schema finalized; CLI + UI for authoring (convert training session → capsule).
- Marketplace backend: package upload, signature verification, dependence check, moderation flows. The `task-capsule-repo` service now stores submissions in Postgres with attestation hashes (`POST /v1/submissions`), exposes reviewer workflows (`POST /v1/submissions/{id}/review`), and returns compliance summaries so governance can approve packages before they appear in search results. MAO consumes those capsules directly via `POST /v1/templates/import`, converting workflow definitions into executable templates and optional schedules in a single call. Tenant installations are tracked via `/v1/installations` (with `/v1/installations/{id}/rollback` for reversions). Analytics now ingests per-capsule billing signals (`POST /v1/billing/events`) and surfaces aggregated ledgers/exports (`GET /v1/billing/ledgers`, `/v1/exports/billing-ledger`) for finance pipelines. Disaster recovery drills run through the `dr_failover_drill` capsule + `scripts/ops/run_failover_drill.sh`, recording outcomes via `/v1/drills/disaster` for RTO/RPO dashboards.
- Security enhancements: SPIFFE/SPIRE mTLS across services, Vault/KMS secret rotation, workload attestation (Nitro/SEV where available).
- Token anomaly alerts, Prometheus + SomaSuite dashboards for budgets.
- Success metric: admin publishes capsule, another tenant installs; attestation evidence stored; alerts for token overruns.

## Phase 6 – Validation, Runbooks & Launch (Weeks 11–12)
**Objectives**: Chaos testing, documentation, staged rollout.
- Chaos scenarios: SLM outage fallback, SomaBrain downtime, Kafka partition loss.
- Performance tests: SLM throughput, token forecast accuracy, capsule execution time.
- Runbooks: constitution update, incident response, capsule rollback, training override.
- Staged tenant rollout, monitoring, post-launch retrospective.
- Success metric: runbook checklists complete, alarms green, first tenants onboarded.

## Phase 7 – Multi-Agent Orchestrator (MAO) (Weeks 12–16)
**Objectives**: Temporal/Argo integration, Task Capsule execution at scale.
- Deploy Temporal cluster (or Argo); implement MAO service that maps capsules to workflows.
- Workspace manager integration: spin VSCode dev containers, Git repos, design boards per persona.
- Capsule scheduling logic: sequential/parallel execution, review gates, artifact bundling.
- Project dashboard UI: show task graph, agent personas, statuses, artifact links.
- Success metric: “Build sample project” command triggers multi-task execution; outputs assembled with minimal manual intervention.

## Phase 8 – Tool Ecosystem Expansion (Weeks 16–20)
**Objectives**: Integrate key external tools, provide auto-generated adapters, enhance automation.
- Priority adapters: Plane.so, GitHub Projects, Notion, Slack/Teams, Terraform, Penpot, Jira, AWS/GCP, Kubernetes.
- Automatic adapter generator for OpenAPI/GraphQL specs.
- UI automation via Playwright for non-API SaaS.
- Marketplace entries for tool bundles (e.g., “Agile Squad Starter Pack”).
- Success metric: Developer persona uses capsule to create Plane project, Git repo, CI pipeline automatically.

## Phase 9 – Capsule Builder & Persona Synthesis (Weeks 20–24)
**Objectives**: Make capsule creation accessible, enable advanced training outputs.
- Visual Capsule Builder UI: drag personas/tools/policies into a reusable template.
- Persona synthesizer pipeline: transforms training session transcripts/docs into signed persona shots automatically.
- Capsule evolution suggestions: gather feedback from completed runs, propose template improvements (admin approval required).
- Success metric: non-technical admin builds capsule via UI; training session automatically yields persona shot.

## Phase 10 – KAMACHIQ Mode (Weeks 24–30)
**Objectives**: Full autonomy vision.
- High-level planner capsules (Project Bootstrapper) create entire project DAGs from roadmaps.
- Self-provisioning infrastructure capsules: spin new SomaGent instances, configure identity/constitution, bootstrap knowledge.
- Governance overlays: ethical modulators per industry, human override hooks, safe fallback modes.
- KAMACHIQ console: conversational interface to request complete projects (“Build SomaBrain-based mobile app”) and monitor progress.
- Success metric: End-to-end project executed by SomaGent with minimal human intervention, within budget & policy constraints.

---

## Feature & Innovation Backlog
- **Constraint-based scheduling**: Integrate Z3/OptaPlanner for powerful plan optimization.
- **UI/Voice Co-pilot**: Whisper/TTS integration so agents can join meetings, capture tasks.
- **Agent Negotiation**: Cross-tenant collaborative capsules with strict data boundaries.
- **Capsule Analytics**: Productivity insights, success rates, reinforcement signals for persona improvement.
- **GitOps integration**: Agents submit infrastructure changes via pipeline PRs for auditable deployments.
- **Ethical overlays**: domain-specific constitutions (finance, healthcare) for plug-and-play compliance.
- **Cross-platform adapters**: connectors for LangChain, CrewAI, AutoGen to interoperate with SomaGent capsules.

---

## What SomaGent Offers the World
1. **Autonomous Software Factory** – Deploys real tools (Plane, VSCode, GitHub, cloud platforms) to build and manage projects end-to-end.
2. **Persona Marketplace** – Shared library of expertly trained personas and capsules, similar to an app store for work.
3. **Constitutional Safety** – Transparent, auditable decisions under SomaBrain’s global constitution.
4. **Token & Budget Intelligence** – Predictive cost estimates and automated budget control.
5. **Task Capsules** – Reusable, versioned modules that blend workflows with autonomous agents.
6. **Training-to-Persona Pipeline** – Capture domain knowledge from experts, synthesize into reusable personas instantly.
7. **Open Source, Modular Stack** – Built on vibrant OSS projects (FastAPI, Temporal, Redis, Kafka, Quadrant, etc.) ready for enterprise deployment.

---

## Dependencies & Decisions
- **Temporal vs Argo**: choose Temporal for long-running workflows, Argo if team prefers K8s-native YAML.
- **Vector backend**: FAISS/pgvector for self-managed, Quadrant for managed multi-tenant similarity search.
- **Secrets management**: Vault vs cloud provider KMS.
- **UI framework**: React + Tailwind (or Vue) for Admin console, aligning with existing team skills.

---

## Risk & Mitigation
- **Tool API changes** – Build AppSpec/GraphQL auto-adapters, nightly health checks, fallback automation.
- **Budget overruns** – Token estimator + strict enforcement; escalate when predictions > thresholds.
- **Security incidents** – mTLS, attestation, SOC2 continuous compliance; quick revoke for compromised personas.
- **User adoption** – Focus on capsule builder, documentation, sample capsules to reduce learning curve.

---

## Success Metrics
- Phase-by-phase completion checks (above).
- Token forecast accuracy > 85% confidence by Week 12.
- Marketplace with > 10 curated capsules by Week 16.
- Autonomous project completion (KAMACHIQ mode) pilot by Week 30.
- Community contributions: aim for external capsule/tool adapters by Week 24.

---

## Closing Vision
SomaGent combines constitutional AI governance, Task Capsules, and real-world tool orchestration to create a “KAMACHIQ-grade” assistant. From a single command, it can plan, build, and deploy entire projects across SaaS tools and infrastructure—open source, audited, and extensible. This roadmap lays the path to deliver it, while leaving room for innovation (capsule marketplaces, ethical overlays, agent negotiation) that pushes the industry forward.
