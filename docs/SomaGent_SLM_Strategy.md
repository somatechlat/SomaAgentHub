# SLM Strategy

> ⚠️ WE DO NOT MOCK, WE DO NOT IMITATE, WE DO NOT USE BYPASSES OR FAKE VALUES. This document describes the real SLM approach in this repository.

Last Updated: October 9, 2025

## Goals
- Deterministic, local language capabilities for reliable demos and tests
- Simple, observable API surface

## API Endpoints
- GET /health → {"status":"healthy","service":"slm-service"}
- GET /metrics → Prometheus metrics
- POST /v1/infer/sync → text generation
- POST /v1/embeddings → vector embeddings

## Metrics
- slm_infer_sync_requests_total
- slm_infer_sync_latency_seconds
- slm_embedding_requests_total
- slm_embedding_latency_seconds

## Sequence (example)
```mermaid
sequenceDiagram
  autonumber
  participant User
  participant Gateway as Gateway API
  participant Orchestrator
  participant Policy as Policy Engine
  participant SLM as SLM Service

  User->>Gateway: POST /v1/dashboard/action
  Gateway->>Orchestrator: Dispatch workflow
  Orchestrator->>Policy: POST /v1/evaluate
  Policy-->>Orchestrator: allowed: true
  Orchestrator->>SLM: POST /v1/infer/sync
  SLM-->>Orchestrator: completion + usage
  Orchestrator-->>Gateway: result
  Gateway-->>User: 200 OK
```
