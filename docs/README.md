# SomaAgentHub Documentation

![Version](https://img.shields.io/badge/version-1.0.0-blue)

## Quick Overview
- **What**: Production-ready orchestration platform for autonomous agents built on Kubernetes, Temporal, and FastAPI.
- **Who**: Platform engineers, AI/ML engineers, DevOps teams, enterprise developers, AI agents.
- **Where**: Docs live under the `/docs/` folder and are published via MkDocs-Material.

---
## Documentation Structure
| Manual | Path | Audience |
|--------|------|----------|
| User Manual | `docs/user-manual/` | End-users, product managers |
| Technical Manual | `docs/technical-manual/` | SREs, Ops, Platform engineers |
| Development Manual | `docs/development-manual/` | Contributors, developers |
| Onboarding Manual | `docs/onboarding-manual/` | New hires, contractors |
| Agent Onboarding | `docs/agent-onboarding/` | AI agents, automation bots |

## Core Services Architecture

| Service | Host Port | Container Port | Purpose |
|---------|-----------|----------------|---------|
| **Gateway API** | 10000 | 8000 | Public ingress for UI, CLI, and partner integrations. Handles wizard flows and session fan-out. |
| **Orchestrator** | 10001 | 8000 | Coordinates multi-agent workflows, talks to Temporal, identity, and policy services. |
| **Identity Service** | 10002 | 8000 | Issues access tokens and validates identities for every agent-facing request. |
| **Memory Gateway** | 10021 | 8000 | Stores and retrieves long-term context via Qdrant for agent recall. |
| **Policy Engine** | 10020 | 8000 | Provides rule-based guardrails and compliance enforcement. |

## Technology Stack
- **Languages**: Python 3.11+, TypeScript/React, Bash
- **Core Services**: FastAPI, Temporal, Redis, PostgreSQL, Qdrant
- **Infrastructure**: Kubernetes, Helm, Kind, Terraform
- **Observability**: Prometheus, Grafana, Loki, OpenTelemetry

## ISO/IEC Compliance

This documentation follows these international standards:
- **ISO/IEC 26514**: User documentation requirements
- **ISO/IEC 26515**: Online documentation delivery
- **ISO/IEC 26512**: Documentation processes & governance
- **ISO/IEC 26513**: Maintenance documentation
- **ISO/IEC 42010**: Architecture description
- **ISO 21500**: Project management documentation