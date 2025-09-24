# SomaGent Notification Orchestrator

Consumes `notifications.events` from Kafka and broadcasts payloads to websocket clients (`/ws/notifications/{tenant_id}`). The admin console will subscribe to receive alerts, approvals, and system notices.

Configure via `SOMAGENT_NOTIFY_*` env vars.
