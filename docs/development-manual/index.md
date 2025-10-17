# Development Manual

**Contributor guide for developers building and extending SomaAgentHub.**

Welcome to the Development Manual. This guide is for **software engineers, developers, and contributors** who build, test, and extend the SomaAgentHub codebase.

---

## 📚 Quick Navigation

### Core Documentation

| Section | Purpose | Time |
|---------|---------|------|
| **[Local Setup](./local-setup.md)** | Get your development environment ready | 15 min |
| **[Codebase Overview](../onboarding-manual/codebase-walkthrough.md)** | Understand project structure & architecture | 30 min |
| **[Coding Standards](./coding-standards.md)** | Code style, linting, formatting | 20 min |
| **[Testing Guidelines](./testing-guidelines.md)** | Unit, integration, e2e testing | 30 min |
| **[API Reference](./api-reference.md)** | Service endpoints & data models | Reference |
| **[Volcano Integration Roadmap](./volcano-integration-roadmap.md)** | Scheduler adoption plan & recovery checklist | Reference |
| **[Contribution Process](./contribution-process.md)** | Git workflow, PR process, code review | 20 min |

---

## 🎯 Your First Day

**Get up and running in 2 hours:**

### Quick Start

1. Clone: `git clone https://github.com/somatechlat/SomaAgentHub.git && cd SomaAgentHub`
2. Setup: `make setup && docker-compose up -d`
3. Verify: `curl http://localhost:10000/health`
4. Explore: Read [Codebase Walkthrough](../onboarding-manual/codebase-walkthrough.md)
5. Contribute: Pick a `good-first-issue` and make your first PR

---

## 📚 Manual Contents

| Section | Description |
|---------|-------------|
| **[Local Environment Setup](local-setup.md)** | Complete development environment configuration |
| **[Coding Standards](coding-standards.md)** | Style guides, linting rules, and best practices |
| **[Testing Guidelines](testing-guidelines.md)** | Unit, integration, and E2E testing procedures |
| **[API Reference](api-reference.md)** | Complete API documentation and examples |
| **[Contribution Process](contribution-process.md)** | Git workflow, PR process, and code reviews |
| **[Volcano Integration Roadmap](volcano-integration-roadmap.md)** | Sprint plan and continuity guide for Volcano adoption |

---

## 🏗️ Codebase Overview

### Repository Structure
```
somaAgentHub/
├── services/                    # Microservices (14 services)
│   ├── gateway-api/            # Main API gateway
│   ├── orchestrator/           # Workflow coordination
│   ├── policy-engine/          # Constitutional AI governance
│   ├── memory-gateway/         # Vector memory & RAG
│   ├── identity-service/       # Authentication & RBAC
│   └── ...                     # Other services
├── infra/                      # Infrastructure as Code
│   ├── k8s/                   # Kubernetes manifests
│   ├── helm/                  # Helm charts
│   └── terraform/             # Terraform modules
├── sdk/                       # Client SDKs
│   └── python/                # Python client library
├── tests/                     # Integration & E2E tests
├── scripts/                   # Build & deployment scripts
└── docs/                      # Documentation (this manual)
```

### Technology Stack
- **Languages**: Python 3.11+, TypeScript, Bash
- **Frameworks**: FastAPI, React, Temporal
- **Databases**: PostgreSQL, Redis, Qdrant
- **Infrastructure**: Kubernetes, Helm, Docker
- **Testing**: pytest, Jest, Playwright
- **CI/CD**: GitHub Actions, Make

### Key Design Principles
1. **Microservices Architecture** - Independent, deployable services
2. **API-First Design** - OpenAPI specifications for all services
3. **Cloud-Native** - 12-factor app methodology
4. **Test-Driven Development** - Comprehensive test coverage
5. **Infrastructure as Code** - Everything versioned and reproducible

---

## 🚀 Quick Start for Developers

### 1. Environment Setup
```bash
# Clone repository
git clone https://github.com/somatechlat/somaAgentHub.git
cd somaAgentHub

# Set up Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# Install development tools
make install-dev-tools

# Start local development environment
make dev-up
```

### 2. Run Your First Test
```bash
# Unit tests
pytest tests/unit/

# Integration tests
make integration-test

# E2E tests
make e2e-test

# Specific service tests
pytest services/gateway-api/tests/
```

### 3. Make Your First Change
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and run tests
pytest services/gateway-api/tests/
ruff check .
mypy .

# Run local smoke tests
make dev-smoke-test

# Commit and push
git add .
git commit -m "feat: add new feature"
git push origin feature/your-feature-name
```

---

## 🔧 Development Workflow

### Daily Development Commands
```bash
# Start development environment
make dev-up

# Run specific service locally
make dev-run-gateway
make dev-run-orchestrator

# Watch for changes and restart
make dev-watch

# Stop development environment
make dev-down

