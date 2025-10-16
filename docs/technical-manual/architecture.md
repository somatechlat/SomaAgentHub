# SomaAgentHub System Architecture

<!-- markdownlint-disable MD013 -->

> _Version: soma_integration (last updated 2025-10-16)_

## Purpose

Provide a single source of truth for how SomaAgentHub is assembled, which components exist today, and how they interact across environments (local Docker, staging, production clusters).

## Audience

| Role | Why this page matters |
|---|---|
| Platform engineers & SREs | Understand service boundaries, dependencies, and failure domains before operating or extending the platform. |
| Application developers | Locate integration points, required upstreams, and shared infrastructure prior to feature work. |
| Security & compliance reviewers | Validate data flows, trust zones, and enforcement layers against policy requirements. |
| External partners | Confirm open-source dependencies, container images, and orchestration touchpoints for integration planning. |

## Prerequisites

- Familiarity with containerized deployments (Docker, Kubernetes basics).
- Access to the repository (`somaAgentHub`) and the local helper script `scripts/docker-cluster.sh`.
- Installed tooling: Docker Engine 24+, Docker Compose v2, and (optionally) Kind for local Kubernetes validation.
- Optional tooling used in verification steps: PostgreSQL `psql` client and MinIO Client (`mc`).

---

**A detailed overview of the SomaAgentHub platform's components, design principles, and data flow.**

This document provides a comprehensive architectural overview for platform engineers, SREs, and system administrators. It details the microservices architecture, guiding principles, data flow patterns, and technology stack that power SomaAgentHub.

---

## 🎯 Guiding Principles

The architecture is built on a foundation of modern, cloud-native principles to ensure scalability, resilience, and maintainability.

| Principle | Description | Implementation |
|---|---|---|
| **Microservices** | Each service is independently deployable, scalable, and maintainable. | FastAPI services packaged as individual containers under `services/`. |
| **API-First Design** | Services communicate through well-defined, versioned APIs. | OpenAPI specifications for every service. |
| **Cloud-Native** | Designed for containerization and orchestration. | Kubernetes-native, 12-factor app methodology. |
| **Asynchronous & Event-Driven** | Long-running tasks are handled asynchronously for resilience. | Temporal for workflow orchestration, Redis for caching. |
| **Infrastructure as Code (IaC)** | All infrastructure is defined and managed in version control. | Kubernetes manifests, Helm charts, and Terraform. |
| **Comprehensive Observability** | The system is designed to be monitored and understood. | Prometheus metrics, Grafana dashboards, Loki logging. |
| **Security by Design** | Security is integrated at every layer of the platform. | JWT authentication, RBAC, secrets management. |

---

## 🏗️ High-Level Architecture

SomaAgentHub operates as a layered system, separating concerns from public-facing APIs down to the underlying infrastructure.

