# Token Estimator Service

**Sprint-4: Experience & Ecosystem**

FastAPI service providing token usage forecasts and cost estimates per provider using historical `slm.metrics` data.

## Features

- `/v1/forecast` - Generate single-provider forecast
- `/v1/forecast/{tenant}` - Multi-provider forecasts for tenant
- Prometheus metrics for request latency and MAPE
- Heuristic baseline estimates (to be enhanced with analytics-service integration)

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
uvicorn app.main:app --reload --port 8007

# Build Docker image
docker build -t token-estimator:latest .

# Run container
docker run -p 8007:8007 token-estimator:latest
```

## API Examples

```bash
# Get forecast for a tenant
curl -X POST http://localhost:8007/v1/forecast \
  -H "Content-Type: application/json" \
  -d '{
    "tenant": "acme-corp",
    "provider": "openai",
    "window_hours": 24
  }'

# Get multi-provider forecast
curl http://localhost:8007/v1/forecast/acme-corp?window_hours=24
```

## Metrics

- `token_forecast_requests_total` - Counter by tenant/provider
- `token_forecast_latency_seconds` - Histogram of computation time
- `token_forecast_mape` - Mean Absolute Percentage Error distribution

## Integration

- Consumed by admin console Models & Providers tab
- Will integrate with analytics-service for real historical data
- Supports Sprint-4 token cost visibility objectives

## Status

🟢 **Complete** - Baseline implementation ready; analytics integration pending
