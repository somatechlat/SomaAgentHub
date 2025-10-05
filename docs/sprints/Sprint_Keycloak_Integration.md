# Sprint: Keycloak Integration

**Objective**: Wire up Keycloak authentication across the platform (gateway‑api, orchestrator, other services).

## Tasks
- Add `python-keycloak` (or `authlib`) dependency.
- Implement JWT validation middleware in `gateway-api/app/core/middleware.py`.
- Create a reusable Keycloak client wrapper.
- Update service configs to read `KEYCLOAK_URL`, `REALM`, `CLIENT_ID`, `CLIENT_SECRET`.
- Write unit tests for token validation and error handling.
- Deploy Keycloak via Helm (docs/reference) and configure realms.

## Owner
- Platform / Security team

## Status
- **Not started** – placeholders exist, implementation pending.
