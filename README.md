# SomaGent

Fresh monorepo scaffold for the SomaGent platform. The repository is organized around independent services (FastAPI microservices for now), shared libraries, infrastructure assets, and documentation derived from the SomaGent Master Plan.

## Repository Layout

- `services/` – Core backend services (gateway, orchestrator, constitution, policy engine, MAO, etc.). Each service ships with its own FastAPI stub, `pyproject.toml`, and `requirements.txt`.
- `libs/` – Shared Python packages (`somagent-common`, `somagent-eventbus`) for utilities and event schemas.
- `apps/admin-console/` – Placeholder for the future Admin Console front-end.
- `docs/` – Product and engineering design docs, including the Master Plan, Architecture Blueprint, Roadmap, and Security Playbook.
- `infra/` – Docker/K8s assets and other deployment artifacts. Currently contains a base Python service Dockerfile stub.
- `scripts/` – Developer and operational helper scripts (e.g., `scripts/dev/bootstrap_local_env.sh`).
- `tests/` – Test harness placeholders for service and integration coverage.

## Getting Started

1. Create a virtual environment per service:
   ```bash
   ./scripts/dev/bootstrap_local_env.sh services/gateway-api
   source services/gateway-api/.venv/bin/activate
   uvicorn app.main:app --reload --port 8080
   ```
2. Use `docker-compose.dev.yml` to spin up selected services with live-reload style mounting once dependencies are installed.
3. Extend services by fleshing out domain logic, persistence, and inter-service integrations following the docs.

## Deployment Modes

Set `SOMAGENT_DEPLOYMENT_MODE` to pick how the stack boots (docker-compose, Helm, or Terraform can inject it).

- `developer-light` – single service + mocks for rapid prototyping.
- `developer-full` – full local stack with Postgres/Redis/Kafka/Temporal stubs.
- `test` – deterministic CI profile with frozen personas.
- `test-debug` – test profile with verbose telemetry for troubleshooting.
- `production` – hardened multi-tenant configuration; training sessions require admin approval.
- `production-debug` – production with enhanced telemetry for incident response; should be temporary.

Training vs learned persona states are handled separately by the identity/training workflows.

## Next Steps

- Flesh out CI/CD, linting, and test automation per service.
- Implement persistence layers (Postgres, Redis, Kafka) and wire them into `docker-compose`.
- Translate roadmap phases into tracked issues/milestones.
- Fill `docs/design/` with vertical-slice design notes as development progresses.

Refer to the documents under `docs/` for detailed architecture, roadmap milestones, and security posture expectations.
