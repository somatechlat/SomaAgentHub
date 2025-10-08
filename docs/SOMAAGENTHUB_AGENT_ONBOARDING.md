# SomaAgentHub Coder-Agent Onboarding Guide

**Version:** 1.1.0  
**Last Updated:** October 8, 2025  
**Audience:** Engineers and automation agents integrating with the current SomaAgentHub services and SDK

---

## 1. Mission Brief

This guide documents the live FastAPI services, SDK helpers, and validation flows that ship inside this repository. Every instruction maps directly to code checked into `main`. If a step references an endpoint or script, you can open the path mentioned and inspect the implementation.

---

## 2. Platform Snapshot

Start each service from its directory with `uvicorn app.main:app --reload --port <port>`. The ports below are suggested defaults; change them as needed but keep the cross-service URLs in sync.

| Component | Source Directory | Suggested Port | Key Endpoints |
|-----------|-----------------|----------------|---------------|
| Gateway API | `services/gateway-api/` | `8000` | `GET /health`, `GET /metrics`, `POST /v1/chat/completions`, `GET /v1/models` |
| Orchestrator API | `services/orchestrator/` | `8100` | `POST /v1/sessions/start`, `GET /v1/sessions/{workflow_id}`, `POST /v1/mao/start` |
| Identity Service | `services/identity-service/` | `8600` | `POST /v1/tokens/issue`, `POST /v1/tokens/verify`, `GET /v1/users` |
| Tool Service | `services/tool-service/` | `8900` | `GET /v1/adapters`, `POST /v1/adapters/{adapter_id}/execute`, `POST /v1/provision` |
| Memory Gateway | `services/memory-gateway/` | `9696` | `POST /v1/remember`, `GET /v1/recall/{key}`, `POST /v1/rag/retrieve` |
| Task Capsule Repository | `services/task-capsule-repo/` | `8005` | `GET /v1/capsules`, `POST /v1/capsules` |
| Jobs Service | `services/jobs/` | `8800` | `POST /v1/jobs`, `GET /v1/jobs/{job_id}` |

All listed services expose `GET /health` and `GET /metrics`. Observability manifests are tracked in `infra/monitoring/`.

---

## 3. Prerequisites Checklist

- [ ] Python 3.11 or newer (`python3 --version`)
- [ ] `pip` plus `venv` (or Poetry) available
- [ ] Optional: Docker for dependencies such as Temporal or Redis
- [ ] Clone of this repository (`git clone https://github.com/somatechlat/somaagent.git`)
- [ ] Secrets for secured endpoints (Identity MFA code, adapter tokens, etc.)

Export the common Gateway variables when you plan to call it:

```bash
export SOMAAGENT_API_URL="http://localhost:8000"
export SOMAAGENT_API_KEY="<replace-with-valid-token>"
```

---

## 4. Bringup & Validation

### 4.1 Install the Python SDK (optional helper)

```bash
cd /path/to/somaagent/sdk/python
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 4.2 Launch core services

From separate terminals run:

```bash
cd services/gateway-api && uvicorn app.main:app --reload --port 8000
cd services/orchestrator && uvicorn app.main:app --reload --port 8100
cd services/identity-service && uvicorn app.main:app --reload --port 8600
cd services/tool-service && uvicorn app.main:app --reload --port 8900
cd services/memory-gateway && uvicorn app.main:app --reload --port 9696
```

Start additional services (Task Capsule Repository, Jobs) only if your workflow requires them.

### 4.3 Smoke-test health and metrics

```bash
curl -sf http://localhost:8000/health
curl -sf http://localhost:8100/health
curl -sf http://localhost:8600/health
curl -sf http://localhost:8900/health
curl -sf http://localhost:9696/health

curl -sf http://localhost:8000/metrics | head -20
```

If a service fails to start, inspect its logs, confirm dependencies (e.g., Redis for Identity), and open the corresponding `app/main.py` file to review startup hooks.

### 4.4 Issue an access token

1. Upsert a user via the Identity Service if required (`PUT /v1/users/{user_id}` defined in `services/identity-service/app/api/routes.py`).
2. Enrol MFA: `POST /v1/users/{user_id}/mfa/enroll` followed by `POST /v1/users/{user_id}/mfa/verify`.
3. Issue a token:

```bash
http POST http://localhost:8600/v1/tokens/issue \
  user_id=="demo-user" \
  tenant_id=="demo" \
  mfa_code=="<mfa-secret>"
