# LLM Hub Provider Adapter Interface

## Purpose
Standardize integration with heterogeneous LLM providers (cloud, on-prem, local deterministic) for inference, streaming, embeddings, pricing estimation, and health.

## Core Operations
- list_models() -> [CatalogDescriptor]
- infer(request: InferenceRequest) -> InferenceResult
- stream_infer(request) -> AsyncIterator[InferenceChunk]
- embed(texts: [str]) -> EmbeddingResult
- estimate_cost(tokens_in: int, tokens_out: int) -> CostBreakdown
- health() -> ProviderHealth

## Data Contracts (Conceptual)
InferenceRequest:
- request_id
- model_id (canonical)
- messages (structured: role/user/system/tools)
- options: { max_tokens, temperature, top_p, json_mode_schema_id?, toolset?, metadata }
- actor: { user_id, org_id, roles }
- trace_context

InferenceResult:
- model_id
- output_text (or structured segments)
- tokens_in / tokens_out
- cost_estimate
- provider_latency_ms
- policy_decisions (list)
- fallback_chain (list? if applied)

EmbeddingResult:
- model_id
- vectors: [[float]]
- tokens_in
- cost_estimate

CostBreakdown:
- input_cost
- output_cost
- total_cost
- currency

ProviderHealth:
- status: healthy | degraded | down | rate_limited
- last_error (optional)
- metrics_snapshot (e.g., recent latency p95)

## Errors (Normalized)
- ProviderAuthError
- ProviderRateLimitError
- ProviderModelUnavailableError
- ProviderQuotaExceededError
- ProviderTransientNetworkError
- ProviderCapabilityUnsupportedError

## Capability Negotiation
Client declares requested capability set; adapter declares supported features (streaming, json_mode, tool_call). Hub negotiates or downgrades with policy approval.

## Conformance Suite (Acceptance)
- Adapter returns non-empty list_models; each descriptor matches catalog schema.
- infer() returns token counts within 5% variance of independent tokenizer.
- Streaming: first chunk < 300ms p95 for providers advertising streaming.
- Errors mapped to normalized exceptions; no raw provider-specific codes leak beyond adapter.
- health() transitions to degraded after 3 consecutive transient failures; triggers fallback logic.

## Performance Targets
- infer() overhead (adapter logic excluding provider latency) < 10ms p50.
- estimate_cost() < 2ms p50 for cached pricing data.

## Observability Hooks
- Every adapter call wraps in a span: attributes { provider, model_id, operation, tokens_in, tokens_out }.
- Metrics: request count, error count by normalized error, latency histogram per operation.

## Fallback Signaling
- Adapter marks health status; Hub consults policy + fallback chain. Fallback decisions appended to InferenceResult.
