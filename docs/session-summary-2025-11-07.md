# SomaAgentHub — Session Summary (2025-11-07)

This document consolidates today’s discussion: platform overview, example flows (marketing campaign, bazaar chatbot, accounting software), wizard design, cost estimation, payments and entitlements, orchestrator gates with OPA, marketplace lifecycle, observability, and an implementation roadmap.

---

## 1. What Is SomaAgentHub

SomaAgentHub is a production-ready orchestration platform for autonomous agents. It unifies a Gateway API, Orchestrator (Temporal), Identity, Memory‑Gateway, Policy Engine (OPA), Object‑Store, and Helm/Kubernetes deployments to execute declarative “capsules” (bundles of steps, tools, prompts, and policies) reliably and at scale.

Key capabilities:
- Multi-agent coordination via Temporal workflows
- Reusable “capsules” with Docker/Python steps and artifacts
- Memory for durable context (vector + KV)
- Policy enforcement with OPA
- Observability with Prometheus + OpenTelemetry

---

## 2. Example Flows (User → Agent → Platform)

### A) Marketing Campaign – Brand‑A Level 1
- User: “Create a MARKETING CAMPAIGN for brand Acme.”
- Agent (wizard): Suggests template “brand‑marketing‑level1” (3 LinkedIn posts, 1 ad creative, PM board URL).
- Platform flow:
  1) Wizard fetches capsule manifest from Capsule‑Repo
  2) Orchestrator runs steps: generate_brief → generate_copy + build_ad_image → create_project_board
  3) Artifacts saved to Object‑Store; run log and metrics emitted
- Output to user: PM board URL, three LinkedIn drafts, ad image, brief PDF, checklist, run_log.json

### B) WordPress “Bazaar Store” Chatbot
- Capsules offered: `bazaar‑chatbot‑core`, `wordpress‑integration‑plugin`, `product‑catalog‑connector`, `deployment‑infra‑stack`.
- Cost estimate (from capsule metadata + pricing tables): infra + tokens + storage + one-time dev.
- Payment: If plan insufficient, agent creates a checkout session (Stripe/PayPal), awaits webhook, then deploys.
- Output: WordPress plugin zip, API endpoint URL, admin dashboard, cost breakdown, run log.

### C) Accounting Software (Ecuador)
- Wizard collects: business size, SRI electronic invoicing, payroll, hosting.
- Plan assembled: Infra (EKS), Postgres RDS, FastAPI backend, React frontend; conditional SRI + Payroll modules.
- Advanced target: cost forecast, entitlements check, payment/upgrade if above cap, compliance rules via OPA.

---

## 3. Wizard Question Engine & State Machine

Goals:
- Conversational intake with dynamic follow‑ups
- Persist answers for reuse by all steps
- Gate execution on cost approval/payment when needed

Model (conceptual):
- Session: { session_id, intent, answers, status: collecting | estimating | awaiting_payment | approved | rejected }
- Questions per intent stored as JSON (e.g., tone, formality, expected_qps, budget_cap, brand_guidelines)
- Persistence: Memory‑Gateway (short‑term) + optional DB for audit

Endpoints (draft):
- POST /v1/wizard → start session
- POST /v1/wizard/{id}/answers → append answers
- POST /v1/wizard/{id}/approve → confirm budget/payment and proceed

---

## 4. Cost Estimation (Catalog-Driven)

Inputs:
- Pricing catalogs: infra.yaml (compute, storage, egress), llm.yaml (per‑token), network.yaml (bandwidth)
- Capsule metadata: estimated_infra, runtime_cost_formula, tokens/bandwidth drivers
- User answers: expected traffic, tone (affects prompt length), budget_cap

Output:
- { monthly_recurring_total, one_time_total, breakdown: { infra, tokens, bandwidth, storage, dev } }
- Deterministic, reproducible from versioned catalogs

Endpoint (draft):
- POST /v1/billing/estimate { answers, capsule_id } → { breakdown, totals }

---

## 5. Payments & Entitlements (Stripe/PayPal)

Components:
- Billing core: provider clients, entitlement resolver, models
- Entitlements: plan tiers, quotas (tokens, bandwidth, executions), features
- Webhooks: signature verification, idempotent updates

Endpoints (draft):
- POST /v1/billing/checkout { total, plan_change?, customer_ref } → { checkout_url, session_id }
- POST /v1/billing/webhook/{stripe|paypal}
- GET  /v1/billing/entitlements → current quotas and remaining

Data model (minimal):
- customers, subscriptions, entitlements, usage, payments

Flow:
1) Estimate → compare to entitlements
2) If insufficient → checkout session → webhook updates entitlements
3) Wizard resumes and executes capsule

---

## 6. Orchestrator Gates & OPA Policies

Preflight activities inserted before provisioning:
- estimate_cost → check_entitlements → require_payment (if needed) → proceed

