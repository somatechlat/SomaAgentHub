# SomaAgentHub Canonical Roadmap

> READ FIRST — Vibe Coding Rules apply to all changes. See `docs/VIBE_CODING_RULES.md`. Core: No mocks or placeholders; verify existing code and real docs first; minimal files; real implementations; clear contracts; UTC; typed models; observability; honest status. Any change must reference real sources and fit the end-to-end flow.

> Single source of truth for strategic phases, rapid sprints, and deferred items. All previous roadmap documents have been removed and their content consolidated here. Temporal is the orchestrator. Marketplace (capsule distribution & Kong multi‑tenant edge) is explicitly deferred and scoped at the end.

## 1. Vision (Concise)
Deliver a production‑grade autonomous agent hub capable of:
1. Deterministic build/deploy flows for generated applications (Generic Build Workflow pattern; former “Taxi” example was illustrative only)
2. Policy‑gated execution (cost, quota, feature flags)
3. Transparent pricing & payment gating (live pricing → approval → workflow)
4. Secure, observable, auditable multi‑tenant runs
5. Extensible capsule system with future marketplace integration

## 1.1 Strategic Pillars (Merged)
These pillars were previously documented separately; they are now merged here for single-source guidance.
1. Configuration & Bootstrap Unification
2. Typed Service Contracts & Domain Isolation
3. Interface-Driven Architecture (Adapters, Repositories, Policy Engine)
4. Event-Centric Communication & Auditability
5. Cost, Policy, & Safety Guardrails (Pricing + Policy + Moderation)
6. Observability & Operability (Metrics, Tracing, Structured Logs, SLOs)
7. Reliability & Performance (Caching, Backpressure, Circuit Breakers)
8. Testing & Quality Automation (CI Gates, Coverage, Load Profiles)
9. Developer Experience (Tooling, Docs, Templates, Local Environments)
10. Security & Compliance (Secrets, AuthN/Z, Data Boundaries)

Notes:
- Pillars 1–4 underpin Phase P1–P3 execution; pillars 5–10 drive later hardening (Sprints 6–8 and deferred marketplace work).
- All roadmap acceptance criteria reference at least one pillar.

## 2. High‑Level Phases
| Phase | Objective | Core Outcomes |
|-------|-----------|---------------|
| P1 Foundations | Unified Helm chart, stable services, health & metrics | All baseline services deploy clean, probes + Prometheus OK |
| P2 Live Pricing & Billing Gate | Accurate cost estimate + payment intent before workflow start | `/v1/pricing/live`, Stripe intent, OPA budget policies |
| P3 (Cross‑Cutting) LLM Serving Hub | Centralized multi‑provider LLM gateway with RBAC catalog, policies, auditing | Model catalog + provider adapters + quotas/cost + observability |
| P4 Agent Runtime & Build Artifacts | Real agent spawning + static template expansion | Agent‑Spawner service + static templates repo + BuildRun persistence |
| P4 Generic Build Workflow | End‑to‑end Temporal workflow for build + deploy | `build_workflow` (name TBD) activities instrumented, <5 min minimal build |
| P5 Capsule & Policy Maturity | Harden manifest, cost formulas, feature flags | Extended capsule schema + OPA policies (`allow_build`, quotas) |
| P6 Security & Compliance | mTLS, secrets, audit, SBOM | Mesh/Vault integrated, audit events, Trivy + Syft in CI |
| P7 Observability & Performance | Full tracing, metrics, latency targets | OTel spans across workflow chain, dashboards, alerts |
| P8 Deferred Ecosystem | Marketplace convergence + Kong multi‑tenant edge | Consolidated capsule distribution, external gateway patterns |

### 2.1 Legacy Phase Summary (Historical Context)
For continuity, the earlier numbered phase plan (Foundations → Interfaces → Events → Observability → Typing → Data → Security) maps onto current phases and tracks:
| Legacy Phase | Legacy Focus | Current Mapping |
|--------------|-------------|-----------------|
| Foundations | Bootstrap, settings, lint & type baseline | Sprint 1 (Foundations) |
| Interfaces & Contracts | Protocols, repositories, adapters | Sprint 2 + Track B early & Policy additions |
| Event & Workflow Layer | Kafka topics, outbox pattern | Build workflow + future event publisher (Tracks B/P) |
| Observability & Guardrails | Metrics, tracing, budgeting policies | Sprints 2, 7, 8 (Security/Obs tracks) |
| Full Typing & CI | Strict MyPy, CI quality gates | Sprint 8 completion definition |
| Data & Analytics | Aggregations, forecasting | Deferred post core build (Future enhancement section) |
| Security & Compliance | Secrets, mTLS, SBOM, audit | Sprint 7 |

Historical sections are archived under `docs/archive/` and should not be edited; evolve only this canonical document.

### 2A. Cross‑Cutting Program: LLM Serving Hub
The LLM Hub is a centralized, policy‑aware gateway for all LLM access (external APIs, self‑hosted, and deterministic local models). It runs in parallel with P2–P4 and unblocks orchestrator and memory‑gateway consumers.

- Scope: model catalog with RBAC; provider adapters (OpenAI, Anthropic, Azure OpenAI, Ollama, Local Deterministic); cost/quotas; safety & residency policies; audit; OTel metrics/traces; health/circuit breakers; fallback routing.
- Consumers: orchestrator workflows/activities, memory‑gateway embeddings, gateway dashboard (health + catalog), pricing/billing usage events.
- Outcome: a single endpoint `LLM_HUB_URL` is used across services.

