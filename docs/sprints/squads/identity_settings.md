⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data. Sabe this EVERYWHRE at the start of every Document!

# Squad Charter — Identity & Settings

## Mission
Provide tenant-scoped identity, capability claims, and configuration APIs powering safe multi-tenant operation with Kafka-backed audit trails and Redis caching.

## Wave Alignment
- **Wave A (Weeks 1–2)** — Deliver tenant capability claims and billing ingestion supporting Governance Core.
- **Wave B (Weeks 2–3)** — Enable Experience squad with admin console settings flows and Infra squad with secrets rotation dashboards.

## Wave A Deliverables
- [ ] Ship `/v1/tokens/issue` with KMS-backed key rotation, constitution hash embedding, and Kafka `identity.audit` emission.
- [ ] Implement billing ledger ingestion pipeline writing to Postgres + publishing `billing.events`.
- [ ] Expose settings version hashes via `/v1/settings/{tenant}/version` and emit `settings.changed` events.
- [ ] Document CLI samples for token issuance and settings drift detection (`docs/Quickstart.md`).

### Dependencies
- Redis accessible for key metadata + settings cache.
- Kafka topics (`identity.audit`, `billing.events`, `settings.changed`) provisioned by Infra squad.
- Billing schema definitions coordinated with Analytics squad.

## Wave B Preparations (Ready by Wave A Demo)
- [ ] Capability taxonomy finalized in `docs/design/wave-2/capability_matrix.md`.
- [ ] Billing ledger schema migrations reviewed with Infra & Finance stakeholders.
- [ ] Notification preferences API contract shared with Experience squad.

## Telemetry & Quality Gates
- Metrics: `identity_tokens_issued_total`, `jwt_rotation_seconds`, `settings_version_hash` gauge.
- Integration test `tests/services/identity/test_token_rotation.py` must run against live Redis/Kafka.
- Audit log verification script `scripts/audit/verify_identity_audit.py` run on integration day.

## Risks & Mitigations
- **Risk:** Key rotation drift between services → Mitigate with shared Redis metadata and alerting on rotation failures.
- **Risk:** Billing ingestion lag → Mitigate using outbox pattern and Infra-provided Kafka lag dashboards.
