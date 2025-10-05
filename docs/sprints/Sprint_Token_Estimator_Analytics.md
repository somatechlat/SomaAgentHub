# Sprint: Token Estimator Analytics Integration

**Date:** October 5, 2025  
**Objective**: Wire token estimator to analytics service for historical metrics and trend analysis.

## Current State
- ✅ Token estimator service exists
- ✅ Tiktoken-based estimation works
- ❌ No historical data integration (TODO comment)
- ❌ No analytics service API calls
- ❌ No trend-based optimization
- ❌ No cost forecasting

## Tasks

### 1. Analytics Service Client
- Create HTTP client for analytics service
- Implement `/v1/metrics/query` endpoint calls
- Add retry logic and timeouts
- Cache recent metrics locally

### 2. Historical Metrics Retrieval
- Query `slm.metrics` topic data from ClickHouse
- Aggregate tokens per model/tenant/timeframe
- Calculate average tokens per request type
- Track token usage trends

### 3. Cost Forecasting
- Implement cost prediction based on historical usage
- Add budget alerts (approaching limits)
- Calculate ROI per model
- Suggest cost optimizations

### 4. Trend-Based Recommendations
- Analyze token usage patterns
- Recommend cheaper models for similar tasks
- Suggest prompt optimizations
- Identify high-cost sessions

## Files to Modify
- `services/token-estimator/app/main.py` (replace TODO)
- `services/common/analytics_client.py` (create new client)
- Add analytics service integration tests

## Analytics Queries
```sql
-- Historical token usage
SELECT
  model,
  AVG(prompt_tokens) as avg_prompt,
  AVG(completion_tokens) as avg_completion,
  SUM(total_tokens) as total_tokens,
  COUNT(*) as request_count
FROM slm_metrics
WHERE tenant_id = ?
  AND timestamp >= NOW() - INTERVAL 30 DAY
GROUP BY model

-- Cost by tenant
SELECT
  tenant_id,
  SUM(total_cost_usd) as total_cost,
  AVG(cost_per_request) as avg_cost
FROM slm_metrics
WHERE timestamp >= NOW() - INTERVAL 7 DAY
GROUP BY tenant_id
ORDER BY total_cost DESC
```

## Environment Variables
```bash
export ANALYTICS_SERVICE_URL="http://analytics-service:8000"
export TOKEN_ESTIMATOR_CACHE_TTL="300"
export COST_FORECAST_WINDOW_DAYS="30"
```

## Success Criteria
- ✅ Historical metrics retrieved successfully
- ✅ Cost forecasts accurate within 10%
- ✅ Recommendations reduce costs by 15%+
- ✅ Trends updated every 5 minutes
- ✅ No TODO comments remain

## Owner
Analytics/FinOps team

## Status
**Not started** – TODO comment in main.py
