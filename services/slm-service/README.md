# SomaGent SLM Service

Handles queued SLM generation requests and streams responses back to the orchestrator. The current stub simply accepts requests and returns a placeholder ID.

## Running locally

```bash
uvicorn app.main:app --reload --port 8700
```

Environment prefix: `SOMAGENT_SLM_`.