## 3. Rapid Sprint Plan (Eight 1‑Week Sprints)
Each sprint has hard, verifiable acceptance criteria. No placeholder code; all endpoints live, tests passing.

### Sprint 1 – Foundations & Helm Consolidation
**Deliverables:** Stable Helm chart (`k8s/helm/soma-agent`), pods Ready, health/metrics endpoints, cleaned port map, CI basic pipeline (lint + tests + build + helm lint).  
**Criteria:** `helm install` on fresh Kind succeeds; `curl <gateway>/healthz` OK; metrics scraped; CI green.

### Sprint 2 – Live Pricing & Budget Policy
**Deliverables:** New `pricing-service` (or evolution of `token-estimator`) exposing `/v1/pricing/live`; pricing sources (token rates + static infra tables); OPA `allow_pricing` & `budget_cap`; gateway endpoint to request estimate.  
**Criteria:** Estimate round trip <200ms; over‑budget request blocked by OPA test; unit tests cover drift & fallback.

### Sprint 3 – LLM Hub (Core)
**Deliverables:** `services/llm-hub` API with model catalog (RBAC‑aware), provider adapters for OpenAI + Local Deterministic; unified endpoints for `/v1/infer/sync`, `/v1/infer/stream`, `/v1/embeddings`; baseline policies (cost caps, per‑tenant quotas); OTel metrics; health endpoints.  
**Criteria:** Catalog filters by role; adapters pass conformance tests; quotas enforced; traces present; orchestrator can call hub in dev.

### Sprint 3 – Billing Gating & Payment Intent
**Deliverables:** Stripe payment intent endpoint `/v1/billing/intent`; webhook consumer `/v1/billing/webhook`; wizard flow updated to require APPROVED state; entitlements check; audit log events (`billing.charge`).  
**Criteria:** Simulated intent lifecycle recorded; webhook test passes; unauthorized build blocked pre‑payment; audit row stored.

### Sprint 4 – Static Templates & BuildRun Persistence
**Deliverables:** `services/static-templates/` repo (FastAPI, React, Helm sub-chart, CI workflow YAML); variable substitution engine; `BuildRun` Pydantic model + `/v1/build/result` endpoint; object store artifact upload.  
**Criteria:** Taxi sample build produces source zip + Helm chart stored; BuildRun query returns artifact URLs; template hash integrity enforced.

### Sprint 5 – Agent-Spawner & Dynamic Agents
**Deliverables:** `agent-spawner` FastAPI service (`POST /v1/spawn` → K8s Job/Deployment); `code-generator` and `ui-customizer` lightweight agent images; spawn concurrency metric; OPA `max_agents_per_user`.  
**Criteria:** ≥20 concurrent spawns succeed in test; spawn metrics present; policy blocks excess; agent outputs real generated code consumed by workflow.

### Sprint 6 – LLM Hub (Policies & Fallback)
**Deliverables:** Safety & residency policies; cost estimation per model; fallback chains (primary → cheaper/region‑compliant → local deterministic); provider circuit breakers; admin read API for catalog/health.  
**Criteria:** Policy decisions attached to responses; fallback counters observed; controlled degrade under provider rate limits; admin list shows model states.

### Sprint 6 – Generic Build Temporal Workflow
**Deliverables:** `build_workflow` with activities: `fetch_live_pricing`, `opa_budget_check`, `copy_templates`, `spawn_agent`, `docker_build`, `helm_deploy`, `persist_result`; retry & compensation; OTel instrumentation.  
**Criteria:** Minimal build completes <5 min; failure triggers compensation (artifact cleanup); traces show full span chain.

### Sprint 7 – Security & Compliance Baseline
**Deliverables:** Service mesh mTLS (Linkerd/Istio) injected; Vault secret templates for Stripe keys; Syft SBOM + Trivy scans in CI; OPA audit log export; GDPR delete endpoint for BuildRun.  
**Criteria:** All inter‑service traffic mTLS verified; CI blocks high severity CVEs; secret rotation test passes; deletion removes artifacts & marks record.

### Sprint 8 – Observability & Performance Hardening
**Deliverables:** Metrics (`build_latency_seconds`, `agent_spawn_failure_total`, `budget_overrun_total`); latency SLIs + alert rules; chaos tests (pod kill) + resiliency report; performance tuning (image cache, parallel build/deploy).  
**Criteria:** 99.9% success for baseline scenario; alerts fire within 30s; chaos report documents recovery times; build latency histogram p95 < target.

## 3.1 Blueprint Alignment (A–J → Sprints)
The Senior‑Architect blueprint maps cleanly onto our sprint plan as follows:

- A Foundations → Sprint 1
- B Live‑Pricing Service → Sprint 2
- C Agent‑Spawner → Sprint 5
- D Dynamic Agents (code‑generator, ui‑customizer) → Sprint 5
- E Capsule Catalogue & Marketplace → Deferred to Phase P8 (see section 9)
- F Result‑Persistence Extension (BuildRun) → Sprint 4
- G Generic Build Workflow (formerly Taxi_builder example) → Sprint 6
- H Security & Compliance → Sprint 7
- I Observability & Reliability → Sprint 8
- J Test Suite & Documentation → Spans Sprints 4–8; finalize post‑Sprint 8

