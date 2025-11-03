# SomaAgentHub Marketplace & Tool Catalog — Brainstorming (2025-11-03)

Purpose: capture a crisp, shared understanding of the Marketplace as the Catalog of Everything (personas, task capsules, tools) with metric-driven budgets and observable actions across the hub.

---

**Vision**
- The Marketplace is the single catalog for everything agents use or become:
  - Personas (productized agents) that can be installed per tenant/environment.
  - Task Capsules (versioned, reviewed recipes with typed inputs/outputs and steps).
  - Tools/Integrations (capability providers) reachable via provisioning capsules and adapters.
- Every proposal by the LLM becomes a concrete, auditable action in the hub (policy checked, budgeted, measured).
- Every action emits metrics that roll up to plan/tenant budgets and operator SLO dashboards.

---

**Scope of the Marketplace**
- Personas
  - Manifested skills, guardrails, and monetization metadata; installable “as products”.
  - Published via submission → automated checks → review → install.
- Task Capsules
  - Versioned manifests; approved for tenant scopes; contain budget hints and required capabilities.
  - Executed by KAMACHIQ/activities; fully measured (time/tokens/calls/storage).
- Tools / Integrations
  - Described in the Tool Catalog (see below) with capabilities (e.g., project_management, email_marketing), provisioning capsule id, required secrets, health probe, and cost profile.
  - Installable per tenant/environment with policy gates.

---

**Tool Catalog (Concept)**
- Capability Taxonomy: canonical list (project_management, docs_repository, blog_cms, email_marketing, social_scheduler, approvals, analytics, figma_render, etc.).
- Tool Entry (minimal):
  - `id`, `display_name`, `capabilities[]`, `provisioning_capsule_id`, `required_secrets[]`, `health_probe`, `cost_profile` (qualitative/estimates).
- Decision Contract (LLM → Hub):
  - `decision_id`, `capability_needed`, `candidates[]`, `chosen_tool`, `rationale_summary`, `confidence`, `user_confirmation` (bool), `policy_checked` (bool), `outcome`.
- Install Flow: policy evaluate → run provisioning capsule → record installation → emit metrics → expose bindings to the plan.

---

**Budgets & Costs (Metrics-Driven)**
- Budget Envelopes:
  - Per plan and per tenant: token budget, external API calls, compute/memory, storage/egress, max tool installs.
  - Soft/hard limits; pause/escalate when exceeded.
- Cost Signals (measured in hub):
  - LLM: tokens_used, model/provider; derive cost via rate table.
  - External API calls: per provider/endpoint/status.
  - Compute/Memory time: capsule execution ms → CPU-hours and GB-hours.
  - Storage/egress: GB-hours, bytes transferred for artifacts.
- Rate Sources: “another program” (billing service / external system) provides price lists; hub converts usage → estimated cost for budget enforcement and dashboards.

---

**Required Telemetry (Every Action Measurable)**
- Common Dimensions: `tenant`, `plan_id`, `workflow_id`, `session_id`, `capsule_id`, `capsule_version`, `tool_id`, `capability`, `actor` (agent/persona), `environment`.
- Core Metrics (Prometheus-friendly):
  - `capsule_runs_total{capsule,status}`
  - `capsule_step_latency_seconds_bucket{capsule,step,action}`
  - `tool_decision_total{tenant,capability,tool,outcome}` (proposed/chosen/rejected/failed)
  - `tool_install_total{tool,status}` and `tool_install_latency_seconds`
  - `external_api_calls_total{tool,endpoint,status}`
  - `llm_tokens_total{provider,model}` and `llm_cost_usd_total{provider}`
  - `policy_decisions_total{rule,outcome}`
  - `budget_violations_total{tenant,scope}` and `budget_remaining_ratio{tenant,scope}`
  - `temporal_workflow_duration_seconds` and activity retry/error counters
- Tracing: propagate `decision_id`, `plan_id`, `workflow_id`, `session_id`, `tenant` as trace baggage across Gateway → Orchestrator → Activities → Adapters.

---

**Runtime Flow (Marketing Campaign Example)**
- Intake: Wizard collects goals, channels, approvals, voice.
- Gap Analysis: LLM reasons about missing capabilities (e.g., project_management) and proposes a tool with `ToolDecision` (no chain-of-thought stored; only rationale summary).
- Policy & Budget Gate: evaluate policies and budget envelopes.
- Wave 0 Provisioning: run provisioning capsules for chosen tools; record installs, bindings, and metrics.
- Execution Waves: research → content → design → review/gov → distribution; parallel where possible; each step emits metrics and artifacts.
- Handoff: package results (ZIP, README, links) + distribution report; update cost/budget.

---

**Governance & Policy**
- Submission: attestations/signatures on capsules/personas/tools; automated lint/static checks.
- Install: per-tenant allow/deny lists by action/provider; policy engine evaluations captured as events.
- Execution: gates for high-impact steps (publish, share, external data egress) with timeouts and escalation.

---

**High-Level Data Model (Sketch)**
- `CatalogItem(id, type: persona|capsule|tool, name, summary, tags, owner, verified)`
- `CapsulePackage(id, capsule_id, version, definition, status, attestation_hash, compliance_report, reviewer, approved_at)`
- `PersonaManifest(id, version, skills, guardrails, pricing, signature)`
- `Tool(id, capabilities[], provisioning_capsule_id, required_secrets[], health_probe, cost_profile)`
- `Installation(id, tenant_id, environment, item_id, item_type, version, status, notes, installed_at, installed_by)`
- `Rating(id, item_id, user_id, stars, review, created_at)`
- `Decision(decision_id, type: tool|plan|policy, rationale_summary, outcome, metadata)`
- `Usage(tenant_id, plan_id, metric, value, dims…)` (for analytics/billing)

---

**API Surface (Direction of Travel)**
- Catalog:
  - `GET /v1/catalog?type=persona|capsule|tool&capability=&tag=&q=`
  - `GET /v1/catalog/{id}` (detail)
  - `POST /v1/ratings` (rate item)
- Submissions/Moderation/Install:
  - `POST /v1/submissions` → `POST /v1/submissions/{id}/review`
  - `POST /v1/installations` → `GET /v1/installations`
- Decisions & Budgets:
  - `POST /v1/decisions/tool` (record ToolDecision)
  - `GET /v1/budgets?tenant=&scope=plan|tenant` (envelope state)

---

**Operator Views & SLOs**
- Catalog health (indexing, search latency, stale listings), install success rate, average time-to-first-artifact, distribution P95 latency.
- Budget dashboards per tenant/plan; cost composition (LLM/API/storage/compute/tool fees).
- Policy denials by rule/provider; external API reliability (429/5xx) per integration.

---

**Roadmap (Incremental)**
- Phase 1: Consolidate on a single marketplace backend (extend Capsule Repo), add search/tags/ratings, wire Admin Console to live APIs.
- Phase 2: Tool Catalog + capability mapping, `ToolDecision` events, Wave 0 provisioning; basic budgets and alerts.
- Phase 3: Pricing integration with billing rates, verified publishers/signing, capsule DSL linter and contract tests.
- Phase 4: Persona productization, marketplace monetization toggles, partner onboarding playbooks.

---

**Open Questions**
- Monetization model per persona/capsule/tool (free, one-time, subscription, usage-based)?
- Trust signals: signing authority, security scans, SBOMs for code-carrying capsules.
- Multi-tenancy boundaries for shared tools (org-wide vs project-scoped installs).