```text
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

The docker-compose stack delivers the core runtime needed for local development and integration testing.

| Service | Default Container Port | Purpose & Key Features |
|---|---|---|
| **Gateway API** | 10000 | Handles ingress traffic, JWT enforcement, rate limiting, request validation, and routing to internal services. Provides OpenAI-compatible endpoints for agents and external clients. |
| **Orchestrator** | 10001 | Coordinates multi-agent workflows using Temporal, maintains conversational state, and orchestrates long-running tasks. |
| **Identity Service** | 10002 | Manages tenants, roles, and JWT issuance. Integrates with Redis for session caching and policy lookups. |
| **Temporal Server** | 7233 (gRPC) | Supplies workflow orchestration and durable timers through `temporalio/auto-setup`. |
| **Temporal PostgreSQL** | 5432 | Stores Temporal metadata, task queues, and workflow history. |
| **Redis** | 6379 | Provides caching and lightweight messaging for identity and orchestration components. |
| **Application PostgreSQL** | 5432 | Persists domain data for application services. |
| **Qdrant** | 6333 | Offers vector storage and similarity search for semantic memory and retrieval-augmented generation. |
| **ClickHouse** | 8123 | Serves analytical queries and event ingestion for reporting workloads. |
| **MinIO** | 9000 (API) / 9001 (Console) | Supplies S3-compatible object storage for binary artifacts and dataset snapshots. |

Additional services (for example `policy-engine`, `memory-gateway`, `slm-service`, `tool-service`, and `analytics-service`) live under `services/` and are deployed as needed per environment. Each directory contains its own README with detailed responsibilities and configuration.

### Local Docker Stack (docker-compose)

The `docker-compose.yml` file defines the default local topology. `scripts/docker-cluster.sh` safeguards port allocation and generates `.env` each run.

| Service | Image (pinned) | Host Port (`.env`) | Container Port | Health Check |
|---|---|---|---|---|
| Gateway API | Built from `services/gateway-api` | `${GATEWAY_API_PORT}` | 10000 | `GET /ready` |
| Orchestrator | Built from `services/orchestrator` | `${ORCHESTRATOR_PORT}` | 10001 | `GET /ready` |
| Identity Service | Built from `services/identity-service` | `${IDENTITY_SERVICE_PORT}` | 10002 | `GET /ready` |
| Redis | `redis:7-alpine` | `${REDIS_PORT}` | 6379 | `redis-cli ping` |
| App PostgreSQL | `postgres:16.4-alpine` | `${APP_POSTGRES_PORT}` | 5432 | `pg_isready` |
| Temporal (server) | `temporalio/auto-setup:1.22.4` | Internal | 7233 | `tctl cluster health` |
| Temporal PostgreSQL | `postgres:15-alpine` | Internal | 5432 | `pg_isready` |
| Qdrant | `qdrant/qdrant:v1.11.0@sha256:22a2d455837380d5fa1a3455b87b4fe7af30aa4f4712f8a57027c61022113796` | `${QDRANT_PORT}` | 6333 | `GET /healthz` |
| ClickHouse | `clickhouse/clickhouse-server:24.7-alpine@sha256:3187267104ffa306377a9d41eedcdb9c3fade52db855f92021fb1498a070c7fb` | `${CLICKHOUSE_HTTP_PORT}` | 8123 | `GET /ping` |
| MinIO (API/Console) | `minio/minio:latest@sha256:a1a8bd4ac40ad7881a245bab97323e18f971e4d4cba2c2007ec1bedd21cbaba2` | `${MINIO_API_PORT}` / `${MINIO_CONSOLE_PORT}` | 9000 / 9001 | `GET /minio/health/live` |

- Health probes are mirrored from Kubernetes readiness checks to keep behavior consistent across environments.
- The helper script prints the reserved host ports at startup; re-run it after stopping the stack to release old allocations.

### Container Image Provenance

All third-party containers in the local stack are pinned to official open-source images and verified digests:

- PostgreSQL apps: `postgres:16.4-alpine` (Docker Official Image).
- Temporal dependencies: `postgres:15-alpine`, `temporalio/auto-setup:1.22.4`.
- Redis cache: `redis:7-alpine`.
- Vector store: `qdrant/qdrant:v1.11.0@sha256:22a2d455837380d5fa1a3455b87b4fe7af30aa4f4712f8a57027c61022113796`.
- Analytics warehouse: `clickhouse/clickhouse-server:24.7-alpine@sha256:3187267104ffa306377a9d41eedcdb9c3fade52db855f92021fb1498a070c7fb`.
- Object storage: `minio/minio:latest@sha256:a1a8bd4ac40ad7881a245bab97323e18f971e4d4cba2c2007ec1bedd21cbaba2`.

Documented digests ensure reproducible builds and satisfy the "official OSS only" requirement in ROADMAP-2.5.

---

## 🔄 Data Flow & Communication

### Request Lifecycle Example: Chat Completion

1. **Client Request**: A user sends a request to `POST /v1/chat/completions` on the **Gateway API**.
2. **Authentication**: The Gateway API validates the JWT token with the **Identity Service**.
3. **Routing**: The request is forwarded to the **Orchestrator Service**.
4. **Policy Check (when deployed)**: The Orchestrator calls the **Policy Engine** to evaluate governance rules before executing downstream actions.
5. **Memory Retrieval (when deployed)**: The Orchestrator queries the **Memory Gateway** to fetch relevant context and conversation history for the user. The gateway uses Qdrant as the backing store.
6. **LLM Interaction**: The Orchestrator, now with full context, sends the enriched prompt to the **SLM Service** for processing by a language model.
7. **Response & Memory Update**: The LLM's response is received. The Orchestrator sends the new conversation turn to the **Memory Gateway** to be stored.
8. **Final Response**: The final response is streamed back through the Gateway API to the client.

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

## 🔧 Service-Specific Troubleshooting

For detailed troubleshooting of individual services, refer to the following common issues and solutions:

| Service | Port | Health Endpoint | Common Issue | Solution |
|---------|------|-----------------|--------------|----------|
| **Gateway API** | 10000 | `GET /ready` | 502 Bad Gateway | Check if Orchestrator (10001) and Identity (10002) are healthy |
| **Orchestrator** | 10001 | `GET /ready` | Temporal connection failed | Ensure Temporal server is running with `docker ps \| grep temporal` |
| **Identity Service** | 10002 | `GET /ready` | Redis unavailable | Check Redis health: `redis-cli ping` should return PONG |
| **Redis** | 10003 | `redis-cli ping` | Connection refused | Restart with: `docker restart somaagenthub-redis` |
| **Memory Gateway** | 8000 | `GET /healthz` | Qdrant unavailable | Check Qdrant: `curl http://localhost:10005/healthz` |
| **Qdrant** | 10005 | `GET /healthz` | Storage full | Check volume: `docker exec somaagenthub-qdrant du -sh /qdrant/storage` |
| **ClickHouse** | 10006 | `GET /ping` | Port conflict | Free port 10006: `lsof -i :10006` and kill process |
| **MinIO** | 10007/10008 | `GET /minio/health/live` | Login failed | Use default credentials: `somaagent` / `local-developer` |

