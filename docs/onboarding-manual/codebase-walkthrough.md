# SomaAgentHub Codebase Walkthrough

**A guided tour of the SomaAgentHub repository for new developers.**

Welcome to the codebase! This document will guide you through the structure of the repository, explaining the purpose of key directories and how the different parts of the system fit together.

---

## 🎯 Repository Structure Overview

```
somaAgentHub/
├── docs/                      # All project documentation (you are here!)
├── infra/                     # Infrastructure as Code (Terraform, Helm)
├── k8s/                       # Kubernetes manifests and Helm charts
├── services/                  # The heart of the platform: all microservices
├── scripts/                   # Automation and operational scripts
├── tests/                     # Integration and end-to-end tests
├── Makefile                   # The main entry point for development tasks
├── pyproject.toml             # Python project configuration (for Ruff)
└── README.md                  # High-level project overview
```

---

## ⚙️ The `services/` Directory

This is where all the application logic lives. The platform is built as a set of cooperating microservices.

### Core Services to Know
- **`gateway-api/`**: The public-facing entry point. It handles authentication, rate limiting, and routing requests to other services. If you're working on the API, you'll start here.
- **`orchestrator/`**: The "brain" of the system. It manages complex, long-running workflows using Temporal. This is where the core multi-agent coordination logic resides.
- **`identity-service/`**: Manages users, authentication (JWT), and authorization (RBAC).
- **`memory-gateway/`**: Provides the long-term memory for agents using a vector database (Qdrant). All semantic search and recall logic is here.
- **`policy-engine/`**: Enforces the "constitutional" rules on agent behavior to ensure safety and compliance.

### How They Interact
A typical request flows from the `gateway-api` to the `orchestrator`, which then coordinates with other services like `memory-gateway` and `policy-engine` to fulfill the request.

---

## 🏗️ The `infra/` and `k8s/` Directories

This is where we define and manage our production infrastructure.

- **`infra/terraform/`**: Contains Terraform code for provisioning cloud resources (e.g., Kubernetes clusters, databases).
- **`k8s/helm/soma-agent/`**: This is the master Helm chart for deploying the entire SomaAgentHub application to Kubernetes.
    - **`values.yaml`**: The main configuration file for the deployment.
    - **`templates/`**: Contains the Kubernetes manifest templates for each service.

---

## 🧪 The `tests/` Directory

This directory contains tests that span multiple services.

- **`tests/integration/`**: Tests the interaction between services. For example, a test might verify that the `gateway-api` can successfully communicate with the `orchestrator`.
- **`tests/e2e/`**: End-to-end tests that simulate a full user workflow, from making an API call to verifying the result in the database.

*Note: Unit tests for each service are located within the service's own directory, e.g., `services/gateway-api/tests/unit/`.*

---

## 🚀 Request Lifecycle: A Practical Trace

Let's trace a simple API call to see how the pieces fit together.

**Goal**: Start a new workflow.

1.  **HTTP Request**: The user sends `POST /v1/workflows/start` to the `gateway-api`.
2.  **Gateway API (`services/gateway-api/`)**:
    - It first authenticates the request by validating the JWT token with the `identity-service`.
    - It then forwards the validated request to the `orchestrator`.
3.  **Orchestrator (`services/orchestrator/`)**:
    - It receives the request and creates a new Temporal workflow.
    - The workflow might first call the `policy-engine` to ensure the request is allowed.
    - It then begins executing the workflow's tasks (activities), which might involve calling other services like the `memory-gateway` or `tool-service`.
4.  **Response**: The `orchestrator` immediately returns a `run_id` for the new workflow, and the workflow continues to run in the background.

---

## 🔧 The `Makefile`

The `Makefile` is your best friend for local development. It provides a set of simple commands for common tasks.

- `make dev-up`: Starts all the necessary infrastructure (databases, etc.).
- `make dev-start-services`: Runs the core microservices locally.
- `make test`: Runs the entire test suite.
- `make lint`: Checks your code for style issues.

Explore the `Makefile` to see all the available commands.

---
## 🔗 Next Steps
- **[Local Setup Guide](local-setup.md)**: Now that you understand the structure, it's time to get the code running on your machine.
```