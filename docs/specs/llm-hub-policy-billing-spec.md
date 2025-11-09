# LLM Hub Policy & Billing Specification

## Purpose
Define the enforcement and accounting layer for LLM requests: cost controls, quotas, safety, residency, and usage event emission.

## Policy Types
- Cost Caps: per-request, daily, monthly.
- Quotas: RPM, TPM, concurrent sessions.
- Safety: classification → allow/redact/block.
- Data Residency: constrain provider/model by actor region.
- Tool Use Restrictions: role-based allowlist.
- Fallback Policy: permitted downgrade chain.

## Evaluation Flow
1. Resolve actor context (roles, org, region, entitlements).
2. Retrieve catalog entry & check capability/role authorization.
3. Pre-cost estimation (rough tokens) → compare with caps.
4. Safety pre-scan (prompt classification); redact if needed.
5. Provider dispatch.
6. Post-result safety scan (output), finalize redactions.
7. Emit usage event with tokens, cost, decisions.

## Data Contracts
PolicyDecision:
- decision_id
- type: cost_cap | quota | safety | residency | tool_restriction | fallback
- action: allow | deny | downgrade | redact
- reason | details

UsageEvent:
- event_id
- timestamp
- actor { user_id, org_id, roles }
- model_id / provider
- tokens_in / tokens_out
- cost_total (input_cost + output_cost)
- currency
- decisions: [PolicyDecision]
- latency_ms
- fallback_applied (bool)

QuotaState:
- actor_id / org_id
- window (minute/day/month)
- tokens_consumed / requests_consumed
- remaining

## Enforcement Logic
- Deny if any hard cost cap < estimated cost after fallback attempts.
- Downgrade if requested model violates residency or safety but a fallback chain offers compliant alternative.
- Redact if PII segments detected and policy allows sanitized pass-through.
- Block tool calls if role lacks entitlement; optionally downgrade to plain completion.

## Event Emission & Reliability
- Usage events published to Kafka topic `llm.usage` within 2s.
- Retry with exponential backoff; dead letter queue on repeated failure.
- Idempotency: event_id (UUID) prevents duplicate accounting.

## Metrics
- `llm_policy_decisions_total{type,action}`
- `llm_usage_tokens_in_total{tenant}` / `llm_usage_tokens_out_total{tenant}`
- `llm_quota_denies_total{tenant}`
- `llm_fallback_total{primary, fallback}`
- `llm_redaction_events_total` 

## Acceptance Criteria
- Quota denies and cost caps enforced deterministically in tests.
- Safety classifier redacts configured categories (e.g., PII) with audit trail.
- Usage events match token counts returned in response (no drift).
- Fallback logic chooses next viable model in chain under provider degradation.
