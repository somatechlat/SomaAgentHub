# SomaAgentHub Project Blueprint

**Date:** October 14, 2025
**Version:** 1.0

## 1. Executive Summary

This document provides a comprehensive blueprint for the SomaAgentHub platform. It synthesizes the ambitious vision laid out in the project's documentation with a clear-eyed analysis of the current codebase and infrastructure.

**Vision:** To create an enterprise-grade, autonomous software factory where AI agents, governed by a "constitution," can plan, execute, and deliver complex projects using real-world tools.

**Current State:** The project has a strong foundation, with a multi-region infrastructure defined in Terraform, a Kubernetes-native service architecture, and a powerful Temporal-based orchestrator at its core. However, a significant gap exists between the documented vision and the implemented features. Many services are scaffolds, and key enterprise features like a dedicated API Gateway, a service mesh, and robust security integrations are missing.

**Path Forward:** This blueprint proposes a phased roadmap to bridge this gap. The strategy is to:
1.  **Harden the Foundation:** Implement enterprise-grade infrastructure components.
2.  **Achieve Feature Parity:** Build out the missing functionality in the core services.
3.  **Enable Full Autonomy:** Deliver the advanced multi-agent and "KAMACHIQ Mode" capabilities.

By systematically executing this plan, SomaAgentHub can achieve its goal of becoming a leading platform for autonomous agent orchestration.

## 2. Project Vision and Core Features

Based on a thorough review of all project documentation, the core vision for SomaAgentHub is to create a platform that supports **Autonomous Project Execution**. This is underpinned by several key features:

| Feature | Description |
| :--- | :--- |
| **Multi-Agent Orchestration (MAO)** | The ability to coordinate multiple, specialized AI agents to achieve a common goal, orchestrated by a durable workflow engine (Temporal). |
| **Task Capsules** | Reusable, version-controlled templates that define a task, including the required persona, tools, knowledge, and policies. |
| **Personas** | Specialized agent configurations with specific skills, goals, and backstories (e.g., "Developer," "QA Engineer," "Project Manager"). |
| **Constitutional AI** | A central policy engine that enforces a set of rules and ethical guidelines (the "constitution") on all agent actions. |
| **Tool Service & Adapters** | A rich ecosystem of integrations with real-world tools (GitHub, Slack, AWS, etc.) to allow agents to perform meaningful work. |
| **Marketplace** | A central repository for discovering, sharing, and installing Task Capsules and Personas. |
| **KAMACHIQ Mode** | The ultimate vision of full autonomy, where a high-level command (e.g., "Build a mobile app") can trigger a complete, end-to-end project execution by a team of agents. |
| **Enterprise-Grade Infrastructure** | The entire platform is designed to be secure, scalable, observable, and resilient, suitable for production enterprise workloads. |

## 3. Current State Analysis

### 3.1. Infrastructure

The `infra` directory shows a strong, production-oriented mindset.

*   **Strengths:**
    *   **Terraform for IaC:** Manages a multi-region AWS environment (`us-west-2`, `eu-west-1`), including EKS clusters, RDS databases, and networking. This is excellent.
    *   **Kubernetes-Native:** Services are designed for Kubernetes, with detailed `.yaml` manifests and Helm charts for deployment.
    *   **Robust Observability:** Pre-configured Prometheus scraping, Grafana dashboards, and alerting rules show a commitment to monitoring.
    *   **Temporal for Orchestration:** A production-grade, multi-replica Temporal deployment is defined, which is the correct choice for this system.
*   **Weaknesses:**
    *   **Manual Integration:** While components are defined, there's a lack of a unified, automated GitOps workflow (like Argo CD) to tie it all together.
    *   **Missing Enterprise Components:** Key infrastructure pieces like a dedicated API Gateway and a Service Mesh are not present.

### 3.2. Services

The `services` directory contains a wide array of microservices, but the implementation depth varies significantly.