# Clean up everything
make dev-clean
```

### Code Quality Checks
```bash
# Run all quality checks
make lint

# Individual checks
ruff check .                    # Linting
ruff format .                   # Code formatting  
mypy .                         # Type checking
pytest --cov=services/         # Test coverage
bandit -r services/            # Security scanning
```

### Service Development
```bash
# Add new service
make create-service SERVICE_NAME=my-new-service

# Generate API client from OpenAPI spec
make generate-client SERVICE=gateway-api

# Update database migrations
make migrate SERVICE=identity-service

# Build service Docker image
make build-service SERVICE=gateway-api
```

---

## 📊 Testing Strategy

### Test Pyramid
1. **Unit Tests (70%)** - Fast, isolated tests for individual functions/classes
2. **Integration Tests (20%)** - Service-to-service communication tests
3. **E2E Tests (10%)** - Full user journey tests

### Test Categories
- **Unit Tests**: `/services/{service}/tests/unit/`
- **Integration Tests**: `/tests/integration/`  
- **E2E Tests**: `/tests/e2e/`
- **Load Tests**: `/tests/performance/`
- **Chaos Tests**: `/tests/chaos/`

### Running Tests
```bash
# All tests
make test

# Specific test categories
make test-unit
make test-integration  
make test-e2e

# Service-specific tests
make test-service SERVICE=orchestrator

# Coverage report
make test-coverage
```

---

## 🛠️ Service Development Guide

### Creating a New Service

1. **Generate Service Skeleton**
```bash
make create-service SERVICE_NAME=my-service PORT=8099
```

2. **Service Structure**
```
services/my-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── api/                 # API routes
│   ├── core/               # Business logic
│   ├── models/             # Data models
│   └── deps.py             # Dependencies
├── tests/
├── Dockerfile
├── requirements.txt
└── openapi.yaml           # API specification
```

3. **Essential Files**
```python
# app/main.py
from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="My Service", version="1.0.0")
app.include_router(router, prefix="/v1")

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

### API Development Standards

1. **OpenAPI Specification** - All endpoints must be documented
2. **Versioned APIs** - Use `/v1/`, `/v2/` prefixes
3. **Standard HTTP Status Codes** - Follow REST conventions
4. **Error Handling** - Consistent error response format
5. **Authentication** - JWT token validation on protected endpoints

### Database Integration
```python
# models/example.py
from sqlalchemy import Column, Integer, String
from app.db.base_class import Base

class ExampleModel(Base):
    __tablename__ = "examples"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)

# Alembic migration
alembic revision --autogenerate -m "Add example model"
alembic upgrade head
```

---

## 🎯 Contribution Guidelines

### Git Workflow
1. **Fork Repository** (external contributors)
2. **Create Feature Branch** from `main`
3. **Make Changes** following coding standards
4. **Write Tests** for new functionality
5. **Run Quality Checks** before committing
6. **Submit Pull Request** with clear description
7. **Address Review Feedback**
8. **Merge After Approval**

### Commit Message Convention
```bash
# Format: type(scope): description
feat(gateway): add new authentication endpoint
fix(orchestrator): resolve workflow timeout issue
docs(api): update OpenAPI specifications
test(memory): add unit tests for recall functionality
chore(ci): update GitHub Actions workflow
```

### Pull Request Process
1. **Clear Title and Description**
2. **Link Related Issues** (#123)
3. **Include Screenshots** (for UI changes)
4. **Add Breaking Change Notes** (if applicable)
5. **Ensure CI Passes** (all checks green)
6. **Request Reviews** from code owners

---

## 📚 Resources & References

### Documentation
- **[Architecture Decisions](../technical-manual/architecture.md)** - System design rationale
- **[API Integration Guide](../SOMAGENTHUB_INTEGRATION_GUIDE.md)** - Complete API examples
- **[Deployment Guide](../technical-manual/deployment.md)** - Production deployment

### External Resources
- **[FastAPI Documentation](https://fastapi.tiangolo.com/)**
- **[Temporal Documentation](https://docs.temporal.io/)**
- **[PostgreSQL Documentation](https://www.postgresql.org/docs/)**
- **[Kubernetes API Reference](https://kubernetes.io/docs/reference/)**

### Development Tools
- **IDE Extensions**: Python, Kubernetes, Docker plugins
- **Debugging**: VS Code debugger configurations in `.vscode/`
- **Database GUI**: pgAdmin, DBeaver for PostgreSQL management
- **API Testing**: Postman collections in `/api-collections/`

---

## 🔗 Related Manuals

- **[User Manual](../user-manual/)** - Understanding the user experience you're building
- **[Technical Manual](../technical-manual/)** - Deployment and operational context  
- **[Onboarding Manual](../onboarding-manual/)** - Quick project orientation

---

**Ready to contribute to SomaAgentHub? Start with the [Local Setup Guide](local-setup.md) and join our community of developers building the future of agent orchestration!**
