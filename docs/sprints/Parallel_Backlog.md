⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data. Sabe this EVERYWHRE at the start of every Document!

# Parallel Sprint Backlog — Wave A/B Kickoff (2025-10-04)

All Wave A and Wave B squads are live. This backlog consolidates top deliverables across Sprint-2 (Governance Core), Sprint-3 (Runtime & Training Slice), and Sprint-4 (Experience & Ecosystem). Status uses:
- 🟥 Not Started
- 🟧 In Progress
- 🟩 Complete

## Execution Grid

| Squad / Sprint | Epic | Key Tasks | Owner | Status |
| --- | --- | --- | --- | --- |
| Sprint-2 — Governance Core | Policy Engine | Finalize rule model + deterministic evaluator, emit `policy_decision_total` metrics | Policy Lead (Ada) | 🟧 In Progress |
| | Constitution Sync | Redis cache warmers, SomaBrain signature verification, Prometheus gauges | Memory Liaison (Ravi) | 🟥 Not Started |
| | Identity Enhancements | `/v1/tokens/issue` rotation hooks, `identity.audit` Kafka emission | Identity Anchor (Leah) | 🟧 In Progress |
| | Gateway Enforcement | Middleware enforcing policy headers + telemetry | Gateway Partner (Noah) | 🟥 Not Started |
| | Governance Runbook | Update `docs/runbooks/security.md` with rotation cadence + rollback | Security Guild (Mai) | 🟥 Not Started |
| Sprint-3 — Runtime & Training | Orchestrator Runtime | `/v1/conversation/step` + `/v1/conversation/stream`, SSE bridge, `conversation.events` | Runtime Lead (Kai) | 🟧 In Progress |
| | Training Mode Control | Redis-backed lock, admin enforcement, `training.audit` topic | Training Owner (Zara) | 🟥 Not Started |
| | Gateway Handshake | Streaming handshake, moderation integration, trace propagation | Gateway Partner (Noah) | 🟥 Not Started |
| | Observability | Metrics (`orchestrator_requests_total`, `training_mode_state`), structured logs | Observability Pod (Lina) | 🟥 Not Started |
| | Integration Tests | End-to-end chat flow with fakeredis + aiokafka fixtures | QA Owner (Milo) | 🟥 Not Started |
| Sprint-4 — Experience & Ecosystem | Admin Console Shell | Scaffold layout, routing, design tokens | Frontend Lead (Mira) | 🟥 Not Started |
| | Models & Providers Tab | Live settings API integration, token forecasts | UI Engineer (Theo) | 🟥 Not Started |
| | Marketplace Tab | Capsule list with compliance + token summaries | UI Engineer (Ava) | 🟥 Not Started |
| | Token Estimator Service | FastAPI service with heuristics, metrics | Backend Partner (Jules) | 🟥 Not Started |
| | Marketplace Backend | Extend attestation schema, reviewer workflow, compliance notes | Marketplace Ops (Eli) | 🟥 Not Started |
| | Docs Refresh | Quickstart + roadmap updates with new UI flows | DevRel Liaison (Nia) | 🟥 Not Started |

## Cross-Squad Dependencies (Live)
- Kafka topics: `constitution.updated`, `policy.decisions`, `identity.audit`, `conversation.events`, `training.audit`, `slm.metrics`, `marketplace.catalog` — provisioned by Infra & Ops.
- Redis namespaces: shared key strategy published by Identity squad; Training + Policy caches reuse this layout.
- Temporal workflow version: MAO version bump announced by Policy & Orchestration to Runtime squad before Integration Day.
- Recorded contracts: Runtime squad to capture `/v1/chat/stream`, Governance to capture `/v1/evaluate`, both delivered to Experience squad before 2025-10-09.

## Daily Tracking
- Update statuses during 09:00 PT stand-up; shift tasks to 🟧 or 🟩 as teams progress.
- Use this grid in tandem with `docs/sprints/status/YYYY-MM-DD.md` for executive summaries.

## Immediate Next Actions (2025-10-04 → 2025-10-06)
- **Sprint-2 / Governance Core**
	- Ada to merge rule-pack schema PR and trigger policy evaluator load test by Oct 5 12:00 PT.
	- Ravi to publish Redis namespace proposal + constitution cache warm-up script in `docs/design/contracts/2025-10-05/` by Oct 5 EOD.
	- Leah to schedule first JWT rotation dry run using staging Redis + Kafka audit topic; share results in standup Oct 6.
- **Sprint-3 / Runtime & Training**
	- Kai to land orchestrator SSE scaffold with placeholder provider responses by Oct 5 18:00 PT.
	- Zara to draft training lock state diagram and Redis key layout, attach to Sprint-3 doc by Oct 6 standup.
	- Milo to prepare fakeredis/aiokafka fixtures skeleton for integration tests and open PR checklist by Oct 6.
- **Sprint-4 / Experience & Ecosystem**
	- Mira to scaffold admin console layout + navigation shell in `apps/admin-console` by Oct 5, linking to recorded contracts.
	- Theo to confirm settings API contract ingestion (recorded traffic sample) and create typed client stub by Oct 6.
	- Nia to outline documentation updates (Quickstart + roadmap) with new UI screenshots placeholders, PR planned Oct 6.