## 3.2 LLM Hub Track (Three Focused Sprints)
| Sprint | Goal | Key Deliverables | Acceptance |
|-------|------|------------------|------------|
| L1 | Hub Core | Catalog (RBAC), adapters (OpenAI, Local), `/v1/infer`, `/v1/embeddings`, quotas, metrics | Orchestrator calls succeed; role‑filtered catalog works |
| L2 | Policies & Fallback | Safety/residency policies, cost caps, fallback chains, circuit breakers, admin read API | Policy decisions logged; fallback under rate‑limit conditions |
| L3 | Provider Expansion | Add Anthropic/Azure/Ollama adapters; embeddings cache; usage events for billing | Adapters pass conformance; usage events emitted |

## 4. BuildRun Data Model (Authoritative)
| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string (UUID) | Unique workflow/build identifier |
| `capsule_id` | string | High-level capsule or builder key (`taxi_builder_v10`) |
| `requested_by` | string | User/tenant initiating build |
| `pricing_snapshot` | object | Exact pricing used for approval & reconciliation |
| `payment_intent_id` | string | Stripe intent reference (nullable if free) |
| `status` | enum | `pending|running|completed|failed|rolled_back` |
| `started_at` / `ended_at` | timestamps | Timing fields |
| `template_version` | string | Static template bundle hash/version |
| `agent_invocations` | array | Records of each dynamic agent (type, duration, tokens) |
| `artifacts` | array | `{type, path_or_url, sha256}` entries |
| `policy_decisions` | array | OPA decisions with rule + allow/deny + reasons |
| `metrics` | object | Aggregated tokens, build duration, cost breakdown |
| `receipt` | object | Final cost reconciliation result |

## 4.1 Repo Gap Summary (Nov 7, 2025)
- Present: Temporal workflows/activities (some stubs), billing/analytics foundations, marketplace + task‑capsule‑repo, basic OPA rules, object‑store, metrics stack, static template bundle + copy/substitution engine with tests.
- Partial: Pricing (token estimator only), agent spawn (stub only), billing gating (no intent/webhook in gateway), policies (no budget/feature/quotas), observability gaps for build, LLM provider access not centralized.
- Missing: Agent‑Spawner service, code‑generator/ui‑customizer agents, `/v1/build` gateway flow, BuildRun persistence endpoint, Helm sub‑chart for generated apps, Stripe webhook endpoints, expanded OPA policy pack, targeted metrics and security hardening, centralized LLM Hub service.

## 5. OPA Policy Additions
| Policy | Purpose | Input Fields |
|--------|---------|--------------|
| `somagent.build.allow_build` | Gate build start on approval + entitlements | `user`, `tenant`, `approved_amount`, `estimated_cost` |
| `somagent.build.budget_cap` | Ensure cost ≤ approved budget | `estimated_cost`, `approved_amount` |
| `somagent.build.max_agents_per_user` | Limit concurrent agent spawns | `active_agents`, `tenant_quota` |
| `somagent.build.feature_enabled` | Conditional modules (e.g. loyalty) | `requested_features`, `plan_features` |
| `somagent.pricing.allow_pricing` | Allow pricing queries within rate/quota | `tenant`, `daily_queries` |

## 6. Static Template Bundle Layout
```
services/static-templates/
  fastapi/
    app/main.py
    pyproject.toml
    Dockerfile
  react/
    src/App.tsx
    package.json
    vite.config.ts
  helm/
    Chart.yaml
    values.yaml
    templates/deployment.yaml
    templates/service.yaml
  cicd/
    github-actions/app-build.yml
```
Variable substitution map (`{{APP_NAME}}`, `{{IMAGE}}`, `{{PORT}}`, `{{BRAND_COLOR}}`). Integrity verified via bundle hash.

## 7. Metrics & Alerts (Initial Set)
| Metric | Type | Description | Alert Condition |
|--------|------|-------------|-----------------|
| `build_attempts_total` | Counter | Number of build workflow starts | Sudden drop (>50% hour) |
| `build_success_total` | Counter | Successful completions | N/A |
| `build_latency_seconds` | Histogram | End‑to‑end latency | p95 > 360s for 3 consecutive periods |
| `agent_spawn_failure_total` | Counter | Failed spawns | Any non‑zero in last 15m |
| `budget_overrun_total` | Counter | Attempts exceeding approval | >0 triggers immediate alert |
| `pricing_drift_seconds` | Gauge | Age of pricing snapshot vs live | >300s (stale pricing) |

## 8. Security Controls (Phase Targets)
| Control | Sprint Intro | Enforcement Detail |
|---------|--------------|--------------------|
| mTLS Mesh | 7 | Sidecar injection for all Deployments; deny non‑mesh traffic |
| Secrets (Vault) | 7 | Dynamic Stripe key lease; renewal monitored |
| SBOM + Scan | 7 | Syft generates SBOM; Trivy blocks CVE severity ≥ HIGH |
| Audit Logging | 3+ | Structured events for pricing, build start, payment, spawn; shipped to ClickHouse |
| Build Artifact Integrity | 4 | SHA256 recorded; mismatch blocks persistence |
| GDPR Delete | 7 | Delete endpoint purges object store & marks BuildRun `deleted_at` |