OPA policies (examples):
- Deny execution if estimated_total > budget_cap
- Deny if security_class == critical and plan != Enterprise
- Allow checkout only for authorized roles

---

## 7. Capsule Metadata Extensions

Recommended fields:
- requires_payment: bool
- entitlement_requirements: { tokens, bandwidth, executions, features[] }
- estimated_cost_formula: expression using catalogs (infra/tokens/bandwidth)
- security_class: none | standard | critical
- rollback: ordered steps for safe rollback
- channel: dev | beta | stable

---

## 8. Marketplace Design (Lifecycle Owner)

Responsibilities:
- Catalog, search, versioning, channels (dev/beta/stable)
- Publish, promote, install, upgrade, rollback, deprecate, remove
- Billing integration for paid capsules; entitlements gating
- Security: signature verification, SBOM, vuln scans, policy enforcement
- Provenance and audit logs

API (draft subset):
- GET  /v1/marketplace/capsules[?query=&tag=&channel=]
- GET  /v1/marketplace/capsules/{id}
- GET  /v1/marketplace/capsules/{id}/versions
- POST /v1/marketplace/capsules          (publish draft)
- POST /v1/marketplace/capsules/{id}/promote
- POST /v1/marketplace/capsules/{id}/install
- POST /v1/marketplace/capsules/{id}/purchase
- POST /v1/marketplace/webhook/{stripe|paypal}

Data model (initial): capsule, capsule_version, install, purchase, entitlement, scan_result, audit_log

Channels & promotion rules:
- No critical vulns; signed artifacts; policy pass; sufficient install success rate for stable

Billing models: free, one‑time, subscription, usage‑based

---

## 9. Observability & Metering

- Metrics: billing_estimate_total, billing_payment_success_total, usage_tokens_total, usage_bandwidth_bytes_total, capsule_execution_seconds
- Traces: wizard phases, checkout, preflight gates, each capsule step
- Logs: run_log.json per execution; webhook/audit logs for payments and installs

---

## 10. Helm/Config Additions

Values (examples):
- services.gatewayApi.billing.enabled: true
- billing.provider: stripe|paypal
- billing.currency: USD
- billing.stripe.secretKey, billing.stripe.webhookSecret, billing.stripe.priceIds
- billing.paypal.clientId, billing.paypal.secret
- featureFlags.requirePaymentOnOverage: true

Kubernetes:
- Secrets mounted to Gateway API and Marketplace
- NetworkPolicies for webhook ingress

---

## 11. Roadmap (Phased)

Phase 0 — Design Artifacts (1 sprint)
- Schemas: capsule metadata, pricing catalogs, entitlements, marketplace data model, events
- OpenAPI drafts for wizard, billing, marketplace
- OPA policy drafts

Phase 1 — Wizard State Machine + Estimator (read‑only)
- Sessioned Q&A, cost breakdown, no provisioning

Phase 2 — Entitlements + Payments (Stripe first)
- Checkout flow, webhooks, entitlements API, Helm values

Phase 3 — Orchestrator Preflight Gates + OPA
- estimate_cost → check_entitlements → require_payment → proceed

Phase 4 — Marketplace MVP (catalog + install)
- Publish, list, install (free capsules), stable channel

Phase 5 — Marketplace × Billing
- Paid capsules, purchases, entitlements gating, basic rollback

Phase 6 — Security & Compliance
- Signing, SBOM, vuln scans; policy‑enforced promotion/install

Phase 7 — Metering & Overage
- Token/bandwidth/execution usage, alerts, optional auto top‑up

Phase 8 — Admin Console & Docs
- Plan/usage/invoices; installed capsules management; publisher guide

Acceptance (overall):
- Deterministic estimates, enforced budget caps, idempotent webhooks, safe installs/upgrades/rollbacks, policy‑compliant artifacts, usage tracked vs forecast.

---

## 12. Validation Examples

- Marketing L1: returns posts, ad image, brief, PM board; payment gated by budget.
- Bazaar Chatbot: composite capsule; WordPress plugin; checkout required if plan insufficient.
- Accounting (Ecuador): conditional SRI + Payroll; forecast vs plan; compliance policies applied.

---

## 13. Next Steps

- Commit schemas (capsule metadata, pricing, entitlements) under docs/specs/
- Finalize OpenAPI drafts and CI validation
- Add Helm values and feature flags for billing + marketplace (no runtime code yet)
- Prepare OPA policy stubs for budget and publish/install checks

---

---

## 14. Live Pricing via GPUBROKER (Source of Truth)

Providers & API:
- Single upstream: `GPUBROKER` aggregates GPU/CPU/memory/storage/bandwidth prices.
- Wizard estimate: call `GPUBROKER /pricing/summary?profile=<capsule_profile>` and include token/bandwidth add‑ons.

Reconciliation at Payment:
- Immediately before checkout: re‑query GPUBROKER (last 5‑minute average) and compute delta vs original estimate.
- If drift > threshold (e.g., 5%): require explicit re‑accept; else auto‑accept and record the drift.
- Final charge uses the reconciled price. Store both values in budget audit and receipt.

