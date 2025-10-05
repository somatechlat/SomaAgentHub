⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data. Sabe this EVERYWHRE at the start of every Document!

---
title: Sprint 4 - Experience & Ecosystem (Weeks 3-4)
owner: Experience Platform Crew
start_date: 2025-10-04
end_date: 2025-10-18
---

# Sprint 4 — Experience & Ecosystem

Goal: Stand up the first admin console slice and marketplace scaffolding so operators can configure models, view token forecasts, and prepare capsule listings.

Top-level acceptance criteria:
- Admin Console (React + Tailwind) boots locally with Overview, Models & Providers, and Marketplace tabs wired to live APIs.
- Token Estimator service delivers baseline demand forecasts per provider and exposes `/v1/forecast` consumed by the UI.
- Marketplace service persists capsule metadata with attestation hashes and exposes `/v1/catalog/list` for the UI.
- Documentation updates walk operators through configuring model profiles and reviewing forecasts.

Tasks
- [ ] Scaffold admin console app with routing, layout shell, and shared design system tokens.
- [ ] Implement Models & Providers tab: list profiles from Settings service, allow switching primary provider, display token forecasts.
- [ ] Create Marketplace tab: list capsules from backend, show compliance badge + token estimate summary.
- [ ] Build Token Estimator FastAPI service with heuristics using historical `slm.metrics` data; add Prometheus metrics for prediction latency and MAPE.
- [ ] Extend Marketplace backend schema for attestation hash, reviewer workflow state, and compliance notes.
- [ ] Update operator documentation in `docs/Quickstart.md` and `docs/development/Implementation_Roadmap.md` with new UI flows.

Notes
- Coordinate with Analytics team to access `slm.metrics` history for estimator inputs.
- Ensure console integrates with SomaGent authentication (reuse Identity tokens from Sprint 2).
- Target responsive layout so the console works on tablets for field operators.

## Parallel Coordination
- **Wave Alignment:** Sprint-4 launches as Wave B while Sprint-2 and Sprint-3 finish Wave A deliverables. Design wave stays +1 sprint ahead with component specs in `docs/design/`.
- **Integration Day Objectives:** Consume real policy headers and streaming responses produced by Sprint-2/Sprint-3; demo admin console wired to live settings + forecast APIs.
- **Shared Dependencies:** Identity tokens from Sprint-2, streaming endpoints from Sprint-3, analytics metrics from SLM Execution squad.
- **Upstream Hand-offs Needed:** Recorded API contracts (`scripts/parallel/record_contracts.py`) from backend squads, notification feed topics from Infra crew, and capability taxonomy finalized by Identity & Settings.
