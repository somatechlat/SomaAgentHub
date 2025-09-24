# SomaGent Multi-Agent Orchestrator (MAO)

MAO turns high-level intents into executable task graphs. It coordinates with Temporal/Argo to plan, schedule, and monitor capsules, provisioning the right personas, tools, and workspaces for each step.

## Running locally

```bash
uvicorn app.main:app --reload --port 8200
```

Configuration env prefix: `SOMAGENT_MAO_`.
