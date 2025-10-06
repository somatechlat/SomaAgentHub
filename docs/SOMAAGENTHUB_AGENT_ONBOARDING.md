# SomaAgentHub Coder-Agent Onboarding Guide

**Version:** 1.0.0  
**Last Updated:** October 5, 2025  
**Audience:** Automation agent or developer taking over SomaAgentHub integration work

---

## 1. Mission Brief

Welcome aboard! SomaAgentHub is fully production-ready. Your assignment is to integrate external agents and client applications using the exposed APIs and tooling. This guide contains the exact steps, commands, and validation checks you need so you can execute autonomously without rereading the full 3K-line integration manual.

> **Need more depth?** Cross-reference [`SOMAGENTHUB_INTEGRATION_GUIDE.md`](./SOMAGENTHUB_INTEGRATION_GUIDE.md) for exhaustive API details.

---

## 2. Platform Snapshot

| Component | Purpose | Endpoint/Port | Health Check |
|-----------|---------|---------------|--------------|
| Gateway API | Primary entrypoint, auth, OpenAI-compatible | `http://localhost:8000` | `GET /health` |
| Orchestrator | Temporal workflows, multi-agent execution | `http://localhost:8001` | `GET /health` |
| Identity Service | Authentication, JWT issuance | `http://localhost:8002` | `GET /health` |
| SLM Service | Local LLM completions & embeddings | `http://localhost:8003` | `GET /health` |
| Memory Gateway | Vector memory, RAG endpoints | `http://localhost:8004` | `GET /health` |
| Tool Service | 16 production adapters (GitHub, Slack, AWS…) | `http://localhost:8005` | `GET /health` |
| Marketplace API | Capsule catalog CRUD/search | `http://localhost:8006` | `GET /health` (adjust if deployed differently) |

All services emit Prometheus metrics at `/metrics`. Grafana dashboards live under `infra/monitoring/grafana/` and Prometheus alerts under `infra/monitoring/prometheus/alerts.yml`.

---

## 3. Prerequisites Checklist

- [ ] Python 3.11+ available (`python3 --version`)
- [ ] `pip` and `virtualenv` (or Poetry) installed
- [ ] Docker + Docker Compose (for local dependency emulation)
- [ ] Access credentials:
  - `SOMAAGENT_API_KEY` (service account recommended)
  - Optional: MinIO, Kafka, Postgres connection strings if using outside the default stack
- [ ] Clone of this repository (`git clone https://github.com/somatechlat/somaagent.git`)

Export required environment variables:

```bash
export SOMAAGENT_API_URL="http://localhost:8000"
export SOMAAGENT_API_KEY="<replace-with-valid-token>"
```

---

## 4. Bringup & Validation

### 4.1 Install SDK (local dev)

```bash
cd /path/to/somaagent/sdk/python
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 4.2 Smoke Test Endpoints

```bash
# Health checks
curl -sf http://localhost:8000/health
curl -sf http://localhost:8001/health
curl -sf http://localhost:8002/health
curl -sf http://localhost:8003/health
curl -sf http://localhost:8004/health
curl -sf http://localhost:8005/health

# Metrics spot check
curl -sf http://localhost:8000/metrics | head -20
```

If any service is missing, consult `scripts/dev-deploy.sh` or the Helm chart (`k8s/helm/soma-agent/`).

### 4.3 Verify Authentication

```bash
http --check-status \
  GET http://localhost:8000/v1/models \
  "Authorization:Bearer $SOMAAGENT_API_KEY"
```

Expected: JSON payload listing `somasuite-markov-v1` and other models.

---

## 5. Core Integration Steps

Follow this sequence when wiring a new agent or client:

### Step 1 – Create/Confirm Agent Identity

1. Generate a service account token via Identity Service (if you do not already have one). Example pseudo-flow:
   - `POST http://localhost:8002/v1/service-accounts`
   - Store resulting API key securely (HashiCorp Vault recommended).

2. Validate policy via Policy Engine if scoped permissions are required (`services/policy-engine/`).

### Step 2 – Register or Configure Capsule/Workflow (Optional)

- Use `Task Capsule Repository` (`services/task-capsule-repo/`) or `Marketplace API` (`services/marketplace/app/main.py`) to publish custom task capsules.
- When uploading artifacts, store binary/data assets in MinIO using `services/common/minio_client.py` utilities.

### Step 3 – Wire Conversation or Workflow Calls

#### Simple Chat Completion

