# SomaGent Policy Engine

Performs constitution-based policy evaluation for agent actions. This early stub returns a static score until the SMT/constraint implementation is available.

## Running locally

```bash
uvicorn app.main:app --reload --port 8400
```

Environment variables use `SOMAGENT_POLICY_` prefix.
