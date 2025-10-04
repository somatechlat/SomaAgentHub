⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data. Sabe this EVERYWHRE at the start of every Document!

---
title: Sprint 1 - Execution & Policy (Weeks 2-3)
owner: TBD
start_date: 2025-09-26
end_date: 2025-10-09
---

# Sprint 1 — Execution & Policy

Goal: Implement async SLM queue and provider adapters, baseline Policy Engine MVP, and identity/settings CRUD to enable guarded session start flows.

Top-level acceptance criteria:
- `POST /v1/sessions/start` enforces a policy check and either proceeds or returns a structured refusal.
- SLM requests are emitted to `slm.requests` and processed by an async worker; `slm.metrics` events show up in analytics.

Tasks
- [ ] Implement `slm.requests` Kafka topic schema and producer stub in SLM service.
- [ ] Implement async worker that consumes `slm.requests` and posts responses to `slm.responses`.
- [ ] Add provider adapters for primary providers (OpenAI style stub + local fallback) and instrument token metrics.
- [ ] Implement a minimal Policy Engine service exposing `/v1/evaluate` that returns score + reason codes.
- [ ] Wire Constitution Service caching (Redis) and have Policy Engine consult constitution hash.
- [ ] Implement Identity service token issuance (`/v1/tokens/issue`) and gateway middleware to inject request context headers (tenant, user, capabilities).
- [ ] Add integration tests: start session -> policy evaluate -> queued slm request -> worker response -> session continues.

Notes
- Owners and specific subtask assignees to be filled by team leads. Use `issues/` to track subtasks and link back to this checklist.
- Telemetry: ensure each SLM call emits `tokens_consumed`, `model_id`, `latency_ms` and the policy evaluation emits `score` and `time_ms`.
