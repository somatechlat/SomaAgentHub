# Policy Engine – User Manual

## Overview
The Policy Engine provides centralized authorization and policy enforcement for the SomaAgentHub platform.

## Endpoints

### System
- `GET /health`: Performs a health check of the service.
- `GET /ready`: Indicates if the service is ready to accept traffic.
- `GET /metrics`: Exposes Prometheus metrics.

### Policy
- `POST /v1/evaluate`: Evaluates a request against the defined policies.
    - **Request Body:** `{"session_id": "string", "tenant": "string", "user": "string", "prompt": "string", "role": "string", "metadata": {}}`

## Constitution
The Policy Engine uses a "constitution" to define its policies. The constitution is a set of rules that are evaluated against each request.

## Caching
The Policy Engine caches policy decisions in Redis to improve performance.
