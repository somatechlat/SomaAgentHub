# SomaGent Tool Service

Provides adapters for external tools and systems, manages authentication, and records audit events. Currently ships with static adapter data as a scaffold.

## Running locally

```bash
uvicorn app.main:app --reload --port 8900
```

Environment prefix: `SOMAGENT_TOOL_`.
