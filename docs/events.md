# Domain Events (Initial Draft)

> Canonical naming and payload shapes for cross-service events. Version via additive fields.

## Naming Convention
- Topic: `domain.event.v1` (e.g., `pricing.snapshot_created.v1`, `orchestration.started.v1`)
- Key: deterministic ID (e.g., `snapshot_id`, `workflow_id`)

## Common Envelope
```
{
  "event_id": "uuid",
  "occurred_at": "2025-11-08T12:34:56Z",
  "producer": "service-name",
  "trace_id": "...",  
  "tenant_id": "...",
  "payload": { /* event-specific */ }
}
```

## Events
### pricing.snapshot_created.v1
- Key: `snapshot_id`
- Payload:
```
{
  "snapshot_id": "snap-...",
  "source": "adapter-name",
  "currency": "USD",
  "prices": { /* normalized price map */ }
}
```

### orchestration.started.v1
- Key: `workflow_id`
- Payload:
```
{
  "workflow_id": "session-...",
  "type": "session|mao|capsule",
  "tenant": "...",
  "initiator": "user-id",
  "metadata": { }
}
```

### gateway.wizard_approved.v1
- Key: `session_id`
- Payload:
```
{
  "session_id": "wiz-...",
  "wizard_id": "...",
  "campaign_name": "...",
  "budget": { "cap": 100.0, "decision": "within|exceeded" },
  "orchestration_id": "mao-..."
}
```

## Delivery Semantics
- At-least-once delivery. Consumers must be idempotent.
- Outbox pattern recommended for producers writing to DBs.

## Security
- Avoid PII in payloads; use identifiers.
- Do not include secrets or tokens.

_Last updated: 2025-11-08_
