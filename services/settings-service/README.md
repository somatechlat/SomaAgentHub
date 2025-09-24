# SomaGent Settings & Marketplace Service

Stores tenant configuration, marketplace metadata, token budgets, and tool catalogs. This stub exposes static data until the persistence layer is implemented.

## Running locally

```bash
uvicorn app.main:app --reload --port 8500
```

Environment prefix: `SOMAGENT_SETTINGS_`.
