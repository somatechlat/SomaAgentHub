# Canonical Roadmap (Sprint Plan)

Guiding plan for upcoming work (subject to change). All milestones prioritize real instrumentation, reproducible deployments, and verifiable results.

Last Updated: October 9, 2025

## Sprint 1 (1 week): Test & Observability Foundations
- E2E happy-path test: gateway → orchestrator → policy allow → slm → result
	- Acceptance: 2 runs in CI; response schema validated; metrics increase observed.
- Performance smoke gate
	- 1–2 minute run; assert P95 < 500ms and error rate < 1% for SLM inference.
- ServiceMonitors for gateway + SLM; basic Grafana dashboard
	- Acceptance: dashboard panels show slm_infer_* and slm_embedding_* metrics.

## Sprint 2 (1 week): Reliability & Security
- Chaos automation (2 experiments)
	- pod kill gateway; 100ms network delay to SLM; assert error budget holds.
- Ingress + TLS (production-ready defaults)
	- Gateway exposed via Ingress; TLS termination; probes unaffected.
- OpenAPI schema checks and auth route tests
	- Acceptance: CI fails on schema drift or missing auth on protected routes.

## Sprint 3 (1 week): Scale & Data
- Expand Helm coverage: orchestrator, identity, policy
- Resource requests/limits and HPA for gateway + SLM
- Persistence baselines
	- PVC for SLM models; restart tests confirm fast readiness.

## Sprint 4 (1 week): CI/CD & Governance
- Release automation (tags, changelogs, SBOM)
- Security scanning gates
- SLO tracking and weekly reports
	- Error rate, availability, latency; exported to dashboards.

## Backlog
- Multi-region deployment guide
- Advanced chaos experiments (partitions, IO)
- Deeper analytics and marketplace features
