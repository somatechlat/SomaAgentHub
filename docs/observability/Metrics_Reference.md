# Prometheus Metrics Reference

> ⚠️ WE DO NOT MOCK, WE DO NOT IMITATE, WE DO NOT USE BYPASSES OR FAKE VALUES. All metrics and data are REAL and verifiable.

This document catalogs the key Prometheus metrics exposed by SomaAgent services. It focuses on the SLM service (formerly somallm-provider) and gateway API.

Last updated: October 9, 2025

---

## SLM Service (slm-service)

- slm_infer_sync_requests_total
  - Type: Counter
  - Labels: model
  - Description: Number of synchronous inference requests served.

- slm_infer_sync_latency_seconds
  - Type: Histogram
  - Labels: model
  - Description: Latency of synchronous inference requests.

- slm_embedding_requests_total
  - Type: Counter
  - Labels: model
  - Description: Number of embedding requests served.

- slm_embedding_latency_seconds
  - Type: Histogram
  - Labels: model
  - Description: Latency of embedding operations.

Health endpoint: GET /health returns {"status":"healthy","service":"slm-service"}

---

## Gateway API (gateway-api)

Health endpoint: GET /health returns {"status":"ok","service":"gateway-api"}

---

## Scraping

All services expose /metrics and are scraped by Prometheus using ServiceMonitors (if installed). The Helm templates add the required labels for selectors.
