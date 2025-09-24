# SomaGent Constitution Service

Responsible for retrieving, verifying, and distributing the active SomaGent constitution. Downstream services rely on this component for the latest signed policy hash.

## Running locally

```bash
uvicorn app.main:app --reload --port 8300
```

Uses environment variables prefixed with `SOMAGENT_CONSTITUTION_`.