```python
from somaagent import SomaAgentClient

client = SomaAgentClient(api_key=os.environ["SOMAAGENT_API_KEY"], base_url=os.environ["SOMAAGENT_API_URL"])

response = await client._request(
    method="POST",
    endpoint="/v1/chat/completions",
    json={
        "model": "somasuite-markov-v1",
        "messages": [
            {"role": "system", "content": "You are an assistant."},
            {"role": "user", "content": "Give me a project status summary."}
        ],
        "max_tokens": 200,
        "temperature": 0.7
    }
)
```

#### Workflow Launch (Temporal)

```python
workflow = client.start_workflow(
    workflow_type="multi_agent_research",
    inputs={
        "topic": "AI compliance 2026",
        "agents": ["researcher", "writer", "editor"],
        "deadline": "2025-10-20T00:00:00Z"
    }
)
```

Monitor progress via `GET /v1/workflows/{run_id}` and handle `status` transitions until `completed` or `failed`.

### Step 4 – Hook Tool Adapters

Each adapter lives under `services/tool-service/adapters/`. Invoke via Tool Service API:

```bash
http POST http://localhost:8005/v1/tools/github/execute \
  "Authorization:Bearer $SOMAAGENT_API_KEY" \
  action=create_issue \
  repo=somatechlat/somaagent \
  title="Bug report" \
  body="Reproduce steps..."
```

Substitute adapter/action per needs (e.g., `slack/send_message`, `aws/s3_upload`, `kubernetes/scale_deployment`). Reference inline docstrings for parameter schemas.

### Step 5 – Persist & Retrieve Memory (RAG)

```bash
# Store memory
http POST http://localhost:8004/v1/remember \
  "Authorization:Bearer $SOMAAGENT_API_KEY" \
  key=="support:faq:pricing" \
  value:='{"tier":"Pro","price":99,"notes":"Includes 100K requests"}'

# Retrieve contextual answer
http POST http://localhost:8004/v1/rag/retrieve \
  "Authorization:Bearer $SOMAAGENT_API_KEY" \
  query="Explain pricing tiers" \
  top_k==3
```

Feed retrieved sources into SLM prompts for context-aware responses.

---

## 6. Validation Matrix

| Task | Command / API | Expected Output |
|------|---------------|-----------------|
| Health checks | Section 4.2 | `{ "status": "ok" }` responses |
| Model discovery | `GET /v1/models` | Model list with capabilities |
| Workflow start | `POST /v1/workflows/start` | JSON with `run_id` |
| Tool execution | `POST /v1/tools/<adapter>/execute` | Adapter-specific success payload |
| Memory recall | `GET /v1/recall/{key}` | Stored value returned |
| Grafana | Login to dashboard | Panels updating in real time |

Document all results in your hand-off summary before concluding work.

---

## 7. Troubleshooting Cheat Sheet

| Symptom | Likely Cause | Fix |
|--------|--------------|-----|
| 401 Unauthorized | Missing/expired token | Regenerate service account token via Identity Service |
| 5xx on Tool Service | Adapter credentials invalid | Check adapter-specific environment vars under `services/tool-service/` |
| Workflow stuck `running` | Temporal worker offline | Restart worker or inspect logs (`services/orchestrator/`) |
| RAG returns empty | Qdrant collection missing | Ensure startup created collection (see `services/memory-gateway/`) |
| Marketplace 404 | DB migrations missing | Run Alembic migrations or seed data (`services/marketplace/db.py`) |

Consult `docs/Troubleshooting.md` (if available) or the root runbooks under `docs/runbooks/` for deeper dives.

---

## 8. Reporting & Handoff

When your integration work is complete:

1. Summarize actions, commands executed, and outcomes.
2. Attach logs or screenshots for critical flows (auth, workflow execution, tool calls).
3. Update relevant documentation or README if you added new scenarios.
4. Notify the next operator via Slack (`#soma-platform`) or the runbook-defined escalation channel.

---

## 9. Reference Links

- [Full Integration Guide](./SOMAGENTHUB_INTEGRATION_GUIDE.md)
- [Executive Summary](../EXECUTIVE_SUMMARY.md)
- [Final Sprint Report](./FINAL_SPRINT_COMPLETE.md)
- [Production Readiness Report](./PRODUCTION_READY_STATUS.md)
- [Runbooks Directory](./runbooks/)

You are now unblocked. Execute integrations confidently, and update this doc if you discover improvements for future agents. Good luck! 🚀
