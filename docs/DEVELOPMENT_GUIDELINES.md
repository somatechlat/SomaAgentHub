⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data. Sabe this EVERYWHRE at the start of every Document!

# Development Guidelines (Real‑Infra Only)

## Core principle
- **Never mock external services in the main codebase.** All services (Kafka, Redis, Postgres, etc.) must be started via the provided Docker‑Compose stack and accessed through their real network endpoints.
- Persistence is required for every stateful service. The `docker-compose.stack.yml` defines named volumes (`kafka_data`, `redis_data`, `postgres_data`) that survive container restarts and ensure data integrity across sprint cycles.

## How to work
1. **Start the stack** before any development or test run:
   ```bash
   docker compose -f docker-compose.stack.yml up -d
   ```
   Verify health with `docker compose ps` – all services should be `healthy`.
2. **Use environment variables** to point your code at the real services. Example:
   - `KAFKA_BOOTSTRAP_SERVERS=kafka:9092`
   - `POSTGRES_URL=postgresql://soma:soma_pass@postgres:5432/soma`
   - `REDIS_URL=redis://redis:6379/0`
3. **Do not commit any test‑only mock implementations**. If a temporary stub is required for a very early prototype, place it under a `tests/` directory and ensure production code imports the real implementation.
4. **Run integration tests** against the live stack (e.g., `pytest -m integration`). These tests will spin up temporary containers if needed but always target the real services.
5. **Data cleanup** – to reset state, stop the stack and remove volumes:
   ```bash
   docker compose -f docker-compose.stack.yml down -v
   ```
   Then bring it back up.

## Sprint documentation
- Every sprint checklist now includes a **"Real‑Infra Only"** badge.
- The `docs/SprintPlan.md` has been updated to state that only real services are permitted for development.

## Policy Engine Service

The **Policy Engine** provides a single evaluation endpoint used by downstream services to enforce policy rules.

- **Endpoint**: `POST /v1/evaluate`
- **Request model** (`EvalRequest`):
  ```json
  {
    "session_id": "string",
    "tenant": "string",
    "user": "string",
    "prompt": "string",
    "role": "string",
    "metadata": { "any": "value" }
  }
  ```
- **Response model** (`EvalResponse`):
  ```json
  {
    "allowed": true,
    "score": 0.9,
    "reasons": { "constitution_hash": "<hash>" }
  }
  ```
- The service consults Redis for the **constitution hash** via `redis_client.get_constitution_hash(tenant)`. Ensure the Redis container is running and `REDIS_URL` is set.
- Simple policy rule: prompts containing the word `forbidden` are rejected.
- A **synchronous compatibility wrapper** `evaluate_sync` is provided for legacy scripts; it runs the async endpoint in an event loop.

When developing or testing locally, start the Docker‑Compose stack (includes Redis) before invoking the endpoint.

By following these rules we guarantee that the code you ship works in production environments without hidden mock dependencies.
