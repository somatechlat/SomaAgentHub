# SomaAgentHub Project Structure

## Root Directory Organization

### Core Application Code
- **`services/`** - Microservices architecture with 20+ specialized services
- **`apps/`** - Frontend applications (admin console, UI components)
- **`sdk/`** - Python SDK for agent development and integration
- **`cli/`** - Command-line interface for platform management

### Infrastructure & Deployment
- **`infra/`** - Infrastructure as Code (Terraform, Docker Compose, configs)
- **`k8s/`** - Kubernetes manifests, Helm charts, and deployment configs
- **`scripts/`** - Automation scripts for build, deploy, test, and operations

### Documentation & Guides
- **`docs/`** - Comprehensive documentation organized by audience
  - `development-manual/` - Developer workflows and coding standards
  - `technical-manual/` - Architecture, deployment, and runbooks
  - `onboarding-manual/` - New contributor guidance
  - `user-manual/` - End-user features and tutorials

### Testing & Quality
- **`tests/`** - Multi-layered testing strategy
  - `unit/` - Service-level unit tests
  - `integration/` - Cross-service integration tests
  - `e2e/` - End-to-end workflow validation
  - `performance/` - Load testing and benchmarks
  - `security/` - Security validation suites

## Core Services Architecture

### Gateway Layer (Port 10000)
- **`gateway-api/`** - Public ingress for UI, CLI, and partner integrations
- Handles wizard flows and session fan-out
- FastAPI-based with authentication and rate limiting

### Orchestration Layer (Port 10001)
- **`orchestrator/`** - Multi-agent workflow coordination
- Temporal integration for durable workflows
- Session management and agent lifecycle

### Identity & Security (Port 10002)
- **`identity-service/`** - Access token issuance and validation
- **`policy-engine/`** - Rule-based guardrails and compliance
- **`constitution-service/`** - Governance framework and policies

### Memory & Storage (Port 10018)
- **`memory-gateway/`** - Vector and key/value storage abstraction
- Qdrant integration for semantic search and recall
- Redis for real-time state sharing

### Specialized Services
- **`mao-service/`** - Multi-Agent Orchestrator workflows
- **`slm-service/`** - Small Language Model management
- **`tool-service/`** - External tool integration and adapters
- **`analytics-service/`** - Metrics collection and analysis
- **`billing-service/`** - Usage tracking and cost management

## Infrastructure Components

### Container Orchestration
- **Kubernetes manifests** in `k8s/` with RBAC, networking, storage
- **Helm charts** for templated deployments with environment overrides
- **Kind configuration** for local development clusters

### Observability Stack
- **Prometheus** for metrics collection
- **Grafana** for visualization and dashboards
- **Loki** for log aggregation
- **OpenTelemetry** for distributed tracing

### Data Layer
- **PostgreSQL** for transactional data
- **Redis** for caching and real-time state
- **ClickHouse** for analytics and time-series data
- **Qdrant** for vector storage and semantic search

## Development Workflow

### Build System
- **Makefile** with 40+ targets for common operations
- **Docker** multi-stage builds for optimized images
- **GitHub Actions** for CI/CD automation

### Code Organization Patterns
- **Service isolation** with independent deployments
- **Shared libraries** in `services/common/` for cross-cutting concerns
- **Configuration management** via environment variables and Helm values
- **API-first design** with OpenAPI specifications

### Testing Strategy
- **Pytest** for Python services with fixtures and mocking
- **Integration harnesses** for cross-service validation
- **Smoke tests** for deployment verification
- **Load testing** with Locust scenarios