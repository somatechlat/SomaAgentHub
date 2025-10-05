# Sprint: Kafka Audit Wiring

**Objective**: Complete the Kafka audit event pipeline by replacing TODO stubs with real `aiokafka` producers and ensuring all services emit required audit events.

## Tasks
- Identify all `# TODO: Wire Kafka producer` comments across the codebase.
- Implement a shared `KafkaProducer` helper (e.g., `services/common/kafka_client.py`).
- Update `services/orchestrator/app/workflows/session.py` and other workflow modules to use the helper.
- Add configuration for `KAFKA_BOOTSTRAP_SERVERS` and topic names.
- Write unit tests mocking the producer and verifying message payloads.
- Verify end‑to‑end flow with a local Kafka (docker‑compose) and observe messages in Loki.

## Owner
- Platform / Observability team

## Status
- **Not started** – placeholders exist in several services.
