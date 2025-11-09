# LLM Hub Catalog Specification

## Purpose
Define a canonical, RBAC-aware model catalog powering discovery, routing, pricing, compliance, and SLO reporting for all LLM access in SomaAgentHub.

## Entities
- model_id: canonical identifier (e.g., `openai:gpt-4o-2024-05-13`)
- display_name
- provider: openai | anthropic | azure-openai | ollama | local | fine-tuned
- modality: text | vision | audio | multi
- capabilities: [completion, chat, embeddings, tool_call, json_mode, streaming]
- pricing: { input_per_1k, output_per_1k, embed_per_1k, currency }
- limits: { max_tokens, rpm, tpm, context_window }
- regions: [us, eu, apac, internal]
- safety_profile: { policy_set: strict|balanced|lenient, classifiers: [...]} 
- compliance_tags: [gdpr, hipaa, pii_safe, partner_ok]
- allowed_roles: [admin, engineer, analyst, bot, system, partner]
- state: active | beta | deprecated | blocked
- version: semver; deprecation_date (optional)
- notes: free-form annotations

## Access & Filters
Effective catalog = base models filtered by (role, tenant_policy, region, compliance).
- Inputs: actor {roles, tenant, region}, desired capability, cost class (budget), residency flags.
- Output: list of eligible models sorted by policy preference and health/SLO.

## APIs
- GET /v1/catalog/models?capability=&role=&region=&provider=
- GET /v1/catalog/models/{model_id}
- GET /v1/catalog/providers

## Versioning & Lifecycle
- Add → Publish → Deprecate → Remove
- Downgrade map: recommended successor when deprecating
- Changes tracked with who/when; all reads are strongly consistent

## Governance
- Catalog edits allowed by admins only; audited.
- RBAC rules compiled to an efficient filter; cached per (tenant, role) for TTL.

## Acceptance Criteria
- Role-filtered list returns only eligible models within 50ms p95.
- Deprecation blocks new usage after cut date; downgrade suggestion returned.
- API returns capability/limit/pricing for client-side cost planning.
