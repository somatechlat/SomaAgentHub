⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data. Sabe this EVERYWHRE at the start of every Document!

# Parallel Sprint Execution Playbook

This playbook defines how SomaGent executes product design and engineering sprints concurrently across all squads while honoring the "real systems only" mandate. It extends the existing [Implementation Roadmap](Implementation_Roadmap.md) and [Sprint Plan](../SprintPlan.md) with concrete roles, cadences, and dependency management practices to keep every stream delivering production-grade outcomes in parallel.

## Objectives
- Deliver every roadmap workstream simultaneously without introducing mocks, stubs, or simulated data.
- Maintain design and architecture decisions ahead of implementation by one iteration so engineering always builds against approved artifacts.
- Provide transparent synchronization points that keep squads aligned on shared services, contracts, and benchmarks.
- Ensure all environments (local, staging, prod) run against real infrastructure components (Redis, Kafka/KRaft, Postgres, Temporal, SomaBrain) with observable telemetry.

## Squad Model
| Squad | Domains | Core Ownership | Key Integrations |
|-------|---------|----------------|------------------|
| **Memory & Constitution** | SomaBrain client, Constitution service, Memory Gateway | Transactional outbox, replay metrics, constitution enforcement | Kafka events (`constitution.updated`), Redis streams, Postgres outbox |
| **SLM Execution** | Sync + async inference, provider adapters, benchmarks | `slm-service`, worker pods, provider scoring | Kafka (`slm.requests`, `slm.metrics`), Postgres benchmark store, Observability stack |
| **Policy & Orchestration** | Gateway, Policy Engine, MAO workflows | JWT/mode middleware, Temporal workflow orchestration | Constitution hashes, Notification bus, Identity service |
| **Identity & Settings** | Tenant controls, billing hooks, notification preferences | JWT issuance, settings versioning, billing ledger | Redis cache, Kafka (`settings.changed`, `billing.events`), Postgres |
| **UI & Experience** | Admin console, conversation workspace, marketplace UX | Component library, Agent One Sight, persona tooling | Gateway APIs, Notification WebSockets, Analytics service |
| **Infra & Ops** | Compose stack, CI/CD, observability, security | Helm/Terraform overlays, SomaSuite dashboards, chaos + load test harness | All services via metrics/log exporters |

Each squad executes a two-week cadence with the following roles:
- **Squad Lead** (engineering) – accountable for deliverables and cross-squad commitments.
- **Design Lead** – maintains Figma/system diagrams and pushes design snapshots to `docs/design/` at least one sprint ahead.
- **QA / Benchmark Owner** – curates real-data test suites and nightly regression runs; no mocks permitted.
- **Reliability Anchor** – ensures metrics, alerting, and runbooks land with each feature.

## Sprint Wave Structure
To achieve full parallelism, the program runs overlapping waves:
- **Wave A (Weeks 1–2, 3–4, …)**: Core platform squads (Memory, SLM, Policy, Identity) deliver backend capabilities.
- **Wave B (Weeks 2–3, 4–5, …)**: Experience + Infra squads integrate against freshly delivered APIs while preparing next-wave infrastructure.
- **Design Wave (Always +1 sprint ahead)**: Design leads finalize flows, API contracts, and architecture diagrams for features landing in the subsequent wave.

This overlap keeps every squad building continuously while absorbing interdependencies during a shared integration day each week (Wednesday).

## Cadence & Rituals
- **Daily**: Cross-squad standup (15 minutes) focusing on inter-squad blockers and real-environment validation.
- **Twice Weekly**: Design & Architecture clinic; design leads demo upcoming artifacts, engineering confirms feasibility.
- **Weekly**: Integration Day – squads deploy to staging backed by real services; run smoke + regression packs, update shared telemetry dashboards.
- **End of Sprint**: Parallel review sessions per wave followed by a global demo where each squad presents running software against live infrastructure.
- **Continuous**: Feature flags, migrations, and infrastructure changes must be merged behind real-world tests and CI validations; no mock toggles permitted.