## 9. Deferred: Marketplace & Kong Edge
Deferred until after Sprint 8 to focus on deterministic build core. This corresponds to blueprint phase E (Capsule Catalogue & Marketplace) and the Kong multi‑tenant edge.
| Item | Scope at Deferred Phase |
|------|------------------------|
| Capsule Marketplace Merge | Unify `marketplace-service` & `task-capsule-repo` schema; add attestation/signature verification, cost formula fields |
| Kong / External Edge | Deploy Kong gateway for tenant self‑service APIs (publish, install, billing usage) separate from internal build orchestration |
| Paid Capsule Entitlements | Mapping of capsule versions to required plan & automated checkout integration |

## 10. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|-----------|
| Pricing source latency | Slows build approvals | Cache + parallel fetch with timeout fallback snapshot |
| Agent spawn burst | Resource exhaustion | HPA + OPA quota + queue length metric |
| Build artifact bloat | Storage cost & slow retrieval | Enforce size limit, compress, lifecycle policy |
| Policy misconfig | False denials | Unit tests + staging OPA bundle validation before prod |
| Secret rotation failure | Payment outages | Vault lease alerts + fallback read‑only mode (deny new builds requiring payment) |

## 11. Completion Definition (Platform “Production‑Ready”) 
All Sprint 1–8 criteria satisfied; p95 build latency < 5 min; 99.9% success minimal builds; mTLS enforced; SBOM scanning active; audit trail complete; deletion flow verified; chaos recovery documented.

## 12. Immediate Next Step
Proceed with Sprint 1 tasks if not yet complete or begin Sprint 2 if foundation already stable. Confirm pricing strategy (extend `services/token-estimator` into `pricing-service` versus introducing a new codebase). No marketplace implementation in current sprints; defer.

Immediate Actionable Checklist (pick one to start):
1) Scaffold Agent‑Spawner service (FastAPI + Helm)
2) Create Live‑Pricing micro‑service (`/v1/pricing/live`)
3) Define capsule manifest schema (requires_payment, estimated_cost_formula, security_class)
4) Write OPA policies (`allow_build`, `budget_cap`, `max_agents_per_user`)
5) Add static‑template repository (`services/static-templates/fastapi`, `react`, `helm`, `cicd`)
6) Draft Temporal generic build workflow with activities
7) Generate Helm sub‑chart for generated apps
8) Publish Python SDK stub (`soma-sdk-py`) with `register_tool`
9) Set up service mesh (Linkerd/Istio) in dev cluster
10) Write end‑to‑end build test asserting final URL reachability
11) Implement provider adapter layer in `pricing-service` (aws, runpod initial) and expose metrics counters (`pricing_requests_total`, `pricing_budget_decisions_total`).

---
This file supersedes all prior roadmap documents. Do not recreate separate roadmap markdowns—extend this file only.

---

## 13. LLM Serving Hub (Canonical)

Authoritative design for the centralized, policy‑aware gateway that backs all LLM access in SomaAgentHub.

- Purpose: unify providers, enforce RBAC/policies/quotas, standardize observability, and provide a catalog filtered by role/region/compliance.
- API Surface: `/v1/infer/sync`, `/v1/infer/stream`, `/v1/embeddings`, `/v1/catalog/models`, `/v1/admin/health`.
- Catalog Fields: `model_id`, `display_name`, `provider`, `capabilities`, `pricing`, `regions`, `allowed_roles`, `limits`, `safety_profile`, `version`, `state`.
- Provider Adapters (initial): OpenAI, Local Deterministic; (expansion): Anthropic, Azure OpenAI, Ollama.
- Policies: cost caps, per‑tenant quotas, safety classification/redaction, data residency, tool‑use restrictions; decision traces attached to responses.
- Billing: emit `llm.usage` events with tokens/cost per request; reconcile externally.
- Observability: OTel spans per call; metrics for latency, errors, tokens, cost, fallback counts; health/circuit breaker per provider.
- Fallback: policy‑driven chain (primary → cheaper/region‑compliant → local deterministic) with cool‑downs to avoid oscillation.
- Security: prompt segmentation/redaction; encrypted sensitive logs; per‑tenant provider secrets.

### 13.1 Consumers & Integration Points
- Orchestrator: use `LLM_HUB_URL`; activities call hub for inference/embeddings.
- Memory‑Gateway: route embeddings to `/v1/embeddings`; register local adapter as `local-embeddings-v1`.
- Gateway‑API: dashboard shows hub health + catalog.

### 13.2 Migration & Deprecations
- Finalize LLM Hub cutover in docker‑compose, K8s manifests, and CI workflows; remove deprecated service directory.
 
- Remove `services/model-proxy` stub or replace with real multi‑provider adapter inside the Hub.
- Update docs/glossary to reflect the Hub as the sole LLM entrypoint.

### 13.3 Acceptance Criteria (LLM Hub v1)
- Role‑filtered catalog lists only allowed models for the actor.
- OpenAI + Local adapters pass conformance; quotas enforced; cost decisions logged.
- Orchestrator and memory‑gateway operate solely via `LLM_HUB_URL` in dev.

### 13.4 Airflow Integration (Additive Scheduling Layer)
Airflow is integrated as a complementary batch/scheduling system; it does not replace Temporal.

Scope:
- Periodic maintenance: session warmups (`soma_session_warmup`), memory refresh (`memory_refresh`), future embeddings re-index, pricing normalization.
- Governance pipelines: policy bundle validation (compile + golden tests + SBOM/scan) → promote.
- Reconciliation: daily pricing drift audit, usage aggregation for billing entitlements.
- Security & hygiene: scheduled SBOM & vulnerability scan reports; artifact integrity audits.

