⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data. Sabe this EVERYWHRE at the start of every Document!

# Squad Charter — Memory & Constitution

## Mission
Deliver resilient SomaBrain integration, constitution validation, and replay safety so every interaction honors the canonical ruleset using real infrastructure only.

## Wave Alignment
- **Wave A (Weeks 1–2)** — Platform core enablement alongside SLM, Policy, and Identity squads.
- **Wave B (Weeks 2–3)** — Integration hardening with Experience + Infra squads consuming fresh APIs.

## Wave A Deliverables
- [ ] Stand up transactional outbox dispatcher for memory writes with backlog age telemetry.
- [ ] Enforce constitution checksum verification in gateway + policy integrations via Redis-backed cache.
- [ ] Publish `constitution.updated` Kafka events and document schema in `docs/design/contracts/`.
- [ ] Ship replay metrics dashboard (lag, replay throughput) into SomaSuite observability.

### Dependencies
- SomaBrain endpoint live at `SOMABRAIN_URL`.
- Kafka cluster reachable (`constitution.updated` topic provisioned by Infra squad).
- Redis namespace with `constitution:*` keys managed by Identity squad for rotation parity.

## Wave B Preparations (Ready by Wave A Demo)
- [ ] Schema migration drafts for Postgres outbox tables reviewed and merged.
- [ ] Replay benchmark scenarios defined in `docs/design/wave-2/` with real data samples.
- [ ] Runbook updates for constitution drift response added to `docs/runbooks/constitution_update.md`.

## Telemetry & Quality Gates
- Emit `memory_outbox_backlog_seconds` histogram and `constitution_checksum_mismatch_total` counter.
- Integration tests: `tests/services/memory_gateway/test_outbox_replay.py` and `test_constitution_enforcement.py` must pass against live services.
- No sprint sign-off without staging verification of replay after induced SomaBrain outage.

## Risks & Mitigations
- **Risk:** Kafka topic lag causing replay delays → Mitigate with alert thresholds and Infra escalation runbook.
- **Risk:** Constitution signature verification drift → Mitigate via double-verification against SomaBrain reference signatures and fallback refusal policy.
