# SLM Service

The SLM service now ships with deterministic local language models that power
synchronous inference and embedding endpoints without external dependencies.

## Quick start

```bash
poetry install
poetry run uvicorn app.main:app --reload
```

Or, using the shared repository virtual environment:

```bash
. ../../.venv/bin/activate
uvicorn app.main:app --reload
```

The service automatically trains lightweight models on `slm/data/corpus.txt` at
startup. No additional assets or downloads are required.

## Endpoints

- `POST /v1/infer/sync` — Generates a short completion using the Markov-based
  generator. Returns token accounting and latency metrics.
- `POST /v1/embeddings` — Produces TF-IDF embeddings for the provided inputs and
  reports the deterministic model name.
- `POST /v1/chat/completions` — Convenience wrapper over `/v1/infer/sync` for
  chat-style requests.
- `GET /v1/healthz` — Readiness probe.
- `GET /metrics` — Prometheus metrics for request counters and latencies.

## Testing

Run the focused service tests:

```bash
pytest
```

The suite covers endpoint behaviour, Kafka worker processing, and adapter
integration to ensure the shipped models are exercised.
