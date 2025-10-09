# Security Architecture

> ⚠️ WE DO NOT MOCK, WE DO NOT IMITATE, WE DO NOT USE BYPASSES OR FAKE VALUES. Security controls herein must be enforced in real services.

Last Updated: October 9, 2025

## Components
- Gateway API: Auth enforcement (JWT/Bearer), request validation
- Policy Engine: Central authorization decisions (OPA-style policies)
- Identity Service: Token issuance and user identity

## Patterns
- Gateway authenticates requests; unauthorized requests rejected (e.g., 401 on protected routes)
- Orchestrator calls Policy Engine prior to executing tasks
- Services communicate over ClusterIP; public ingress controlled at gateway

## Configuration
- See `docs/deployment/Environment_Variables.md` for environment variables
- Use secrets (Kubernetes Secrets, sealed-secrets, or external secret manager)

## Hardening (recommended)
- Enforce TLS on ingress in production
- Limit service privileges and use NetworkPolicies
- Enable resource limits and liveness/readiness probes
