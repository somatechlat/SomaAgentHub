# SomaStack Quickstart

Follow these steps to bring up a development environment, run a capsule, and validate analytics.

## 1. Clone & Bootstrap
```
git clone https://github.com/somatechlat/somaagent.git
cd somaagent
python -m venv .venv
source .venv/bin/activate
pip install -r services/gateway-api/requirements.txt
npm install --prefix apps/admin-console
```
(Repeat dependency install for services you touch; see `docs/development/Developer_Setup.md`.)

## 2. Start Core Services
```
docker compose -f docker-compose.stack.yml up -d
```
This launches Kafka, Postgres, Redis, SomaBrain, Prometheus, Grafana.

## 3. Run Gateway, Tool Service, and Admin Console locally
```
uvicorn services.gateway_api.app.main:app --reload --port 8080
uvicorn services.tool_service.app.main:app --reload --port 8900
npm run --prefix apps/admin-console dev
```

## 4. Acquire Token & Call Gateway
```
TOKEN=$(curl -s http://localhost:8600/v1/tokens/issue -d '{"tenant_id":"demo","capabilities":["sessions:start"]}')
```
Use `Bearer $TOKEN` to call orchestrator endpoints via gateway.

## 5. Execute Sample Capsule
```
curl -X POST http://localhost:8210/v1/plans/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"demo","name":"quickstart","deliverables":[{"id":"docs","persona":"educator","tools":["github"],"budget_tokens":5000}]}'
```

## 6. Check Analytics
```
curl http://localhost:8930/v1/kamachiq/summary
curl http://localhost:8930/v1/exports/capsule-runs?tenant_id=demo
```

## 7. Shutdown
```
docker compose -f docker-compose.stack.yml down -v
```

Refer to runbooks in `docs/runbooks/` for security, DR, and KAMACHIQ operations.