```

Export `SOMAAGENT_API_KEY` with the returned token.

---

## 5. Core Integration Steps

### Step 1 – Call the Gateway

```bash
http POST http://localhost:8000/v1/chat/completions \
  "Authorization:Bearer $SOMAAGENT_API_KEY" \
  model=="somaagent-demo" \
  messages:='[{"role":"user","content":"Hello"}]'
```

The current implementation returns a static payload. Modify `services/gateway-api/app/main.py` to integrate real model inference.

### Step 2 – Start a session workflow

```bash
http POST http://localhost:8100/v1/sessions/start \
  tenant=="demo" \
  user=="researcher" \
  prompt=="Summarise onboarding gaps" \
  model=="somaagent-demo"
```

Track progress with:

```bash
http GET http://localhost:8100/v1/sessions/<workflow_id>
```

### Step 3 – Launch a multi-agent orchestration

```bash
http POST http://localhost:8100/v1/mao/start <<'JSON'
{
  "tenant": "demo",
  "initiator": "automation-bot",
  "directives": [
    {
      "agent_id": "researcher",
      "goal": "Collect open GitHub issues",
      "prompt": "List open onboarding bugs",
      "capabilities": ["github.create_repository"],
      "metadata": {}
    }
  ],
  "metadata": {}
}
JSON
```

Query status via `GET /v1/mao/{workflow_id}`.

### Step 4 – Execute tool adapters

```bash
http GET http://localhost:8900/v1/adapters

http POST http://localhost:8900/v1/adapters/github/execute \
  "X-Tenant-ID:demo" \
  action=="create_repository" \
  arguments:='{"name":"sandbox-repo"}'
```

Inspect individual adapters in `services/tool-service/adapters/`. Many expect tokens passed inside `arguments`.

### Step 5 – Use memory and retrieval

```bash
http POST http://localhost:9696/v1/remember \
  key=="support:faq:pricing" \
  value:='{"tier":"Pro","price":99}'

http POST http://localhost:9696/v1/rag/retrieve \
  query=="Explain pricing tiers"

http GET http://localhost:9696/v1/recall/support:faq:pricing
```

If Qdrant or the embedding provider is unavailable, the service logs a warning and stores data in memory.

---

## 6. Validation Matrix

| Task | Command / API | Expected Response |
|------|---------------|-------------------|
| Gateway health | `GET /health` | `{ "status": "ok" }` |
| Model discovery | `GET /v1/models` | `{ "object": "list", "data": [...] }` |
| Session workflow | `POST /v1/sessions/start` | JSON containing `workflow_id` and `run_id` |
| MAO workflow | `POST /v1/mao/start` | JSON containing `workflow_id` and `orchestration_id` |
| Tool execution | `POST /v1/adapters/{adapter}/execute` | `AdapterExecuteResponse` with job metadata |
| Memory recall | `GET /v1/recall/{key}` | Stored payload in `value` |

Document results and include log excerpts for handoff.

---

## 7. Troubleshooting Cheat Sheet

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| 401 from Gateway | Token missing or expired | Re-run the Identity Service token flow |
| 404 on workflow status | Wrong identifier | Use the `workflow_id` returned by the start call (`session-...` or `mao-...`) |
| 503 or 404 from Tool Service | Adapter disabled or missing credentials | Review adapter module and provide required secrets in `arguments` |
| 429 from Tool Service | Rate limit hit | Retry after the `Retry-After` header value |
| Memory Gateway errors | Embedding provider offline | Configure `SOMALLM_PROVIDER_URL` or rely on the fallback store |

For deeper dives, open the corresponding service directory and read the implementation referenced in the stack trace.

---

## 8. Reporting & Handoff

1. Summarise the flows you executed and their outcomes.
2. Attach API transcripts or log snippets showing key successes or failures.
3. Update any documentation you touched and raise pull requests as needed.
4. Notify the next operator via the agreed channel (see `docs/runbooks/`).

---

## 9. Reference Links

- [`services/orchestrator/app/api/routes.py`](../services/orchestrator/app/api/routes.py)
- [`services/tool-service/app/api/routes.py`](../services/tool-service/app/api/routes.py)
- [`sdk/python/README.md`](../sdk/python/README.md)
- [`docs/INTEGRATION_QUICK_START.md`](./INTEGRATION_QUICK_START.md)
- [`docs/runbooks/`](./runbooks/)