*   **Strengths:**
    *   **Clear Separation of Concerns:** The microservices architecture is well-defined, with each service having a clear responsibility.
    *   **Core Components are Strong:** The `orchestrator`, `gateway-api`, and `tool-service` have solid foundations. The integration of agent frameworks like AutoGen and CrewAI within the orchestrator is a smart strategic decision.
    *   **Correct Tooling:** The use of Airflow for scheduling and Flink for stream processing is appropriate and shows architectural maturity.
*   **Weaknesses:**
    *   **Scaffolding:** Many services (`analytics-service`, `billing-service`, `notification-service`) are mere scaffolds with minimal business logic.
    *   **Incomplete Features:** As detailed in the `GAP_ANALYSIS.md`, many documented features (e.g., rate limiting, RABC, sandboxed tool execution) are not fully implemented.

## 4. Proposed Target Architecture

To realize the project's vision, I propose the following target architecture, which builds upon the existing foundation and incorporates best-in-class open-source software to fill the gaps.

### 4.1. Architectural Diagram

```
                               +--------------------------+
                               |  GitOps (Argo CD / Flux) |
                               +-------------+------------+
                                             | (Deploys)
+------------------+           +-------------v------------+           +----------------------+
| Operator Console |<--------->|   API Gateway (Kong/Tyk)   |<--------->| External Tools (SaaS)|
| (UI, CLI)        |           +-------------+------------+           +----------------------+
+------------------+                         | (mTLS via Service Mesh)
                                             v
+---------------------------------------------------------------------------------------------+
|                                                                                             |
|                                KUBERNETES CLUSTER (EKS)                                     |
|                                                                                             |
|    +-----------------------------------------------------------------------------------+    |
|    |                                  Service Mesh (Istio)                             |    |
|    |                                                                                   |    |
|    |  +-----------------+   +-----------------+   +-----------------+   +------------+  |    |
|    |  | Gateway API     |-->| Orchestrator    |-->| Tool Service    |-->| Adapters   |  |    |
|    |  +-----------------+   +-------+---------+   +-----------------+   +------------+  |    |
|    |                              | (Temporal)                                        |    |
|    |  +-----------------+   +------v----------+   +-----------------+                 |    |
|    |  | Identity Service|   | MAO / Workflows |   | SLM Service     |                 |    |
|    |  +-----------------+   +-----------------+   +-----------------+                 |    |
|    |                                                                                   |    |
|    |  +-----------------+   +-----------------+   +-----------------+                 |    |
|    |  | Policy Engine   |   | Memory Gateway  |   | Analytics Svc   |                 |    |
|    |  +-----------------+   +-----------------+   +-----------------+                 |    |
|    |                                                                                   |    |
|    +-----------------------------------------------------------------------------------+    |
|                                                                                             |
+---------------------------------------------------------------------------------------------+
                 | (Events)                    | (Data)                      | (Metrics, Logs, Traces)
                 v                             v                             v
+----------------+---------+   +---------------+------------+   +------------+-------------+
|  Event Bus (Kafka)       |   |  Data Platform             |   |  Observability Platform  |
|  +---------------------+ |   |  +-----------------------+ |   |  +--------------------+  |
|  | Flink (Streaming)   | |   |  | Postgres (RDS)        | |   |  | Prometheus         |  |
|  +---------------------+ |   |  | Redis                 | |   |  | Grafana            |  |
|  +---------------------+ |   |  | Qdrant (Vector DB)    | |   |  | Loki (Logs)        |  |
|  | Data Lake (S3)      | |   |  | ClickHouse            | |   |  | Tempo (Traces)     |  |
|  +---------------------+ |   |  +-----------------------+ |   |  +--------------------+  |
|                          |   |                            |   |                          |
+--------------------------+   +----------------------------+   +--------------------------+

```

### 4.2. Key Recommendations

