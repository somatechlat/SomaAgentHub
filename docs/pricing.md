# Pricing Service

This document describes the Pricing Service endpoints and data model.

## Endpoints

- GET `/v1/pricing/live`
  - Filters: `gpu_model`, `min_vram_gb`, `region`, `cloud`, `spot`, `max_price_hour`, `framework`, `page`, `page_size`, `sort_by`, `order`
  - Response: offers[], summary, paging, meta

- POST `/v1/pricing/snapshot`
  - Action: capture current filtered offers into a snapshot stored in ClickHouse
  - Response: `snapshot_id`, `hash`, `offers`

- GET `/v1/pricing/snapshot/{snapshot_id}`
  - Returns snapshot header and offers rows

- POST `/v1/pricing/evaluate-budget`
  - Inputs: `gpu_model`, `region`, `hours_planned`, `quantity`, `budget_cap`
  - Response: `within_budget`, `estimated_cost`, `currency`, `chosen_offer`, `blocking_reason`

- POST `/v1/pricing/evaluate-budget/with-policy`
  - Inputs: same as above + `payment_approved`, `required_feature`, `current_agents`
  - Response: adds `policy_decision` with fields like `allow_build`, `reason`

## Data Model

- PricingOffer: normalized provider offer with fields for gpu, pricing, location, and quality metrics.
- ClickHouse tables: `pricing_offers_live`, `pricing_snapshots`, `pricing_snapshot_offers`.

## Notes

- Live aggregation currently uses an internal seed; replace with real adapters later.
- On startup, the service ensures ClickHouse tables exist.
- A background refresh loop periodically ingests the latest offers into `pricing_offers_live`.
  Configure interval via `PRICING_CACHE_TTL_SECONDS`. Optional `GPUBROKER_URL` enables external adapter.
