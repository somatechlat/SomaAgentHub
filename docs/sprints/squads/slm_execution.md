⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data. Sabe this EVERYWHRE at the start of every Document!

# Squad Charter — SLM Execution

## Mission
Operate hybrid sync/async inference with real provider adapters, queueing, and benchmark telemetry so orchestration has deterministic, production-ready responses.

## Wave Alignment
- **Wave A (Weeks 1–2)** — Core queue + worker rollout in lockstep with Memory, Policy, and Identity squads.
- **Wave B (Weeks 2–3)** — Integration with Experience squad for live conversation UX and Infra squad for observability pipelines.

## Wave A Deliverables
- [ ] Define and provision `slm.requests` / `slm.responses` Kafka topics with schema registry entries.
- [ ] Implement FastAPI producer endpoints instrumented with token + latency metrics (`slm.metrics`).
- [ ] Deploy async worker pool (>=3 replicas) processing real provider adapters (OpenAI, Anthropic, local Llama fallback).
- [ ] Publish benchmark harness results to analytics-service `/v1/benchmarks/parallel` nightly.

### Dependencies
- Provider credentials vaulted and rotated by Infra squad.
- Redis for request dedupe & idempotency tokens.
- Observability exporters wired to SomaSuite dashboards.

## Wave B Preparations (Ready by Wave A Demo)
- [ ] Benchmark scenario definitions stored in `docs/design/wave-2/slm_benchmarks.md` with real prompts + acceptance thresholds.
- [ ] Provider scoring thresholds reviewed with Policy squad.
- [ ] Alert rules for refusal spikes merged into Infra dashboards.

## Telemetry & Quality Gates
- Ensure p95 end-to-end worker latency ≤ 1.2s with alerts at 1.0s.
- Nightly benchmark job must pass before merging feature PRs.
- Integration test `tests/services/slm/test_async_queue_flow.py` runs against live Kafka during integration day.

## Risks & Mitigations
- **Risk:** Provider rate limits → Mitigate with adaptive concurrency + fallback provider chain.
- **Risk:** Benchmark flakiness → Mitigate by capturing real traffic via `scripts/parallel/record_contracts.py` and replaying deterministically.