*   **API Gateway (Kong or Tyk):** Replace the simple FastAPI gateway with a dedicated, open-source API Gateway. This will provide robust, out-of-the-box solutions for authentication, rate limiting, and traffic management.
*   **Service Mesh (Istio):** Implement a service mesh to handle all service-to-service communication. This will provide automatic mTLS, advanced traffic control (e.g., canary releases), and deep observability without cluttering the application code.
*   **GitOps (Argo CD):** Use Argo CD to automate deployments from Git. This will create a single source of truth for the cluster's state and ensure all changes are auditable and reproducible.
*   **Data Lakehouse (S3 + Delta Lake):** Stream all events from Kafka into an S3 data lake using an open format like Delta Lake. This will create a permanent, queryable archive for analytics, model training, and compliance.
*   **Observability Stack (Prometheus, Grafana, Loki, Tempo):** The foundation is already there. Solidify this by ensuring all services are instrumented for distributed tracing (OpenTelemetry) and that logs are structured and shipped to Loki.

## 5. Phased Implementation Roadmap

This roadmap breaks the project into four distinct phases, moving from foundational hardening to full autonomous capability.

---

### Phase 1: Foundation Hardening (4-6 Weeks)

**Goal:** Solidify the infrastructure and implement the missing enterprise-grade components.

*   **Deliverables:**
    1.  **API Gateway:** Deploy Kong or Tyk as the primary ingress point.
    2.  **Service Mesh:** Deploy Istio and onboard all existing services.
    3.  **GitOps:** Set up Argo CD to manage all Kubernetes deployments from Git.
    4.  **CI/CD Pipeline:** Enhance the CI pipeline to build all services, run tests, and trigger Argo CD syncs.
    5.  **Observability:** Ensure all services export traces via OpenTelemetry and structured logs to Loki.
*   **Success Metrics:**
    *   All traffic is routed through the new API Gateway.
    *   All inter-service communication is encrypted via mTLS.
    *   All deployments are managed via GitOps.
    *   Distributed traces are available for all API calls.

---

### Phase 2: Core Service Completion (8-10 Weeks)

**Goal:** Bridge the gap identified in the `GAP_ANALYSIS.md` by building out the missing features in the core services.

*   **Deliverables:**
    1.  **Gateway API:** Implement the OpenAI-compatible endpoints.
    2.  **Orchestrator:** Implement resource allocation and human-in-the-loop review gates.
    3.  **Tool Service:** Integrate and harden the sandboxed execution environment.
    4.  **Identity Service:** Implement full RBAC, OAuth/OIDC, and SAML support.
    5.  **Scaffolded Services:** Build out the business logic for the `Analytics`, `Billing`, and `Notification` services.
*   **Success Metrics:**
    *   All "High" and "Medium" gaps from the `GAP_ANALYSIS.md` are closed.
    *   The platform fully matches the functionality described in the documentation.

---

### Phase 3: Marketplace & Ecosystem (6-8 Weeks)

**Goal:** Build the marketplace and the tooling required for a thriving ecosystem of capsules and personas.

*   **Deliverables:**
    1.  **Task Capsule Repository:** Full implementation of the capsule lifecycle (authoring, publishing, versioning, installation).
    2.  **Marketplace UI:** A user-friendly interface for discovering and managing capsules.
    3.  **Persona Synthesis:** A pipeline for creating and training new agent personas.
    4.  **Billing & Analytics Integration:** Full integration of the billing and analytics services to track usage and costs.
*   **Success Metrics:**
    *   Developers can create, publish, and share Task Capsules.
    *   Users can browse and install capsules from the marketplace.
    *   Platform usage is accurately metered and billed.

---

### Phase 4: Full Autonomy (Ongoing)

**Goal:** Realize the "KAMACHIQ Mode" vision of full, end-to-end project autonomy.

*   **Deliverables:**
    1.  **High-Level Planner:** An agent capable of decomposing a high-level goal (e.g., "Build a website") into a detailed project plan (a DAG of capsules).
    2.  **Workspace Manager:** A service that can provision and manage the resources needed for a project (e.g., Git repos, cloud environments).
    3.  **Self-Improving Agents:** Agents that can learn from their mistakes and improve their performance over time.
*   **Success Metrics:**
    *   A user can initiate a complex, multi-step project with a single command.
    *   The platform can autonomously execute the project from start to finish, using a team of agents.
    *   The success rate of autonomous projects improves over time.
