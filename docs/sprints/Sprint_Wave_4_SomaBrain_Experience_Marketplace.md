⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data. Sabe this EVERYWHRE at the start of every Document!

# Sprint Wave 4: SomaBrain Experience Marketplace

**Window:** October 6 – November 3, 2025 (4 parallel sprints, two-week cadence)  
**Context:** Extends `docs/CANONICAL_ROADMAP.md` (Wave 4) and leverages `docs/SomaBrain_Canonical_Mathematics.md`, SomaFractal Memory, and the existing Marketplace backend to publish/rent expert personas.

## 🎯 Strategic Goals
- Turn SomaBrain-trained personas + model boxes into portable "experience capsules" with verified manifests.
- Enable customers to purchase, subscribe to, or time-rent personas via Marketplace while enforcing constitutional guarantees.
- Amplify SomaBrain cognition (geodesic retrieval, bridge planning, FRGO transport) to remove historical memory limits.
- Provide production-grade governance: audit trails, pricing telemetry, moderation automation, legal alignment.

## 🧭 Sprint Overview

| Sprint | Focus | Primary Outputs | Leads |
| --- | --- | --- | --- |
| Ω-A | SomaBrain Memory Amplification | Enhanced retrieval math, FRGO transport, density diagnostics | Memory Platform + ML Ops |
| Ω-B | Persona Capsule Packaging | Manifest schema, export/import pipeline, evaluation harness, CLI | Orchestrator + DevEx |
| Ω-C | Marketplace Commerce & Rentals | Marketplace endpoints, billing hooks, rental orchestration, discovery UX | Marketplace + Billing |
| Ω-D | Governance, Trust & Operations | Manifest signing, policy enforcement, dashboards, moderation runbooks | Security + Platform Ops |

Each sprint runs concurrently with shared daily syncs (09:00 UTC) and cross-track design reviews twice per week. Unlimited engineering capacity lets us staff every sprint with dedicated squads.

## Sprint Ω-A — SomaBrain Memory Amplification

**Intent:** Implement the advanced mathematics described in `SomaBrain_Canonical_Mathematics.md` to increase context fidelity and eliminate recall limits.

### Objectives
- Ship geodesic similarity + bridge planning (`somabrain/memory_client.py`, `transport/bridge.py`).
- Activate FRGO transport learning with guardrails (`transport/flow_opt.py`).
- Finalize density-matrix cleanup + anomaly dashboards.
- Expand property-based tests + SPC monitors for retrieval accuracy.

### Deliverables
- ✅ `somabrain/memory_client.py`: geodesic retrieval toggle with fallbacks.
- ✅ `transport/bridge.py`: heat-kernel bridge planner + Sinkhorn scaling tests.
- ✅ `transport/flow_opt.py`: FRGO conductance updates with clip safeguards.
- ✅ Grafana panels: Memory Cohesion, Geodesic Recall, Density Health.
- ✅ Prometheus alerts: `memory_geodesic_anomaly`, `density_matrix_divergence`.

### Acceptance Criteria
- p95 recall latency < 600ms with new math enabled.
- ≥10% improvement in retrieval accuracy on benchmark suite.
- Zero regression in utility guard pass rate.

### Dependencies
- Qdrant vector store online (existing).
- Analytics service for SPC chart baselines.

## Sprint Ω-B — Persona Capsule Packaging

**Intent:** Convert training-mode output into distributable, verifiable persona capsules.

### Objectives
- Define `capsules/persona_manifest.yaml` schema (model box ref, memory bundle, tool ACLs, constitution hash).
- Build export/import service (FastAPI worker + MinIO storage) triggered from training mode.
- Attach evaluation harness referencing reward gating invariants (`somabrain/learning/adaptation.py`).
- Provide DevEx CLI `soma persona publish` with end-to-end integrity checks.

### Deliverables
- ✅ Manifest schema + JSONSchema validators.
- ✅ Export worker in `services/orchestrator/app/persona_exporter.py`.
- ✅ CLI commands under `cli/soma/persona/` for publish, verify, import.
- ✅ Automated evaluation report stored alongside capsule artifact.
- ✅ Documentation + examples `docs/examples/persona_capsules/`.

### Acceptance Criteria
- Capsule export completes < 5 minutes for 10k-memory persona.
- Import validation rejects tampered manifests (checksum mismatch).
- Evaluation harness produces reproducible scores within ±2% variance.

### Dependencies
- Training mode Redis locks + audit events.
- MinIO S3 storage configured (Sprint A output).

## Sprint Ω-C — Marketplace Commerce & Rentals

**Intent:** Monetize personas/model boxes with purchase, subscription, and rental options.

