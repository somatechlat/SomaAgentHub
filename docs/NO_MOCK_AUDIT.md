# No-Mock Audit (Real Services Only)

This repository enforces a strict no-mock policy for product code and integration tests. Below is the current status and actions taken to eliminate mocks, bypasses, or fake values.

## Completed removals (this change)

- Gateway API
  - Removed stub endpoints (`/v1/sessions`, `/v1/models`, `/v1/chat/completions`) from `services/gateway-api/app/main.py` and included the real router that forwards to the Orchestrator.
  - Replaced Wizard Engine mock approve path with a real call to Orchestrator `/v1/mao/start` in `services/gateway-api/app/wizard_engine.py`.

- Identity Service Tests
  - Replaced `fakeredis` with a real Redis via Testcontainers in `services/identity-service/tests/conftest.py`.
  - Removed `fakeredis` from `services/identity-service/requirements.txt`.

- Policy Engine Integration Test
  - Removed the in-process fake Orchestrator and now require a real Orchestrator URL via `SOMAGENT_GATEWAY_ORCHESTRATOR_URL` in `services/policy-engine/tests/test_integration_flow.py`.

- Dev dependencies
  - Added real-integration dependencies to `requirements-dev.txt`: `boto3`, `testcontainers[redis,kafka]`, `aiokafka`.
  - Fixed AWS adapter test fixture to use real boto3 parameter names and lazy imports to avoid import-time failures.

## Remaining mock-like test patterns

- Orchestrator Unit Tests
  - Files under `services/orchestrator/tests/` use `monkeypatch` and a `FakeTemporalClient` to validate workflow routing and behavior. These are classic unit tests and do not execute against a live Temporal cluster.
  - Migration path: add an end-to-end integration test suite that connects to a real Temporal cluster (Helm or docker-compose) and drives `/v1/sessions/start` and `/v1/mao/start` via Gateway → Orchestrator, asserting real workflow outcomes. Keep unit tests for fast local dev while integration tests enforce no-mock policy.

- SLM service tests
  - Some tests in `services/slm-service/tests/` use monkeypatch for adapter selection and timeouts. Migration path is similar: add a testcontainers-based Kafka + real provider adapters to validate live message flow (`slm.requests` → `slm.responses`).

## How to run integration tests (real services)

1. Ensure a Temporal server is available and export:
   - `TEMPORAL_TARGET_HOST` (e.g., `localhost:7233`)
   - `TEMPORAL_NAMESPACE` (default `default`)

2. Set the Gateway → Orchestrator URL:
   - `SOMAGENT_GATEWAY_ORCHESTRATOR_URL=http://localhost:8001` (adjust to your Orchestrator endpoint)

3. Provide sandbox credentials for tool adapters as needed (e.g., `GITHUB_TEST_TOKEN`, `SLACK_TEST_BOT_TOKEN`).

4. Install dev deps and run tests:
   - `pip install -r requirements-dev.txt`
   - `pytest -q`

## Policy

- Product code MUST NOT contain mocks/stubs.
- Integration tests MUST use real services (Testcontainers allowed for infra like Redis/Kafka).
- Unit tests MAY use monkeypatch/fakes for speed but cannot replace integration coverage.
