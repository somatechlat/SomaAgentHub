# SomaAgentHub Architecture

Date: 2025-10-08

This document reflects what’s actually implemented in this repository today. It maps services, data flows, and the observability plane based on code and manifests.

## Components at a glance

- API and Orchestration
  - Gateway API (FastAPI): entry point for clients; exposes /health and /metrics
  - Orchestrator (Temporal + FastAPI): workflow coordination, activities, analytics metric emission
- Batch and Stream
  - Airflow service: example DAG that calls the Gateway; logs to Loki
  - Flink service (scaffold): starter job and manifests for future streaming
- Observability
  - Prometheus: metrics scraping via ServiceMonitors
  - Loki: centralized logs; optional python-logging-loki handler in services

Other service directories exist (identity-service, tool-service, memory-gateway, etc.). They provide starting points and APIs, but the minimal verified path centers on Gateway + Orchestrator, plus Airflow and Loki integration.

## Service map

- services/gateway-api
  - FastAPI app, exposes /health and /metrics
  - Observability: optional Loki handler through LOKI_URL; Prometheus metrics endpoint

- services/orchestrator
  - FastAPI app for admin/endpoints and a Temporal-based workflow layer
  - Workflows include marketing activities; analytics_setup_activity increments a Prometheus Counter with labels for later queries
  - Observability: optional Loki handler; Prometheus metrics endpoint

- services/airflow-service
  - Airflow Docker image with python-logging-loki and DAG(s)
  - Example DAG: invokes Gateway to refresh memory; outputs logs to Loki

- services/flink-service
  - Scaffold for Apache Flink job(s); manifests exist to run a basic job

Directories for other services (identity-service, tool-service, memory-gateway, etc.) are present with main.py files; their production wiring varies. Consult each service’s README or code.

## Data flows

- Client -> Gateway API (HTTP)
  - Gateway receives requests and may proxy or trigger workflows

- Gateway API -> Orchestrator (HTTP/Temporal activities)
  - Orchestrator runs workflows (Temporal); activities include analytics setup that emits Prometheus metrics

- Airflow -> Gateway API (HTTP)
  - Airflow DAG tasks call Gateway endpoints on schedule; logs go to Loki

- Flink (future)
  - Stream processors ingest events and enrich/write to downstream systems; current repo provides the scaffold only

## Observability plane

- Metrics: Prometheus scrapes /metrics on Gateway, Orchestrator, and any service labeled for monitoring in k8s/monitoring/servicemonitors.yaml. Custom metric example: campaign_analytics_created_total with labels.
- Logs: Loki Deployment and Service at k8s/loki-deployment.yaml; services can send logs by setting LOKI_URL to http://loki:3100 and enabling the Loki handler (already wired in Gateway/Orchestrator).

Tracing is optional and not required for the baseline. If you add OTLP exporters, document endpoints and sampling in a tracing-specific guide.

## Kubernetes manifests

- k8s/loki-deployment.yaml: Namespace, ConfigMap, Deployment, Service for Loki (image grafana/loki:2.x)
- k8s/monitoring/servicemonitors.yaml: scrapes Gateway/Orchestrator and any service labeled monitoring: enabled; includes namespace selectors (observability, somaagent, etc.)
- k8s/airflow-deployment.yaml: Airflow webserver and scheduler Deployments + Service; envs include LOKI_URL and GATEWAY_URL
- k8s/flink-deployment.yaml: Flink job/cluster scaffold

## Scripts

- scripts/deploy.sh: installs kube-prometheus-stack with Grafana disabled and applies Loki
- scripts/deploy-wave-c-infra.sh: similar infra deploy for a wave; updated to verify Loki

## Status summary

- Core path: Gateway + Orchestrator with Prometheus metrics and optional Loki logging — implemented
- Airflow: implemented with Loki logging and real DAG calling Gateway
- Flink: scaffold present, production wiring to be added
- Grafana: not required; legacy references deprecated

For deployment details, see docs/INSTALLATION_DEPLOYMENT.md and docs/observability/README.md.
