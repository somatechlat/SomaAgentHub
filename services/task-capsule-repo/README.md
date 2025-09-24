# SomaGent Task Capsule Repository

Persists capsule templates, persona molds, and tool bundles for the orchestration layer. The current placeholder surfaces a static capsule list for integration testing.

## Running locally

```bash
uvicorn app.main:app --reload --port 8910
```

Environment prefix: `SOMAGENT_CAPSULES_`.
