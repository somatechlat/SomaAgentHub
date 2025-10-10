# Canonical Roadmap (Dedup + Architecture Fix Plan)

Truth-first roadmap to reduce redundancy and correct architecture issues with real code, real services, and reproducible deployments. Work streams run in parallel; each item includes concrete deliverables and pass/fail acceptance criteria.

Last Updated: October 9, 2025

## Scope guardrails
- No mocks in critical paths; tests run against real services in-cluster (Kind).
- Helm is the source of truth for deploy wiring; gateway, orchestrator, policy, identity, slm are core and enabled by default.
- Observability and health/ready endpoints are consistent across services.

---

## Sprint 1 (1 week, parallel tracks): Standardize and Prove

Track A: Central Observability (dedupe x6)
- Deliverables:
	- services/common/observability.py with standardized init (Prometheus, optional OTEL), consistent labels: service.name, service.version, env.
	- Replace app/observability.py in gateway-api, orchestrator, policy-engine, identity-service, slm-service, analytics-service.
	- /health, /ready helpers unified semantics. /metrics remains Prometheus text.
- Acceptance:
	- All 6 services boot with common init; /metrics exposes counters/histograms; dashboards show data for each.

Track B: Unified Redis Client (phase 1)
- Deliverables:
	- Upgrade services/common/redis_client.py with pooled async client, basic retries, metric hooks.
	- Migrate policy-engine and constitution-service to shared client (remove per-service wrappers).
- Acceptance:
	- Both services pass health, and integration flows that touch Redis succeed in-cluster without code duplication.

Track C: Helm ergonomics + Secrets
- Deliverables:
	- values.yaml: core services ON by default; non-core OFF; envFrom pattern documented and optional.
	- Identity JWT secret via env/envFrom; maintain dev default for local runs.
- Acceptance:
	- helm upgrade --install completes cleanly; pods Ready; secret wiring verified with a minimal token issue call.

Track D: E2E + Perf Smoke (gates)
- Deliverables:
	- E2E happy path: gateway → orchestrator → policy allow → slm; schema and metrics assertions.
	- Perf smoke: 2–3 min, P95 < 500ms, error < 1% on SLM basic inference path.
- Acceptance:
	- CI job runs both; failure breaks the build.

---

## Sprint 2 (1 week, parallel): Consolidate and Simplify

Track A: Identity + Gateway Redis migration
- Deliverables:
	- Migrate identity-service and gateway-api to shared Redis client. Remove bespoke client code and redundant helpers.
- Acceptance:
	- Health endpoints pass; JWT issuance/validation flows pass; no service-specific Redis code remains.

Track B: Base Dockerfile
- Deliverables:
	- Dockerfile.base: python:3.13-slim, uvicorn entrypoint that respects $PORT.
	- Convert gateway, orchestrator, slm, policy, identity to inherit base; unify EXPOSE and PORT.
- Acceptance:
	- Images build faster and run identically; helm upgrade works; probes stay green.

Track C: Temporal hygiene
- Deliverables:
	- Single worker entry for orchestrator with dev/prod flags; TEMPORAL_ENABLED stays as the local gate.
	- Audit mao-service Temporal usage; decision: consolidate into orchestrator or keep with a clear boundary (doc + value prop).
- Acceptance:
	- Worker runs with one entrypoint; if consolidated, mao-service Temporal code removed and functionality present in orchestrator.

Track D: Dashboards + Alerts
- Deliverables:
	- Minimal Grafana dashboard JSON: latency, RPS, error rate for gateway/slm/orchestrator; service_healthy gauges.
	- Basic alerts (error rate, readiness flaps) documented and optionally enabled.
- Acceptance:
	- Panels render with live data from local Prometheus; alert rules validated in dry-run.

---

## Sprint 3 (1 week, parallel): Reduce Surface Area

Track A: Service consolidation
- Deliverables:
	- Merge memory-gateway capabilities into recall-service (or retire one) with redirects and docs.
	- Fold constitution-service cache helpers into policy-engine or a shared lib and background task.
- Acceptance:
	- Helm values updated; removed service not deployed by default; dependent flows still pass E2E.

Track B: Config unification
- Deliverables:
	- services/common/settings.py with Pydantic BaseSettings helpers, standard prefixes, URL/duration parsing.
	- Migrate core services to shared settings (gateway, orchestrator, policy, identity, slm).
- Acceptance:
	- Env parity proven via snapshot tests; services boot with identical env names across environments.

Track C: Autoscaling & Limits
- Deliverables:
	- Resource requests/limits and HPA for gateway + slm; simple load test scaling demo.
- Acceptance:
	- HPA scales pods under load; error budget maintained; perf smoke still green.

---

## Sprint 4 (1 week, parallel): Production Hardening

Track A: Ingress + TLS
- Deliverables:
	- NGINX Ingress + cert-manager; TLS termination for gateway; path rules for core APIs.
- Acceptance:
	- HTTPS endpoints healthy; no breakage in probes or E2E.

Track B: Security gates
- Deliverables:
	- SBOM, image scanning, dependency audits, OpenAPI auth checks in CI.
- Acceptance:
	- CI fails on critical vulnerabilities or auth drift.

Track C: SLOs + Runbooks
- Deliverables:
	- Documented SLOs (latency, availability, error rate); runbooks for outages, Redis failure, Temporal downtime.
- Acceptance:
	- On-call simulation: follow runbook to restore green state in local env.

---

## Always-on quality bars
- Helm deploy must pass with --wait; pods Ready.
- /health and /ready consistent; metrics emitted; no broken dashboards.
- E2E and perf smoke gates are non-optional in CI.

## De-scoped or removed (pending decision)
- Duplicate orchestration: retire jobs service in favor of Temporal workers.
- Temporal duality: consolidate mao-service into orchestrator unless a strong, documented reason exists.
- Redundant memory and constitution services: fold responsibilities into recall-service and policy-engine or shared libs.

## Appendix: acceptance test cues
- Observability: /metrics exposes counters + histograms; Grafana panels non-empty during test.
- Redis client: integration that sets/gets keys via shared client passes; no per-service redis code remains.
- Docker base: all core images build from base; helm rollout unaffected; probes green.
- Temporal: worker starts via single entry; E2E path unaffected with TEMPORAL_ENABLED=false in dev.
