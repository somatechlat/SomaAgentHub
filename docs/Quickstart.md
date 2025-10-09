# Quick Start

Minimal steps to run key services locally and verify metrics/logging. For Kubernetes and full observability, see docs/observability/README.md.

## 1. Clone & bootstrap

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## 2. Launch services (separate shells)

```
uvicorn services/gateway-api/app.main:app --reload --port 60000
uvicorn services/orchestrator/app.main:app --reload --port 60002
```

## 3. Verify endpoints

```
curl -s http://localhost:60000/health
curl -s http://localhost:60000/metrics | head -n 20
```

## 4. Optional: enable Loki logging locally

Install python-logging-loki in your venv and export LOKI_URL if you have a Loki instance running.

```
pip install python-logging-loki
export LOKI_URL=http://localhost:3100
```

## 5. Next steps

- Deploy Prometheus (Grafana disabled) and Loki via scripts/deploy.sh and k8s/loki-deployment.yaml.
- Explore the Airflow example in services/airflow-service.
- Review tests under tests/ and run pytest.
