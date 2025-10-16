# SomaAgentHub System Architecture

**A detailed overview of the SomaAgentHub platform's components, design principles, and data flow.**

This document provides a comprehensive architectural overview for platform engineers, SREs, and system administrators. It details the microservices architecture, guiding principles, data flow patterns, and technology stack that power SomaAgentHub.

---

## 🎯 Guiding Principles

The architecture is built on a foundation of modern, cloud-native principles to ensure scalability, resilience, and maintainability.

| Principle | Description | Implementation |
|---|---|---|
| **Microservices** | Each service is independently deployable, scalable, and maintainable. | 14+ FastAPI services, each in its own container. |
| **API-First Design** | Services communicate through well-defined, versioned APIs. | OpenAPI specifications for every service. |
| **Cloud-Native** | Designed for containerization and orchestration. | Kubernetes-native, 12-factor app methodology. |
| **Asynchronous & Event-Driven** | Long-running tasks are handled asynchronously for resilience. | Temporal for workflow orchestration, Redis for caching. |
| **Infrastructure as Code (IaC)** | All infrastructure is defined and managed in version control. | Kubernetes manifests, Helm charts, and Terraform. |
| **Comprehensive Observability** | The system is designed to be monitored and understood. | Prometheus metrics, Grafana dashboards, Loki logging. |
| **Security by Design** | Security is integrated at every layer of the platform. | JWT authentication, RBAC, secrets management. |

---

## 🏗️ High-Level Architecture

SomaAgentHub operates as a layered system, separating concerns from public-facing APIs down to the underlying infrastructure.

```
┌─────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                    │
│         (Admin Console, CLI, External Integrations)     │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                       GATEWAY LAYER                     │
│      (Gateway API: Auth, Rate Limiting, Routing)        │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                   ORCHESTRATION LAYER                   │
│      (Orchestrator Service, Temporal Workflows)         │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                      SERVICE LAYER                      │
│ (Policy, Memory, Identity, Tools, SLM, and other services)│
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                   INFRASTRUCTURE LAYER                  │
│      (PostgreSQL, Redis, Qdrant, Kubernetes)            │
└─────────────────────────────────────────────────────────┘
```

---

## ⚙️ Core Service Responsibilities

The platform is composed of specialized microservices, each with a distinct responsibility.

| Service | Container Port | Purpose & Key Features |
|---|---|---|
| **Gateway API** | 10000 | **Public Entry Point**: Handles all incoming traffic, authentication (JWT), rate limiting, request validation, and routing to internal services. Provides OpenAI-compatible endpoints. |
| **Orchestrator** | 10001 | **Workflow Coordination**: The "brain" of the system. Manages multi-agent workflows using Temporal, coordinates tasks, and maintains state for long-running processes. |
| **Identity Service** | 10002 | **Authentication & Authorization**: Manages users, tenants, and roles. Issues and validates JWT tokens and enforces Role-Based Access Control (RBAC). |
| **Policy Engine** | 10003 | **Governance & Safety**: Enforces constitutional rules and ethical constraints on agent behavior. Evaluates actions against defined policies before execution. |
| **Memory Gateway** | 10004 | **Intelligent Memory**: Provides semantic storage and retrieval for agent context and conversation history using the Qdrant vector database for RAG. |
| **SLM Service** | 10005 | **Language Model Access**: Manages interactions with various LLMs, whether local models or external APIs (e.g., OpenAI, Azure). |
| **Tool Service** | 10006 | **External Integrations**: Provides a registry and execution environment for 16+ adapters that connect agents to external tools like GitHub, Slack, and AWS. |
| **Analytics Service**| 10007 | **Usage & Metrics**: Collects and processes data for reporting, cost tracking, and performance analytics, often using a ClickHouse backend. |

### Local Docker Cluster Ports

For local development the `scripts/docker-cluster.sh` helper reserves consecutive host ports starting at 10000 (or the next available slot) and writes them to `.env`. The current Docker Compose stack exposes the following endpoints:

| Service | Host Port (from `.env`) | Container Port | Notes |
|---|---|---|---|
| Gateway API | `${GATEWAY_API_PORT}` (e.g., 10006) | 10000 | `/ready` for liveness, `/healthz` may warn when optional upstreams are offline. |
| Orchestrator | `${ORCHESTRATOR_PORT}` (e.g., 10007) | 10001 | Requires Temporal at `temporal-server:7233`. |
| Identity Service | `${IDENTITY_SERVICE_PORT}` (e.g., 10008) | 10002 | Issues JWTs, depends on Redis. |
| Redis | `${REDIS_PORT}` (e.g., 10009) | 6379 | Backing cache/message bus for Identity and orchestrator tasks. |
| Temporal UI/API | n/a | 7233 / 8080 | Internal only; reachable from other containers in the compose network. |

> Check the generated `.env` file after each `docker-cluster.sh` run to confirm the actual host bindings when multiple stacks share the machine.

---

## 🔄 Data Flow & Communication

### Request Lifecycle Example: Chat Completion

1.  **Client Request**: A user sends a request to `POST /v1/chat/completions` on the **Gateway API**.
2.  **Authentication**: The Gateway API validates the JWT token with the **Identity Service**.
3.  **Routing**: The request is forwarded to the **Orchestrator Service**.
4.  **Policy Check**: The Orchestrator sends the prompt to the **Policy Engine** to ensure it complies with safety and governance rules.
5.  **Memory Retrieval**: The Orchestrator queries the **Memory Gateway** to fetch relevant context and conversation history for the user.
6.  **LLM Interaction**: The Orchestrator, now with full context, sends the enriched prompt to the **SLM Service** for processing by a language model.
7.  **Response & Memory Update**: The LLM's response is received. The Orchestrator sends the new conversation turn to the **Memory Gateway** to be stored.
8.  **Final Response**: The final response is streamed back through the Gateway API to the client.

### Asynchronous Workflows

For complex tasks (e.g., "research and write a report"), the Orchestrator initiates a **Temporal Workflow**. This workflow defines a series of durable tasks (activities) that are executed by worker agents, ensuring the process can survive crashes and run for hours or days if needed.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend Services** | Python 3.11+, FastAPI | High-performance, modern API development. |
| **Frontend** | TypeScript, React | Admin console and user-facing interfaces. |
| **Workflow Engine** | Temporal | Durable, scalable, and resilient orchestration. |
| **Primary Database** | PostgreSQL | Relational data storage (users, policies, etc.). |
| **Caching & Messaging**| Redis | Caching, session storage, real-time state. |
| **Vector Database** | Qdrant | High-performance semantic search for memory. |
| **Infrastructure** | Kubernetes, Docker, Helm | Containerization, orchestration, and deployment. |
| **Observability** | Prometheus, Grafana, Loki | Metrics, dashboards, and log aggregation. |
| **CI/CD** | GitHub Actions, Make | Automated builds, testing, and deployments. |

---

## 🔗 Related Documentation

- **[Deployment Guide](deployment.md)**: For instructions on how to deploy this architecture.
- **[Monitoring Guide](monitoring.md)**: For details on how to observe system health.
- **[Development Manual](../development-manual/index.md)**: For information on how to contribute to these services.
