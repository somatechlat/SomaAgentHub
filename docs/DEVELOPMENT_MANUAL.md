# Development Manual

Date: 2025-10-08

This guide covers local development, environment variables, testing, and observability for SomaAgentHub.

## Prerequisites

- macOS or Linux
- Python 3.10+ (3.11 recommended)
- pip and virtualenv (venv or uv)
- Optional: Docker + kubectl for container/K8s flows

## Environment setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Running core services locally

In separate terminals:

```bash
uvicorn services/gateway-api/app.main:app --reload --port 60000
uvicorn services/orchestrator/app.main:app --reload --port 60002
```

Verify:

```bash
curl -s http://localhost:60000/health
curl -s http://localhost:60000/metrics | head -n 20
```

## Observability in development

- Metrics: each service should expose /metrics. Use curl locally; Prometheus scraping requires K8s with ServiceMonitors.
- Logs to Loki (optional): install python-logging-loki in your venv and set LOKI_URL if you have a Loki instance.

```bash
pip install python-logging-loki
export LOKI_URL=http://localhost:3100
```

Gateway and Orchestrator will attach a Loki handler automatically when LOKI_URL is set.

## Environment variables

- LOKI_URL: http://loki:3100 (K8s) or http://localhost:3100 (local Loki)
- OTEL_*: Optional if enabling OpenTelemetry exporters (not required by baseline)

## Testing and linting

```bash
pytest -q
```

Consider enabling pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Service conventions

- Expose /health and /metrics
- Structure logs (JSON preferred) and rely on environment flags for external sinks
- Keep dependencies minimal and pinned in service-specific requirements.txt

## Next steps

- For K8s observability deployment, see docs/observability/README.md
- For system architecture, see docs/ARCHITECTURE.md
