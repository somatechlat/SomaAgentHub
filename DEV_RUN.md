## Quick dev run

1. Generate an override with free host ports (script will print chosen ports):

```bash
./scripts/select_free_ports.sh
```

2. Start Temporal infra with the override:

```bash
docker compose -f infra/temporal/docker-compose.yml -f infra/temporal/docker-compose.override.ports.yml up -d
```

3. Start Orchestrator (example):

```bash
export TEMPORAL_HOST=localhost:7237   # adjust according to generated override
export PYTHONPATH=$(pwd)/services/orchestrator
./.venv/bin/python -m uvicorn services.orchestrator.app.main:app --host 0.0.0.0 --port 60002
```

4. Start Gateway (example):

```bash
export SOMAGENT_GATEWAY_JWT_SECRET=dev-secret
export SOMAGENT_GATEWAY_REDIS_URL=redis://localhost:6380/0
export SOMAGENT_GATEWAY_ORCHESTRATOR_URL=http://localhost:60002
export PYTHONPATH=$(pwd)/services/gateway-api
./.venv/bin/python -m uvicorn --app-dir services/gateway-api app.main:app --host 0.0.0.0 --port 60010
```

5. Smoke test: Generate a dev JWT (matching `SOMAGENT_GATEWAY_JWT_SECRET`) and POST to `http://localhost:60010/v1/sessions`.
