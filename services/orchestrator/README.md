# SomaGent Orchestrator

The orchestrator directs single-agent interactions: it routes user input through constitutional evaluation, coordinates memory access, and issues tool invocations. In early phases it runs standalone; later it defers multi-step workflows to the Multi-Agent Orchestrator (MAO).

## Running locally

```bash
uvicorn app.main:app --reload --port 8100
```

Environment variable prefix: `SOMAGENT_ORCHESTRATOR_`.