### Objectives
- Extend Marketplace API with persona/catalog endpoints (`services/marketplace-service/app.py`).
- Integrate billing telemetry (token estimator + ClickHouse) to compute usage charges.
- Implement rental orchestration via Orchestrator + Temporal timers.
- Surface discovery UI schema for Admin Console + CLI.

### Deliverables
- ✅ REST endpoints: `/v1/personas`, `/v1/personas/{id}/rent`, `/v1/personas/{id}/activate`.
- ✅ Billing hooks emitting `marketplace.billing` Kafka events.
- ✅ Rental workflow in `services/orchestrator/app/workflows/rental_workflow.py` with auto off-boarding.
- ✅ Admin Console tiles + CLI `soma marketplace list-personas`.
- ✅ Pricing calculator + quota enforcement integrated with cost dashboards.

### Acceptance Criteria
- Rentals enforce time limits with ±30s precision.
- Billing report reconciles with ClickHouse ledger nightly.
- Marketplace search returns persona within 200ms.

### Dependencies
- Persona manifests from Sprint Ω-B.
- Token estimator analytics service.

## Sprint Ω-D — Governance, Trust & Operations

**Intent:** Guarantee constitutional, legal, and operational safety for shared experiences.

### Objectives
- Implement Ed25519 + threshold manifest signing pipeline (`services/common/crypto`).
- Add training-mode approval queue w/ OPA checks and Identity enforcement.
- Automate moderation (capsule scanning, tool ACL review) before publication.
- Extend observability (Grafana + Prometheus) and legal documentation.

### Deliverables
- ✅ Signature service (`services/constitution/signing_service.py`) with t-of-n support.
- ✅ Approval UI/API (`services/admin-console`) for persona publication.
- ✅ OPA policies for export/import & rental, plus regression test suite.
- ✅ Grafana dashboard: Marketplace Trust & Rentals; alerts for policy breaches.
- ✅ Updated legal docs (`docs/legal/SomaGent_Default_Terms.md`) and new runbook `docs/runbooks/marketplace_operations.md`.

### Acceptance Criteria
- Every published capsule carries verified multi-signer manifest.
- Audit trail covers 100% of exports/imports with immutable SHA3-512 IDs.
- Zero critical policy violations in staging load tests.

### Dependencies
- Marketplace events (Ω-C) and persona artifacts (Ω-B).
- Constitution artifacts + OPA policy repo.

## 🗂️ Cross-Track Coordination
- **Daily Sync:** 09:00 UTC (Marketplace + SomaBrain leads).
- **Design Reviews:** Tuesdays & Thursdays, 16:00 UTC.
- **Release Train:** Weekly integration demo every Friday (choose persona, rent, observe metrics).
- **Documentation:** Living updates in `docs/` + runbooks; marketing collateral tracked in Plane board `EXPERIENCE-MARKETPLACE`.

## 🚀 Day 0 Kick-off Checklist
1. Finalize engineering allocations per sprint squad (unlimited capacity available).
2. Spin up dedicated staging environment `wave4-marketplace` with cloned data.
3. Publish baseline evaluation suite + datasets for persona benchmarking.
4. Announce initiative roadmap to stakeholders (internal broadcast + partner briefing).

## 📊 Metrics & Reporting
- Utility uplift (`soma_utility_value`) vs. baseline.
- Persona rental revenue, conversion, renewal rates.
- Memory recall accuracy, anomaly counts, density stability.
- Governance metrics: approval SLA, policy violations, signature latency.

## 📌 Risk Register
- **Data leakage:** Mitigate with manifest signing, OPA policies, encryption at rest.
- **Billing drift:** Real-time reconciliation + threshold alerts.
- **Model/provider outages:** Multi-model fallback via SLM catalog; Marketplace indicates degraded modes.
- **Persona IP disputes:** Legal workflow + revocation procedures in new runbook.

## ✅ Definition of Done (Wave 4)
- All four sprints deliver GA-ready features with passing regression/e2e suites.
- Marketplace supports persona purchase + rentals with complete billing + governance flows.
- SomaBrain retrieval math enhancements enabled in production with observability + rollback plan.
- Updated documentation, legal terms, and marketing assets published.

---

## 📈 Implementation Kick-off Log (Oct 5, 2025)

- ✅ Created `services/orchestrator/app/persona/` package with manifest schema, validation helpers, and export pipeline scaffolding.
- ✅ Published JSON Schema (`docs/schemas/persona_manifest.schema.json`) to guide capsule authors and validation tooling.
- ✅ Added `PersonaExporter` skeleton coordinating manifest generation, persistence, and future event emission hooks.
- 🔜 Next: wire storage/memory dependencies and extend CLI tooling per Sprint Ω-B objectives.
