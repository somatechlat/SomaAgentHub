# Sprint: OPA Integration

**Objective**: Connect the platform services to the OPA policy engine for runtime policy enforcement.

## Tasks
- Add a client library (e.g., `opa` HTTP client) or configure OPA sidecar.
- Implement policy check calls in `gateway-api` middleware and orchestrator workflow steps.
- Create a shared policy‑engine SDK (`services/policy-engine/app/client.py`) for other services.
- Store policy bundles in Git and load them on startup.
- Write integration tests that simulate policy denials.
- Deploy OPA via Helm and configure policy bundles.

## Owner
- Security / Platform team

## Status
- **Not started** – policy‑engine service exists but not wired.
