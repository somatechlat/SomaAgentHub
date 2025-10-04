⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data. Sabe this EVERYWHRE at the start of every Document!

# Local Development: Orchestrator Service

This guide describes how to run the Temporal-backed orchestrator service locally. It assumes you have Python 3.11+, [Temporal](https://docs.temporal.io/) tooling, Kafka, and Ray available. When working on Sprint 1A you should exercise the service end-to-end with the real infrastructure components listed below.

## 1. Environment Variables

The orchestrator reads its configuration from environment variables (see `services/orchestrator/app/core/config.py`). Set these before launching:

| Variable | Description | Default |
| --- | --- | --- |
| `TEMPORAL_TARGET_HOST` | Temporal frontend host:port | `temporal:7233` |
| `TEMPORAL_NAMESPACE` | Temporal namespace to use | `default` |
| `TEMPORAL_TASK_QUEUE` | Task queue that the worker polls | `somagent.session.workflows` |
| `POLICY_ENGINE_URL` | HTTP URL for the policy engine | `http://policy-engine:8000/v1/evaluate` |
| `IDENTITY_SERVICE_URL` | HTTP URL for the identity service | `http://identity-service:8000/v1/tokens/issue` |
| `KAFKA_BOOTSTRAP_SERVERS` | Comma-separated Kafka brokers for audit events | _unset_ |
| `RAY_ADDRESS` | Ray cluster or `auto` for local | `auto` |
| `RAY_NAMESPACE` | Ray namespace for completions | `somagent` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Optional OTLP collector endpoint | _unset_ |

## 2. Start Dependencies

1. **Temporal** – run a local instance with the CLI:
   ```bash
   temporal server start-dev --ip 0.0.0.0 --port 7233
   ```
2. **Kafka** – start the existing cluster from `docker-compose.stack.yml` or connect to an integration environment. The workflow will publish audit events to the `agent.audit` topic if brokers are configured.
3. **Ray** – start a local ray runtime (only required if you want the SLM activity to execute):
   ```bash
   ray start --head --port=6379
   ```

## 3. Run the Orchestrator API

Launch the FastAPI application once dependencies are ready:

```bash
uvicorn services.orchestrator.app.main:app --host 0.0.0.0 --port 8090 --reload
```

The service exposes the following primary endpoints:

- `POST /v1/sessions/start` – starts the `session-start-workflow` in Temporal.
- `GET /v1/sessions/{workflow_id}` – fetches workflow status and final result.
- `GET /health` – liveness probe.
- `GET /metrics` – Prometheus metrics scrape endpoint.

## 4. Start the Temporal Worker

In a separate terminal, run the worker so activities are executed:

```bash
python -m services.orchestrator.app.worker
```

The worker registers the `SessionWorkflow` along with the following activities:

- `evaluate-policy` – hits the real policy engine via HTTP.
- `issue-identity-token` – obtains a JWT from the identity service.
- `run-slm-completion` – invokes a Ray remote function to simulate provider completions.
- `emit-audit-event` – publishes audit events to Kafka if brokers are configured.

## 5. Smoke Test

With the API and worker running, trigger a session workflow:

```bash
curl -X POST http://localhost:8090/v1/sessions/start \
  -H 'Content-Type: application/json' \
  -d '{
        "tenant": "tenant-demo",
        "user": "user-demo",
        "prompt": "kick off a demo",
        "metadata": {"session_id": "sess-local"}
      }'
```

The response contains the Temporal `workflow_id` and `run_id`. Use the status endpoint to inspect completion:

```bash
curl http://localhost:8090/v1/sessions/session-sess-local
```

If Temporal, Kafka, or Ray are unreachable, the worker logs will surface the error. Ensure dependent services are available before filing bugs — the orchestrator intentionally uses the real clients instead of mocks.