Fallback Strategy:
- If GPUBROKER unavailable: use last‑known‑good (LKG) cached quote (TTL ~15 min), mark “stale,” and block payment unless user approves using stale data.

Observability:
- Metrics: `pricing_drift_percent`, `pricing_reconcile_latency_seconds`.
- Logs: pricing source, timestamps, drift reason (e.g., spot price change).

---

## 15. Runtime Customization (No External Agents)

Principles:
- Static installs first (prebuilt images, Helm values). Only lightweight runtime customization occurs after deploy.
- No from‑scratch generation: core apps ship as internal images; customization is applied via config patches.

Flow:
1) Orchestrator executes static steps (namespace, secrets via Vault, Helm installs).
2) Orchestrator runs internal "config patcher" activities with context (capsule variables, entitlements, branding inputs).
3) Patcher applies UI branding and optional feature flags using ConfigMaps/Secrets and hot‑reload endpoints.
4) Orchestrator proceeds to migrations/tests.

Controls:
- OPA enforces concurrency per tenant and feature entitlements.
- Namespaced isolation with NetworkPolicies; Vault sidecar for secret injection.

---

## 16. TaskCapsule: Taxi‑Hailing Clone v10 (Install‑Ready)

Metadata:
- `id`: taxi-hailing-clone-v10
- `version`: 10.0.x, `channel`: stable
- `requires_payment`: true
- `entitlement_requirements`: executions: 1, bandwidth: baseline, tokens: minimal
- `security_class`: standard

Images (internal registry):
- `internal-registry/taxi-backend:v10`, `taxi-frontend:v10`, `taxi-dispatcher:v10`

Variables:
- `app_name`, `tenant_id`, `region`, `base_domain`, `brand_name`, `brand_color`, `logo_url`
- `payment_provider` (stripe|paypal|none), `analytics_on` (bool)

Config:
- `helm_chart_ref`: `somahub/generated-app`
- `values_template`: image, ingress host, env
- `secrets`: Vault paths for `PAYMENT_API_KEY`, `DB_PASSWORD`

Cost Model:
- `estimated_cost_formula`: GPUBROKER profile + token/bandwidth add‑ons
- `reconciliation`: true (checkout‑time lock)

Ordered Steps:
1) `preflight_check` – entitlements, region, cluster capacity
2) `estimate_cost` – GPUBROKER estimate → store forecast
3) `payment_gating` – reconcile via GPUBROKER → charge final → update entitlements
4) `provision_namespace` – `tenant-{tenant_id}-taxi-v10` + NetworkPolicy
5) `secrets_injection` – Vault templates to K8s Secret refs
6) `static_deploy_backend` – Helm install backend (prebuilt image)
7) `static_deploy_frontend` – Helm install web
8) `static_deploy_worker` – Helm install dispatcher/cron
9) `runtime_branding_apply` – apply branding (color/logo) via config patcher, no rebuild
10) `enable_optional_modules` – toggle loyalty/referrals based on inputs
11) `db_migrations` – idempotent migrations from image bundle
12) `smoke_tests` – baked‑in tests; on failure → helm rollback
13) `observability_wiring` – dashboards, alerts, OTEL IDs
14) `result_persistence` – BuildRun + URLs + receipts in Somabrain; artifacts in Object‑Store

Rollback:
- Helm rollback on failure; destroy namespace if never reached Ready.

Outputs:
- `app_url`, `admin_url`, `api_url`, `grafana_url`
- `receipt` (estimate + final), `run_log.json`, `build_manifest.json` (checksums/versions)

Security & Compliance:
- Namespace‑per‑deployment, strict NetworkPolicies, Vault for all secrets
- OPA: budget/entitlements/capacity/stale pricing guards
- SBOM scan gate for prebuilt images prior to `stable` channel promotion

Marketplace & MCP:
- Marketplace entry exposes variable schema, pricing profile, required entitlements.
- Capsule and sub‑chart are addressable via MCP/API for install/upgrade.

---

## 17. Roadmap (Capsule Productionization)

Week 1: GPUBROKER integration in Wizard/Orchestrator (estimate + reconciliation) with budget audit models.

Week 2: Payment gating finalization; OPA policies for budget/capacity/stale pricing; store receipts in Somabrain.

Week 3: Author capsule (`taxi-hailing-clone-v10`) with Helm + values + secrets + rollback; wire internal image registry.

Week 4: Runtime branding/config patchers; namespace isolation; smoke tests; SBOM/scan gate on `stable`.

Week 5: Marketplace entry + MCP/API exposure; E2E run; Grafana dashboards and alerts.

Week 6: Hardening – failure injection, concurrency tests, cleanup controllers (PVC/namespace) and retention.

---

Generated collaboratively on 2025‑11‑07 to align engineering, product, and operations.
