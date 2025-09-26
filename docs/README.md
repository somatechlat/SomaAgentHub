# SomaGent Documentation

## New API Endpoints

### Settings Service
- **DELETE** `/v1/tenants/{tenant_id}/model-profiles/{profile_name}` – Delete a model profile (audit logged).

### Policy Engine
- **GET** `/v1/health/redis` – Simple health‑check that pings the Redis client (or placeholder) and returns `{"status": "ok"}` (200) or `{"status": "unavailable"}` (503).

- `SomaGent_Master_Plan.md` – Product philosophy and guiding principles.
- `SomaGent_Architecture.md` – Service topology, control/data flows, and KAMACHIQ-mode blueprint.
- `SomaGent_Roadmap.md` – Phase-by-phase development plan.
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

## Integration‑Test Guidance

We provide a test scaffold under `services/policy-engine/tests/test_integration_flow.py` that demonstrates how to:

1. Spin up the **Identity Service** (via FastAPI `TestClient`).
2. Issue a JWT using the `/tokens/issue` endpoint.
3. Call the **Gateway API** to create a session.
4. Invoke the **Policy Engine** `/v1/evaluate` endpoint.
5. Use the **SLM producer** to send an `slm.requests` message and verify the `slm.responses` payload.

The scaffold uses **pytest**, **httpx**, and **unittest.mock** to stub out Kafka/Redis interactions, making the test runnable locally without full Docker‑Compose.

Refer to the file for detailed comments and replace the mocks with real testcontainers when you need end‑to‑end verification.
