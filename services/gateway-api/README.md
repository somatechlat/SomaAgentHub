# SomaGent Gateway API

This service fronts the SomaGent platform, providing a unified entrypoint for the Admin UI, CLI, and third-party integrations. It validates identity tokens, enforces request rate limits, and forwards traffic to the internal orchestration layer.

## Running locally

```bash
uvicorn app.main:app --reload --port 8080
```

Environment variables prefixed with `SOMAGENT_GATEWAY_` configure downstream services (see `app/core/config.py`).
