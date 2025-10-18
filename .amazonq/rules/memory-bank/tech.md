# SomaAgentHub Technology Stack

## Programming Languages & Versions
- **Python 3.11+** - Primary backend language for all services
- **TypeScript/React** - Frontend applications (admin console, dashboards)
- **Bash** - Operations scripts and automation
- **SQL** - Database schemas and migrations
- **YAML** - Configuration and infrastructure definitions

## Core Backend Technologies
- **FastAPI** - REST API framework for all HTTP services
- **Temporal** - Workflow orchestration and durable execution
- **Redis** - Caching, session storage, and real-time state
- **PostgreSQL** - Primary transactional database
- **Qdrant** - Vector database for semantic search and embeddings

## Infrastructure & Deployment
- **Kubernetes 1.24+** - Container orchestration platform
- **Helm 3+** - Package manager and templating for K8s deployments
- **Kind** - Local Kubernetes development clusters
- **Docker & Docker Compose** - Containerization and local development
- **Terraform** - Infrastructure as Code for cloud resources

## Development Tools & Standards
- **Ruff** - Python linting and code formatting (line-length: 120)
- **MyPy** - Static type checking for Python
- **Pytest** - Testing framework with fixtures and mocking
- **Pre-commit hooks** - Code quality enforcement
- **GitHub Actions** - CI/CD automation

## Observability & Monitoring
- **Prometheus** - Metrics collection and alerting
- **Grafana** - Visualization dashboards and monitoring
- **Loki** - Log aggregation and search
- **OpenTelemetry** - Distributed tracing and observability
- **Jaeger/Tempo** - Trace storage and analysis

## Security & Compliance
- **SPIFFE/SPIRE** - Zero-trust identity and authentication
- **Vault** - Secrets management and rotation
- **OPA (Open Policy Agent)** - Policy enforcement engine
- **Trivy** - Container vulnerability scanning
- **Syft** - Software Bill of Materials (SBOM) generation

## Data & Analytics
- **ClickHouse** - Analytics database for time-series data
- **Apache Kafka** - Event streaming and message queues
- **Apache Flink** - Stream processing for real-time analytics
- **Apache Airflow** - Workflow scheduling and data pipelines

## Development Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Local Development
```bash
# Start local infrastructure (Temporal + Redis)
make dev-up

# Start core services locally
make dev-start-services

# Port forward gateway for testing
make port-forward-gateway LOCAL=8080 REMOTE=10000
```

### Build & Deploy
```bash
# Build changed service images
make build-changed

# Deploy to local Kind cluster
make start-cluster

# Run smoke tests
make k8s-smoke
```

### Testing
```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run end-to-end tests
make test-e2e
```

### Code Quality
```bash
# Run linting
ruff check .

# Run type checking
mypy services/

# Format code
ruff format .
```

## Configuration Management
- **Environment Variables** - Runtime configuration via `.env` files
- **Helm Values** - Kubernetes deployment configuration
- **pyproject.toml** - Python project configuration and dependencies
- **Makefile** - Build automation with 40+ targets

## Port Allocation
- **10000** - Gateway API (public ingress)
- **10001** - Orchestrator service
- **10002** - Identity service
- **10018** - Memory gateway (optional)
- **10020** - Policy engine (optional)
- **7233** - Temporal server
- **6379** - Redis server
- **5432** - PostgreSQL database