**For complete runbook procedures, see**: `docs/technical-manual/runbooks/service-is-down.md`

---

1. Run `scripts/docker-cluster.sh` and confirm all services start:

    ```bash
    ./scripts/docker-cluster.sh
    docker compose ps
    ```

2. Verify key health endpoints:

    ```bash
    curl http://127.0.0.1:${GATEWAY_API_PORT}/ready
    curl http://127.0.0.1:${QDRANT_PORT}/healthz
    curl http://127.0.0.1:${CLICKHOUSE_HTTP_PORT}/ping
    ```

3. Ensure data services are reachable via CLI (requires `psql` and `mc`):

    ```bash
    PGPASSWORD=somaagent psql -h 127.0.0.1 -p ${APP_POSTGRES_PORT} -U somaagent -c "select now();"
    mc alias set local http://127.0.0.1:${MINIO_API_PORT} somaagent local-developer
    ```

Successful responses confirm the compose topology matches this architecture description.

## ⚠️ Common Issues and Fixes

| Symptom | Likely Cause | Resolution |
|---|---|---|
| `docker compose up` fails with `manifest unknown` | Image tag missing or moved. | Pull the pinned digest listed above; ensure Docker Hub credentials are valid if rate limited. |
| Temporal health check loops forever | `temporal-postgres` not ready or port collision. | Delete `.env`, rerun `scripts/docker-cluster.sh`, ensure ports are free (`lsof -i :<port>`). |
| Gateway `/ready` returns 502 | Upstream orchestrator or identity unavailable. | Check `docker compose logs orchestrator` and identity; restart dependent services once healthy. |
| Qdrant health endpoint 404 | Old container tag cached locally. | `docker image rm qdrant/qdrant:latest`, rerun helper to pull digest-pinned image. |

---

## 🔗 Related Documentation

- **[Deployment Guide](deployment.md)**: For instructions on how to deploy this architecture.
- **[Monitoring Guide](monitoring.md)**: For details on how to observe system health.
- **[Development Manual](../development-manual/index.md)**: For information on how to contribute to these services.
- **[ROADMAP-2.5](../ROADMAP-2.5.md)**: Strategic plan for Istio service mesh, policy plane, and observability enhancements referenced in this architecture.

<!-- markdownlint-restore -->