Boundaries:
- Domain conversational / build workflows remain in Temporal.
- Airflow triggers gateway/service HTTP endpoints; never orchestrates multi-step interactive agent state.

Success Criteria:
- All periodic tasks (pricing normalization, memory refresh, policy validation) operate via Airflow DAGs by end of Sprint 3.
- No duplication of Temporal workflow logic inside DAGs; each DAG run produces auditable lineage (run_id ↔ BuildRun / snapshot IDs).

Risks & Mitigations:
- Overloading Airflow with high-frequency tasks → enforce scheduling SLAs & separate queue.
- Credential sprawl → managed short-lived service tokens via Identity API & secret rotation.

Refer to `services/airflow-service/dags/` for current DAG examples; expansion tracked under Track S & P as appropriate.

---

## 14. Parallel Sprint Plan (Execution)

Run multiple focused tracks in parallel to accelerate delivery. Each track has weekly outcomes and verifiable acceptance criteria. No placeholders.

### Tracks
- Track L (LLM Hub): Centralize model access, policies, fallbacks.
- Track B (Build System): Agent‑Spawner, workflow, artifacts, deployment.
- Track P (Pricing/Billing): Live pricing, payment gating, approvals.
- Track S (Security/Observability): Mesh/Vault/SBOM; tracing/metrics/SLOs.

### Week‑By‑Week Plan (4 Weeks)
| Week | Track L (Hub) | Track B (Build) | Track P (Pricing/Billing) | Track S (Sec/Obs) |
|------|----------------|------------------|----------------------------|-------------------|
| 1 | L1 Core: Catalog (RBAC), OpenAI + Local adapters, `/v1/infer`, `/v1/embeddings`, quotas + metrics | B1: Agent‑Spawner MVP + integrate static templates engine; artifact storage wired | P1: `/v1/pricing/live` with token rate sources; OPA `allow_pricing` | S1a: Bootstrap unified logging/tracing/metrics module; begin mesh plan |
| 2 | L2 Policies & Fallback: safety/residency policies, fallback chain, circuit breakers; admin read API | B2: Generic Build Workflow with `fetch_pricing` → `budget_check` → `copy_templates` → `spawn_agent` | P2: Payment intent + webhook; wizard gating; audit events | S1b: Vault secret templates; SBOM + Trivy CI gates; service health probes standardized |
| 3 | L3 Provider Expansion: Anthropic/Azure/Ollama adapters; embeddings cache; usage events for billing | B3: Deploy via Helm sub‑chart, compensation paths, BuildRun persistence + delete | — | S2: SLO dashboards + alerts; chaos test (pod kill) and resiliency report |
| 4 | L4 Hardening: throughput tests, cost anomaly alerts, provider failover drills; finalize LLM Hub | B4: E2E build test asserting final URL reachability; perf tuning | P3: Reconciliation sanity vs usage events; budgets/quotas refined | S3: Finalize mesh mTLS rollout in dev; documentation + runbooks |

### Acceptance Criteria (Weekly)
- Week 1: Orchestrator calls LLM Hub in dev; Agent‑Spawner spawns ≥10 jobs; pricing endpoint <200ms p50; unified tracing visible across services.
- Week 2: Policy decisions attached to Hub responses; build workflow runs end‑to‑end in dev gated by payment intent simulation; CI blocks HIGH CVEs.
- Week 3: Additional providers pass conformance; BuildRun stores artifacts + receipt; SLO dashboards live; chaos recovery documented.
- Week 4: LLM Hub cutover complete; validate Hub throughput & failover; E2E test green; alerts for cost anomalies and provider degradation verified.

### Dependencies & Parallelization Notes
- Track L enables Track B and P; ensure `LLM_HUB_URL` available by end of Week 1.
- Security hardening (S1) runs in parallel but must not block core flows; gate only on critical CVEs.
- Pricing intents (P2) required before enabling build in prod; dev/staging can simulate approvals while wiring real webhooks.

### Deliverable Artifacts
- Conformance suite for provider adapters (Track L).
- Temporal workflow definition and tests (Track B).
- OPA policy bundle + golden tests (Tracks P & L).
- Dashboards, alerts, and runbooks (Track S).

---

## 15. Wizard State Machine & Preflight Gates

Authoritative design for the conversational intake and pre-execution approvals that gate orchestrator workflows.

- Purpose: collect inputs, compute cost, enforce budget/entitlements/payment, then signal Temporal to proceed.
- States: `collecting → estimating → awaiting_payment → approved | rejected`.
- Storage: short-term via Memory-Gateway; audit fields duplicated in BuildRun.

APIs:
- `POST /v1/wizard` → start session `{intent, tenant_id}` → `{session_id}`
- `POST /v1/wizard/{id}/answers` → append/update answers (idempotent by `question_id`)
- `POST /v1/wizard/{id}/approve` → confirm budget/payment; transitions to `approved`

Preflight sequence (OPA enforced):
1) `estimate_cost` (Pricing Service)
2) `check_entitlements` (Policy Engine)
3) `require_payment` if over plan (Billing)
4) `proceed_with_build` (Temporal signal)

