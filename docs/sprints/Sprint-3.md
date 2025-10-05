⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data. Sabe this EVERYWHRE at the start of every Document!

---
title: Sprint 3 - Runtime & Training Slice (Weeks 3-4)
owner: Runtime Intelligence Crew
start_date: 2025-10-04
end_date: 2025-10-18
---

# Sprint 3 — Runtime & Training Slice

Goal: Deliver the orchestrated runtime path so chat sessions can flow through the orchestrator, enter training mode, and emit auditable events end-to-end.

Top-level acceptance criteria:
- Orchestrator service mediates chat interactions, attaches constitution hash + policy verdict headers, and persists `conversation.events` to Kafka.
- Training Mode API allows admin-only enable/disable with lock state stored in Redis and audit trail in `training.audit` topic.
- Streaming chat endpoint (`/v1/chat/stream`) proxies between Gateway and SLM, enforcing moderation middleware before orchestrator dispatch.
- Observability: Prometheus metrics cover orchestrator request latency and training mode toggles; structured logs include trace IDs.

Tasks
- [ ] Stand up orchestrator FastAPI service with `/v1/conversation/step` and `/v1/conversation/stream` endpoints.
- [ ] Implement middleware to validate policy headers, append constitution hash, and emit Kafka events.
- [ ] Build Training Controller with Redis-backed lock, admin auth checks, and audit event producer.
- [ ] Wire Gateway + Orchestrator handshake, including streaming responses using server-sent events/websocket proxy.
- [ ] Add integration test covering chat request -> moderation -> orchestrator -> SLM -> response path.
- [ ] Instrument Prometheus metrics (`orchestrator_requests_total`, `training_mode_state`) and structured logging with trace IDs.

## Implementation Plan

1. **Orchestrator Runtime Path**
	- Implement `/v1/conversation/step` for synchronous turns and `/v1/conversation/stream` using Server-Sent Events/WebSocket bridging to the SLM worker, attaching policy verdict + constitution hash headers to every dispatch.
	- Add middleware that validates incoming policy headers against Redis, rejects mismatches, and publishes `conversation.events` Kafka messages with trace context.

2. **Training Mode Controller**
	- Extend the training lock endpoints with admin capability checks (via Identity verify), persist lock state in Redis with TTL, and emit `training.audit` Kafka records for every transition.
	- Provide Prometheus gauges and structured logs capturing lock owner, timestamp, and tenant.

3. **Gateway ↔ Orchestrator Streaming**
	- Enhance the Gateway session proxy to support full-duplex streaming, reusing moderation verdicts and policy evaluations before forwarding traffic.
	- Handle backpressure, timeouts, and cancellation gracefully while preserving `traceparent` headers for observability.

4. **Observability & Telemetry**
	- Instrument `orchestrator_requests_total{route,decision}` counters, latency histograms, and `training_mode_state` gauges; integrate OpenTelemetry tracing spans spanning gateway, orchestrator, and SLM hops.
	- Normalize structured JSON logs with `trace_id`, `session_id`, and `tenant` fields for audit readiness.

5. **End-to-End Validation**
	- Build an integration suite that spins up gateway, orchestrator, and SLM stubs with fakeredis + aiokafka test fixtures to validate chat flow, training toggles, and Kafka emissions.
	- Ensure policy headers and constitution hashes persist through the pipeline and are asserted within the tests.

Notes
- Coordinate with Ops for Kafka topic provisioning (`conversation.events`, `training.audit`).
- Ensure moderation middleware reuses existing refusal taxonomy from policy engine for consistent user messaging.

## Parallel Coordination
- **Wave Alignment:** Sprint-3 runs concurrently with `Sprint-2` (Governance Core) within Wave A and feeds results into `Sprint-4` (Experience & Ecosystem) starting Wave B.
- **Integration Day Objectives:** Validate Gateway → Policy → Orchestrator streaming path with live constitution hash + policy headers supplied by Sprint-2.
- **Shared Dependencies:** Kafka (`conversation.events`, `training.audit`), Redis locks (shared with Identity/Settings), Temporal workflow versions announced by Policy & Orchestration charter.
- **Upcoming Hand-offs:** Surface streaming contract (`/v1/chat/stream`) recordings for Experience squad and provide telemetry dashboards for Infra team before Wave B kickoff.
