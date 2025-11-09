# SomaAgentHub Canonical Roadmap

> Single source of truth for strategic phases, rapid sprints, and deferred items. All previous roadmap documents have been removed and their content consolidated here. Temporal is the orchestrator. Marketplace (capsule distribution & Kong multi‑tenant edge) is explicitly deferred and scoped at the end.

## 1. Vision (Concise)
Deliver a production‑grade autonomous agent hub capable of:
1. Deterministic build/deploy flows for generated applications (Generic Build Workflow pattern; former “Taxi” example was illustrative only)
2. Policy‑gated execution (cost, quota, feature flags)
3. Transparent pricing & payment gating (live pricing → approval → workflow)
4. Secure, observable, auditable multi‑tenant runs
5. Extensible capsule system with future marketplace integration

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