Acceptance:
- Deterministic replays: same inputs + pricing version produce the same estimate.
- Denials are explainable with policy decision traces.

---

## 16. Pricing Source: GPUBROKER (Live Pricing Authority)

Centralizes infra pricing via an upstream provider, with reconciliation at checkout.

- Fetch: `GET GPUBROKER /pricing/summary?profile=<capsule_profile>`.
- Reconciliation: re-query within 5 minutes before payment; require re-accept if drift > 5%.
- Fallback: use LKG cache (TTL ~15m) when unavailable, flag as `stale`.

Observability:
- Metrics: `pricing_drift_percent`, `pricing_reconcile_latency_seconds`.
- Logs: pricing source, timestamps, drift reasons.

### 16.1 Detailed Integration Design (SomaAgentHub ↔ GPUBROKER)

Purpose: Leverage GPUBROKER's real-time provider aggregation (`provider-service`) for deterministic cost estimation and checkout-time reconciliation inside SomaAgentHub.

Upstream Endpoints Utilized:
- `GET /providers` (GPUBROKER provider-service) with query params: `gpu|gpu_type`, `region`, `max_price`, pagination (`page`, `per_page`).
- `GET /health` (sanity + adapter inventory for diagnostics).
- Optional enrichments (phase later): KPI service `GET /kpis/gpu/{gpu_type}` and `GET /kpis/provider/{provider_name}` for cost-per-token or reliability overlays.

SomaAgentHub Pricing Facade:
- `POST /v1/pricing/live` → returns a `PricingSummary` snapshot built from filtered provider offers.
- `POST /v1/pricing/reconcile` → re-fetches offers with identical constraints, computes drift, enforces OPA threshold, yields `PricingReconcileResponse` (receipt & drift flag).

Request Mapping:
| Field | Source | Notes |
|-------|--------|-------|
| `capsule_profile` | client | Maps to a profile config (GPU search terms, default hours/tokens) |
| `region` | client | Passed through to GPUBROKER filter or omitted if None |
| `price_cap` | client | Translates to `max_price` param |
| `required_tags[]` | client | Post-filter on returned `tags`; not sent upstream (GPUBROKER currently lacks that filter) |
| `usage.hours` | client/profile | Used for total cost computation |
| `usage.tokens` | optional | Token cost optional; fallback to internal mapping if KPI service not queried |

Profile Configuration Examples:
```
llm-inference-a100:
  gpu_terms: ["A100", "H100"]
  hours: 20
  tokens: 2000000
  region_allow: ["us-east", "eu-west"]
image-gen-4090:
  gpu_terms: ["4090", "L40", "A6000"]
  hours: 40
training-v100:
  gpu_terms: ["V100", "A100"]
  hours: 100
```

Snapshot Data Model (PricingSummary):
```
{
  source: "gpubroker",
  snapshot_id: <uuid>,
  fetched_at: <iso8601>,
  ttl_seconds: 300,
  stale: false,
  cache_status: "miss|hit|stale",
  constraints: { capsule_profile, region?, price_cap?, required_tags?, gpu_terms:[], usage: { hours, tokens? } },
  offers_considered: <int>,
  provider_warnings: [<string>],
  selected_offer: { provider, gpu, region, price_per_hour, availability, last_updated },
  breakdown: { hourly: <float>, hours: <float>, tokens?: <int>, token_cost?: <float>, bandwidth_cost?: <float>, storage_cost?: <float> },
  total_estimated: <float>
}
```

Reconciliation Logic:
1. Accept prior snapshot (by `snapshot_id` or full body) and re-invoke upstream `GET /providers` with same filters.
2. Select new offer using original selection strategy (cheapest that satisfies tags & availability > threshold).
3. Compute `drift_percent = ((new_total - old_total) / old_total) * 100`.
4. If `abs(drift_percent) > DRIFT_THRESHOLD` (OPA or config, default 5) → `requires_reaccept = true`.
5. Persist receipt: `{ old_total, new_total, drift_percent, selected_offer, stale, source_metadata }` into BuildRun or Billing receipt store.

Failure Modes & Fallbacks:
| Failure | Handling | Metrics/Flags |
|---------|----------|---------------|
| Upstream timeout | Retry (2 attempts, exponential jitter), then LKG snapshot fallback | `pricing_upstream_timeout_total` |
| Partial adapter failures | Upstream response includes `warnings`; accept degraded dataset | `pricing_provider_warnings_total` |
| Empty results | Return error or fallback to LKG if allowed; policy may deny | `pricing_empty_results_total` |
| Redis down (cache) | Graceful degrade to in-memory LRU | `pricing_cache_degraded_total` |
| Drift high at reconcile | Require explicit user acceptance; record denial if rejected | `pricing_drift_high_total` |
| Stale snapshot used | Mark `stale=true`; OPA may block payment | `pricing_stale_snapshot_total` |

Caching Strategy:
- Key: hash of profile + region + price_cap + gpu_terms normalized.
- Redis TTL: 300s; in-memory LRU fallback size ~200 entries.
- Store full JSON snapshot for fast serve; mark `cache_status: hit` on retrieval.

Metrics (Extended):
- `pricing_requests_total{stage="live|reconcile"}`
- `pricing_latency_seconds{stage="live|reconcile"}` histogram
- `pricing_cache_status_total{status="hit|miss|stale"}`
- `pricing_drift_percent` gauge (last reconcile per tenant)
- `pricing_upstream_timeout_total`
- `pricing_provider_warnings_total`
- `pricing_stale_snapshot_total`

