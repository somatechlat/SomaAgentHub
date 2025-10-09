#!/usr/bin/env bash
# Simple dev starter: run port selection, start temporal infra, and print commands to start services.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

echo "Running port selection script..."
scripts/select_free_ports.sh

echo
echo "Bringing up Temporal infra with generated override..."
docker compose -f infra/temporal/docker-compose.yml -f infra/temporal/docker-compose.override.ports.yml up -d

echo
echo "Temporal infra started. Check 'docker ps' and the generated override at infra/temporal/docker-compose.override.ports.yml"
echo
echo "Start Orchestrator (example):"
echo "  export TEMPORAL_HOST=localhost:7237" # adjust if override uses other host port
echo "  export PYTHONPATH=$ROOT/services/orchestrator"
echo "  $ROOT/.venv/bin/python -m uvicorn services.orchestrator.app.main:app --host 0.0.0.0 --port 60002"
echo
echo "Start Gateway (example):"
echo "  export SOMAGENT_GATEWAY_JWT_SECRET=dev-secret"
echo "  export SOMAGENT_GATEWAY_REDIS_URL=redis://localhost:6380/0"
echo "  export SOMAGENT_GATEWAY_ORCHESTRATOR_URL=http://localhost:60002"
echo "  export PYTHONPATH=$ROOT/services/gateway-api"
echo "  $ROOT/.venv/bin/python -m uvicorn --app-dir services/gateway-api app.main:app --host 0.0.0.0 --port 60010"