## Dependency Management
1. **Contract-First**: API/schema changes are captured as `.proto`, OpenAPI specs, or Postgres migration drafts in `design/` before implementation. Any squad consuming the contract signs off during the clinic.
2. **Staging Guarantees**: Shared staging environment mirrors production topology. Changes merge only after passing:
   - Live Redis/Postgres migrations
   - Kafka topic verification (`kafka-topics.sh` health check)
   - Temporal workflow end-to-end run
3. **Temporal Handshakes**: Policy/Orchestration squad publishes Temporal workflow IDs & versions. Downstream squads consume these through `settings-service` or environment variables with explicit version pinning.
4. **Telemetry Gates**: Every new component must emit metrics/traces before feature completion. Infra squad provides dashboards; reliability anchors confirm alerts fire with synthetic-but-real data (e.g., replaying actual Kafka messages).

## Parallel Sprint Commitments
| Workstream | Sprint N Deliverables | Sprint N+1 Prereqs (ready at start of N) |
|------------|----------------------|-------------------------------------------|
| Memory & Constitution | Outbox dispatcher, constitution checksum enforcement | Finalized schema migrations, replay benchmarks, updated runbooks |
| SLM Execution | Provider adapter GA, async queue scaled to 3 replicas | Benchmark scenarios, provider scoring thresholds, observability queries |
| Policy & Orchestration | Policy scorecards, MAO workflow version bump | Temporal contract updates, notification escalation flows |
| Identity & Settings | Tenant capability claims, billing event ingestion | Billing ledger schema, JWT claim taxonomy, CLI samples |
| UI & Experience | Admin console releases, live conversation & notification UX | Wireframes, API mocks recorded from real staging (via `scripts/record_live_traffic.py`) |
| Infra & Ops | Helm rollout for staging, SomaSuite dashboards, chaos drills | Terraform delta plan, secrets rotation schedule, capacity benchmarks |

## Design & Docs Workflow
- Design artifacts live in `docs/design/` with versioned subfolders (`wave-<num>/`).
- Each sprint, design squads produce: user flows, API specs, sequence diagrams, acceptance criteria, and attach real data samples captured from staging.
- Engineering squads cannot start implementation without the design pull request merged the prior sprint.
- Documentation updates are treated as blocking deliverables; missing docs fail the sprint review.

## Quality Gates
- **Build**: Every push triggers backend `pytest`, frontend `pnpm test`, linting (Ruff/ESLint), type checks (mypy/tsc), Temporal lint (when available).
- **Integration**: Nightly pipeline executes real end-to-end scenarios across services using shared staging infra.
- **Security**: Weekly dependency scan, monthly penetration test rehearsal. Any failure blocks releases until resolved.

## Tooling & Automation
- `scripts/parallel/squad_status.py` – Scrapes GitHub projects, merges CI health, emits dashboard JSON for the SomaSuite Observability Console (`parallel_sprint_status`).
- `scripts/parallel/record_contracts.py` – Captures live OpenAPI/Proto contracts from staging and stores them under `docs/design/contracts/<date>/` for traceability.
- `scripts/parallel/benchmark_runner.py` – Runs cross-squad performance suites nightly; results stored in `analytics-service` and surfaced via `/v1/benchmarks/parallel`.

## Risk Management
- Maintain a single source of truth issue board with swimlanes per squad and explicit cross-lane dependency tags.
- Infra squad owns incident response; reliability anchors from each squad join war room rotations.
- Regression budgets allocated per sprint; no backlog item closes without at least one real-environment validation.

## Exit Criteria Per Sprint
A sprint is only considered complete when:
1. The software is deployed to staging and production-like environments with real backing services.
2. Documentation (design + runbooks + API references) is updated and merged.
3. Telemetry dashboards show healthy metrics for new components.
4. Regression tests covering the new capability run cleanly against live systems.
5. Billing and audit logs capture the new workflows end-to-end.

## Next Actions
1. Instantiate squad charters in `docs/sprints/` with links to the parallel commitments table.
2. Publish SomaSuite dashboards per squad using the `parallel_sprint_status` data source.
3. Wire nightly benchmark + regression pipelines to post results into the notification feed tagged by squad.
4. Audit current sprints to align with this wave structure and backfill any missing design artifacts.