Alert Examples:
- High drift: `avg_over_time(pricing_drift_percent[5m]) > 7` → notify.
- Timeouts: `increase(pricing_upstream_timeout_total[10m]) > 20`.
- Empty results spike: `increase(pricing_empty_results_total[10m]) > 5`.

Security & Auth:
- Internal-only network path to GPUBROKER (cluster DNS or service mesh virtual service).
- mTLS enforced (mesh sidecars) + optional internal service JWT header: `Authorization: Bearer <service-token>`.
- Rate limiting: pricing-service local token bucket per tenant (defend cascade retries).

OPA Policy Inputs (Enhanced):
```
{
  estimated_cost: <float>,
  approved_amount: <float>,
  age_seconds: <int>,
  stale: <bool>,
  drift_percent?: <float>,
  capsule_profile: <string>,
  region: <string>,
  provider: <string>,
  availability: <string>
}
```

Rollout Plan (Weeks 1–4):
- Week 1: Client + live endpoint + Redis cache + metrics base.
- Week 2: Reconcile endpoint + drift policies + BuildRun storage integration.
- Week 3: KPI enrichment (optional cost-per-token) + advanced alerts + chaos tests (forced upstream delay).
- Week 4: Hardening (circuit breakers, backpressure, provider preference profiles) + final docs & runbooks.

Testing Strategy:
- Golden snapshot tests for representative profiles (A100, 4090, V100 training).
- Simulated drift test (manually altered `price_per_hour`).
- Timeout injection test (proxy delaying upstream responses). 
- Stale fallback test (disable upstream, rely on LKG, `stale=true`).

Open Questions:
- Currency conversion needed? (Assume USD only for now.)
- Minimum availability threshold? (Default allow all; warn if `<"low">`).
- Provider weighting strategy phase? (Cheapest-first vs reliability score weighting – defer to KPI integration week 3.)

Risks:
- Upstream burst causing rate-limit: Mitigate with per-tenant caching & backoff.
- Inconsistent tags taxonomy: Normalize or treat tags as hints until standardization.
- Large pagination sets: Cap `per_page` to 100 and consider multi-page aggregation only if offers < required minimum.


---

## 17. Payments & Entitlements

Stripe-first implementation with idempotent webhooks and entitlement resolver.

APIs:
- `POST /v1/billing/checkout` → `{ checkout_url, session_id }`
- `POST /v1/billing/webhook/{stripe|paypal}`
- `GET  /v1/billing/entitlements` → current quotas/features

Data model (minimal): `customers, subscriptions, entitlements, usage, payments`.

Flow:
1) Estimate → compare to entitlements
2) If insufficient → checkout → webhook updates entitlements
3) Wizard resumes; OPA re-check; proceed

OPA examples:
- Deny execution if `estimated_total > budget_cap`.
- Deny if `security_class == critical` and plan ≠ Enterprise.

---

## 18. Marketplace Lifecycle (Deferred Scope, Canonical Design)

Responsibilities:
- Catalog/search/versioning/channels; publish/promote/install/rollback; provenance and scans; billing entitlements for paid capsules.

Draft APIs:
- `GET  /v1/marketplace/capsules[?query=&tag=&channel=]`
- `GET  /v1/marketplace/capsules/{id}` (+ `/versions`)
- `POST /v1/marketplace/capsules` (publish draft)
- `POST /v1/marketplace/capsules/{id}/promote`
- `POST /v1/marketplace/capsules/{id}/install`
- `POST /v1/marketplace/capsules/{id}/purchase`

Security:
- Signature verification, SBOM gate, vuln scans, OPA promotion/install policies.

Channels:
- `dev → beta → stable` promotion rules (no critical CVEs; signed artifacts; policy pass; install success rate thresholds).

---

## 19. Runtime Customization (Post-Deploy, No Rebuilds)

Principles:
- Static installs first (prebuilt images, Helm values); then apply lightweight runtime config (branding/flags) via ConfigMaps/Secrets and hot-reload endpoints.

Flow:
1) Namespace + NetworkPolicy
2) Secrets injection (Vault → K8s)
3) Helm installs (backend, frontend, worker)
4) Config patcher applies branding and feature toggles
5) Migrations/tests → rollback on failure

---

## 20. Capsule: Taxi‑Hailing Clone v10 (Install‑Ready Example)

Metadata:
- `id: taxi-hailing-clone-v10`, `version: 10.0.x`, `channel: stable`, `requires_payment: true`, `security_class: standard`

Images:
- `internal-registry/taxi-backend:v10`, `taxi-frontend:v10`, `taxi-dispatcher:v10`

Variables:
- `tenant_id, region, base_domain, brand_name, brand_color, logo_url, payment_provider, analytics_on`

Steps (ordered):
1) Preflight (entitlements/region/capacity)
2) Cost estimate → payment reconciliation
3) Namespace + NetworkPolicy
4) Vault secrets → K8s
5) Helm deploy backend/frontend/worker
6) Branding patcher
7) Optional modules toggling
8) DB migrations
9) Smoke tests → rollback on failure
10) Observability wiring
11) Result persistence (BuildRun + artifacts + receipt)

Outputs:
- `app_url, admin_url, api_url, grafana_url, receipt, run_log.json, build_manifest.json`

