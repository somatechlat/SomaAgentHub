# Development Setup

This guide helps you run and contribute to SomaAgentHub locally, and points you to manifests and scripts for a Kubernetes-based setup with Prometheus and Loki. It reflects the current repo as-is and omits unimplemented parts.

## Prerequisites

- Python 3.10+ (3.11 recommended)
- pip and a virtual environment tool (venv or uv)
- Optional: Docker and kubectl for containerized/K8s workflows

## Local setup (services only)

1) Clone and create a virtual environment

   - python -m venv .venv && source .venv/bin/activate

2) Install development dependencies

   - pip install -r requirements-dev.txt

3) Run services

   - Gateway: uvicorn services/gateway-api/app.main:app --reload --port 60000
   - Orchestrator: uvicorn services/orchestrator/app.main:app --reload --port 60002

4) Verify

   - curl http://localhost:60000/health
   - curl http://localhost:60000/metrics | head -n 20

## Observability (Prometheus + Loki)

For Kubernetes deployment and verification steps, see docs/observability/README.md. In brief:

- Prometheus installed with Grafana disabled (scripts/deploy.sh)
- Loki applied via k8s/loki-deployment.yaml
- ServiceMonitors in k8s/monitoring/servicemonitors.yaml scrape services exposing /metrics

To enable Loki logging locally for a service, export LOKI_URL (e.g., http://localhost:3100) and ensure python-logging-loki is installed in that environment.

## Airflow and Flink

- Airflow service and example DAG live under services/airflow-service; see its README/Dockerfile and k8s manifests for running in-cluster with Loki logging.
- Flink has a starter job scaffold; integrate your connectors and update its manifest when ready.

## Tests

- Run pytest from the repo root. A unit test exists for orchestrator analytics activity behavior.

## Tips

- New services should expose /metrics and structure logs; label K8s Services with monitoring: enabled to be scraped.
- Prefer minimal, explicit dependencies in service requirements.
# Check utilities
