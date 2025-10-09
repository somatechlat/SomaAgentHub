# SLM Service – User Manual

## Overview
Deterministic local language capabilities for text generation and embeddings.

## Base URL
- Local port-forward: http://127.0.0.1:11001

## Endpoints
- GET /health -> {"status":"healthy","service":"slm-service"}
- GET /metrics -> Prometheus metrics
- POST /v1/infer/sync
- POST /v1/embeddings

## Quick Start
```
POST /v1/infer/sync
{
  "prompt": "Write a short greeting",
  "max_tokens": 64,
  "temperature": 0.8
}
```

## Troubleshooting
- Check /health and /metrics; see docs/observability/Metrics_Reference.md