---

## 21. Module-by-Module Implementation Plan

Per service/module, current status → detailed implementation → acceptance.

1) Gateway API
- Current: Health, routing, partial pricing integration.
- Implement: Wizard endpoints; budget precheck; payment approval flow; BuildRun fetch.
- APIs: `/v1/wizard/*`, `/v1/build/{id}`.
- Acceptance: End-to-end approval→build trigger works; policy denials surfaced with reasons.

2) Orchestrator (Temporal)
- Current: Workflow scaffolds; capsule executor integration.
- Implement: `build_workflow` with activities (`fetch_pricing`, `opa_budget_check`, `copy_templates`, `spawn_agent`, `docker_build`, `helm_deploy`, `persist_result`), signals for approve/cancel.
- Acceptance: Minimal build < 5 minutes; compensation on failures; traces end-to-end.

3) Pricing Service
- Current: Live estimate endpoints and snapshots.
- Implement: GPUBROKER client; reconciliation step; drift metrics; provider adapters.
- Acceptance: p50 < 200ms; drift handling with re-accept policy.

4) Policy Engine (OPA)
- Current: Basic allow rules.
- Implement: Budget cap, max agents per user, feature/plan checks, capacity, stale pricing guards; bundle versioning and tests.
- Acceptance: Golden tests pass; denial reasons attached to responses.

5) LLM Hub
- Current: Minimal endpoints.
- Implement: Catalog (RBAC), adapters (OpenAI, Local; then Anthropic/Azure/Ollama), quotas, safety/residency, fallback chains, circuit breakers; usage events.
- Acceptance: Orchestrator/memory-gateway use Hub exclusively; quotas enforced; fallbacks observable.

6) Capsule Repos & Marketplace
- Current: Capsule-repo and Task-capsule-repo implemented.
- Implement: Canonicalize schema; add metadata extensions (requires_payment, entitlements, security_class, estimated_cost_formula, rollback, channel); prepare for deferred marketplace APIs.
- Acceptance: Orchestrator fetches manifests with extended fields; integrity/attestation checks.

7) Agent Spawner
- Current: Missing.
- Implement: `POST /v1/spawn` → K8s Job/Deployment with concurrency quotas; spawn metrics.
- Acceptance: ≥20 concurrent spawns; policy gate on max agents; outputs consumed by workflow.

8) Static Templates
- Current: Partial bundles.
- Implement: `services/static-templates/` for FastAPI/React/Helm/CICD; variable substitution; bundle hashing.
- Acceptance: Sample build produces source zip + Helm chart with verified hash.

9) BuildRun Persistence
- Current: Partial artifacts.
- Implement: Authoritative model (see section 4); `/v1/build/result` persistence; deletion (GDPR) flow.
- Acceptance: Artifact URLs + receipt retrievable; delete purges object store and marks record.

10) Object Store
- Current: Client + uploads.
- Implement: Size limits, lifecycle policy, integrity verification.
- Acceptance: Oversized artifacts rejected; SHA mismatch blocks persist.

11) Identity & Auth
- Current: Basic auth.
- Implement: Tenant-aware RBAC for wizard/build/pricing; service-to-service mTLS + JWT propagation.
- Acceptance: Role-limited model catalog; cross-service auth verified under mesh.

12) Memory Gateway
- Current: Vector + KV.
- Implement: Embeddings via LLM Hub; TTL policies; audit logging for reads/writes.
- Acceptance: Consistent embeddings source; access logs with tenant context.

13) Observability
- Current: Base metrics/logging.
- Implement: Metrics and alerts (section 7); trace sampling; dashboards and runbooks.
- Acceptance: SLOs visible; alerts firing in dev; chaos recovery documented.

14) Security
- Current: Partial.
- Implement: Mesh mTLS; Vault secrets; SBOM + Trivy; policy audit exports; cleanup controllers and retention.
- Acceptance: All inter-service traffic via mesh; CI blocks HIGH CVEs; rotation tests pass.

---

## 22. Validation Scenarios

- Marketing L1: returns posts/ad image/brief; payment gated by budget.
- Bazaar Chatbot: composite capsule; WordPress plugin; checkout if plan insufficient.
- Accounting (Ecuador): conditional SRI + Payroll; forecast vs plan; compliance via OPA.

---

## 23. Helm/Config Additions

Values:
- `services.gatewayApi.billing.enabled: true`
- `billing.provider: stripe|paypal`
- `billing.currency: USD`
- `billing.stripe.secretKey`, `billing.stripe.webhookSecret`, `billing.stripe.priceIds`
- `billing.paypal.clientId`, `billing.paypal.secret`
- `featureFlags.requirePaymentOnOverage: true`

Kubernetes:
- Secrets mounted to Gateway API and Marketplace
- NetworkPolicies for webhook ingress

---

## 24. Consolidation & Maintenance

- This is the single canonical roadmap. All other roadmap documents have been removed.
- Update the “Repo Gap Summary” quarterly; keep acceptance criteria current.
- Cross-link changes in `ARCHITECTURE.md` and `docs/specs/` when schemas evolve.

### 24.1 Document Hygiene (Enforced)
- Prohibit reintroduction of standalone roadmap markdowns (`roadmap-*.md`).
- Archive any large deprecated strategy docs under `docs/archive/` with date stamp.
- Reference pillar alignment in future PR descriptions (template to be added in developer docs section).
