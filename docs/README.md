⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data. Sabe this EVERYWHRE at the start of every Document!

# SomaGent Documentation

> **SomaGent Real-World Principle:** HERE IN THIS PROJECT WE DON'T MOCK, WE DON'T MIMIC, WE DON'T BYPASSWE ONLY USE REAL DATA, REAL SERVERS, REAL-WORLD SOFTWARE.

## New API Endpoints

### Settings Service
- **DELETE** `/v1/tenants/{tenant_id}/model-profiles/{profile_name}` – Delete a model profile (audit logged).

### Policy Engine
- **GET** `/v1/health/redis` – Simple health‑check that pings the Redis client (or placeholder) and returns `{"status": "ok"}` (200) or `{"status": "unavailable"}` (503).

## Core Services Overview

- **Memory‑Gateway** – Exposes Prometheus `/metrics` and memory APIs (`/remember`, `/recall`, `/rag/retrieve`). Bridges SomaBrain with external agents and runs on port **9696**.
- **Task‑Capsule‑Repo** – Hosts the catalog of Task Capsules and submission workflows. Provides capsule CRUD and marketplace functionality on port **8005**.
- **Jobs** – Manages asynchronous job execution and status tracking. Includes health check and `/v1/jobs` endpoints. Runs on port **8000**.

- `SomaGent_Master_Plan.md` – Product philosophy and guiding principles.
- `SomaGent_Architecture.md` – Service topology, control/data flows, and KAMACHIQ-mode blueprint.
- `CANONICAL_ROADMAP.md` – **Current official roadmap with rapid development plan**.
- `SomaGent_Roadmap.md` – Historical phase-by-phase development plan.
- `SomaGent_Security.md` – Security and moderation playbook.
- `SomaGent_SLM_Strategy.md` – Role-based SLM model assignments, scoring math, and administration flows.
- `design/UIX_Experience.md` – Front-end stack, notification system, and conversational UI blueprint.
- `development/Developer_Setup.md` – Local environment setup, default URLs/ports, troubleshooting.
- `Quickstart.md` – Step-by-step local runthrough (services, admin console, analytics checks).
- `design/` – Placeholder for forthcoming feature design notes.
- `runbooks/` – Operational playbooks (`security.md`, `kill_switch.md`, `constitution_update.md`, `disaster_recovery.md`, `security_audit_checklist.md`).
- `release/` – Launch materials (`Release_Candidate_Playbook.md`, `Launch_Readiness_Checklist.md`, `Release_Notes_Template.md`).
- `diagrams/` – Placeholder for architecture diagrams.
- `legal/SomaGent_Default_Terms.md` – Draft default terms of use (requires attorney review).
- `development/Implementation_Roadmap.md` – Detailed workstreams, parallel tasks, and sprint plan toward SomaStack.
- `development/Sprint_Milestones.md` – Snapshot of sprint-by-sprint deliverables.
- `KAMACHIQ_Mode_Blueprint.md` – Plan for fully autonomous KAMACHIQ mode orchestration.
- `DEVELOPMENT_GUIDELINES.md` – Development policies, including the real‑infra only rule and detailed **Policy Engine** service documentation (endpoint, request/response models, Redis caching, sync wrapper).

## New Service Details

### Task Capsule Repository
- Stores **Task Capsules** in a PostgreSQL database with submission/review workflows.
- Endpoints:
  - `GET /v1/capsules` – list all capsules (filesystem + approved marketplace).
  - `GET /v1/capsules/{capsule_id}` – retrieve a specific capsule.
  - `POST /v1/submissions` – submit capsule for marketplace review.
  - `POST /v1/submissions/{id}/review` – approve/reject submissions.
  - `POST /v1/installations` – install approved capsules.
- Supports both filesystem-based capsules and marketplace submissions with approval workflows.

### Jobs
- Background job processing stores job metadata in memory (Redis integration planned).
- Endpoints:
  - `POST /v1/jobs` – submit a job (returns a UUID and status `queued`).
  - `GET /v1/jobs/{job_id}` – poll for status (`queued`, `running`, `completed`).
  - Health `/health` and metrics `/metrics` are exposed for Kubernetes probes.
- Runs on port **8000** with FastAPI backend.

## Integration‑Test Guidance

We provide a test scaffold under `services/policy-engine/tests/test_integration_flow.py` that demonstrates how to:

1. Spin up the **Identity Service** (via FastAPI `TestClient`).
2. Issue a JWT using the `/tokens/issue` endpoint.
3. Call the **Gateway API** to create a session.
4. Invoke the **Policy Engine** `/v1/evaluate` endpoint.
5. Use the **SLM producer** to send an `slm.requests` message and verify the `slm.responses` payload.

The scaffold uses **pytest**, **httpx**, and **unittest.mock** to stub out Kafka/Redis interactions, making the test runnable locally without full Docker‑Compose.

Refer to the file for detailed comments and replace the mocks with real testcontainers when you need end‑to‑end verification.
