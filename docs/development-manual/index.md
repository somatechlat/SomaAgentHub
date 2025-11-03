# SomaAgentHub Development Manual

**Complete guide for software engineers and contributors**

> Master the development, testing, and contribution processes for SomaAgentHub's enterprise agent orchestration platform.

---

## 📋 Overview

This Development Manual provides comprehensive guidance for engineers working on SomaAgentHub. It covers local development setup, coding standards, testing practices, API development, and contribution workflows.

### Target Audience

- **Software Engineers** - Core platform development
- **Frontend Developers** - UI and dashboard development
- **Backend Developers** - Service and API development
- **DevOps Engineers** - Infrastructure as code and automation
- **Open Source Contributors** - Community contributions and extensions

---

## 🏗️ Development Architecture

**SomaAgentHub Development Stack:**

```
┌─────────────────────────────────────────────────────────────┐
│                Development Environment                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Python    │  │ TypeScript  │  │    Bash     │         │
│  │  Services   │  │   React     │  │   Scripts   │         │
│  │  (FastAPI)  │  │    Apps     │  │ (Automation)│         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Docker    │  │ Kubernetes  │  │   Temporal  │         │
│  │ Containers  │  │   Local     │  │  Workflows  │         │
│  │   (Kind)    │  │  (Kind)     │  │   (Local)   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Development Tools                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │    Ruff     │  │    MyPy     │  │   Pytest    │         │
│  │  (Linting)  │  │ (Type Check)│  │  (Testing)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Pre-commit  │  │   GitHub    │  │    Make     │         │
│  │   Hooks     │  │   Actions   │  │ (Automation)│         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📚 Manual Contents

| Section | Description | Audience |
|---------|-------------|----------|
| [Local Setup](local-setup.md) | Development environment configuration | All developers |
| [Coding Standards](coding-standards.md) | Style guides and best practices | All developers |
| [Testing Guidelines](testing-guidelines.md) | Testing strategies and frameworks | All developers |
| [API Reference](api-reference.md) | REST API documentation | Backend developers |
| [Contribution Process](contribution-process.md) | Git workflow and PR guidelines | All contributors |

### Specialized Development

- [Volcano Integration](volcano-integration-roadmap.md) - Kubernetes batch job scheduling
- [Agent Development](agent-development.md) - Creating custom agents
- [Frontend Development](frontend-development.md) - React/TypeScript UI development
- [Infrastructure Development](infrastructure-development.md) - Terraform and Kubernetes

---

## 🚀 Quick Start for Developers

### 1. Environment Setup

**Prerequisites:**
```bash
# Required tools
python --version  # 3.11+
node --version    # 18+
docker --version  # 20+
kubectl version   # 1.24+
helm version      # 3+
```

**Repository Setup:**
```bash
# Clone repository
git clone https://github.com/somatechlat/SomaAgentHub.git
cd SomaAgentHub

# Set up Python environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 2. Local Development

**Start Infrastructure:**
```bash
# Start local Kubernetes cluster
make start-cluster

# Start core services
make dev-up

# Verify services
make k8s-smoke
```

**Development Workflow:**
```bash
# Start service in development mode
cd services/gateway-api
uvicorn app.main:app --reload --host 0.0.0.0 --port 10000

# Run tests
pytest tests/

# Check code quality
ruff check .
mypy .
```

### 3. Testing & Validation

**Run Test Suite:**
```bash
# Unit tests
make test-unit

# Integration tests
make test-integration

# End-to-end tests
make test-e2e

# All tests
make test-all
```

**Code Quality Checks:**
```bash
# Linting and formatting
make lint

# Type checking
make type-check

# Security scanning
make security-scan

# All quality checks
make quality-check
```

---

## 🏗️ Project Structure

### Repository Organization

```
SomaAgentHub/
├── services/                 # Microservices (Python FastAPI)
│   ├── gateway-api/         # Public API gateway
│   ├── orchestrator/        # Workflow orchestration
│   ├── identity-service/    # Authentication & authorization
│   ├── policy-engine/       # Governance & compliance
│   ├── memory-gateway/      # Vector storage & context
│   └── common/              # Shared libraries
├── apps/                    # Frontend applications
│   ├── admin-console/       # React admin interface
│   └── mobile-app/          # React Native mobile app
├── sdk/                     # Client SDKs
│   └── python/              # Python SDK
├── infra/                   # Infrastructure as Code
│   ├── terraform/           # Cloud infrastructure
│   ├── k8s/                 # Kubernetes manifests
│   └── helm/                # Helm charts
├── scripts/                 # Automation scripts
├── tests/                   # Test suites
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── e2e/                 # End-to-end tests
└── docs/                    # Documentation
```

### Service Architecture

**Microservices Pattern:**
- **Independent deployments** - Each service can be deployed separately
- **Technology diversity** - Services can use different tech stacks
- **Fault isolation** - Service failures don't cascade
- **Team ownership** - Clear service boundaries and responsibilities

**Communication Patterns:**
- **Synchronous** - HTTP/REST for request-response
- **Asynchronous** - Redis pub/sub for events
- **Workflow** - Temporal for durable processes
- **Streaming** - Kafka for high-volume data

---

## 🛠️ Development Tools

### Code Quality Tools

**Linting & Formatting:**
```bash
# Ruff - Fast Python linter and formatter
ruff check .                 # Check for issues
ruff format .                # Format code
ruff check --fix .           # Auto-fix issues

# Configuration in pyproject.toml
[tool.ruff]
line-length = 120
target-version = "py311"
```

**Type Checking:**
```bash
# MyPy - Static type checking
mypy services/              # Check all services
mypy services/gateway-api/  # Check specific service

# Configuration in pyproject.toml
[tool.mypy]
python_version = "3.11"
strict = true
```

**Testing:**
```bash
# Pytest - Testing framework
pytest                      # Run all tests
pytest tests/unit/          # Run unit tests
pytest -v --cov=app        # Run with coverage

# Configuration in pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

### Development Automation

**Make Targets:**
```bash
# Development
make dev-up                 # Start local infrastructure
make dev-start-services     # Start core services
make dev-down               # Stop local infrastructure

# Testing
make test-unit              # Unit tests
make test-integration       # Integration tests
make test-e2e               # End-to-end tests

# Quality
make lint                   # Code linting
make format                 # Code formatting
make type-check             # Type checking

# Build & Deploy
make build-changed          # Build modified services
make deploy-dev             # Deploy to development
make k8s-smoke              # Smoke tests
```

**Pre-commit Hooks:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

---

## 🔧 Development Workflows

### Feature Development

**1. Create Feature Branch:**
```bash
# Create and switch to feature branch
git checkout -b feature/agent-performance-optimization

# Make changes
# ... edit files ...

# Commit changes
git add .
git commit -m "feat: optimize agent execution performance

- Implement connection pooling for external APIs
- Add caching layer for frequently accessed data
- Reduce memory allocation in hot paths
- Add performance metrics and monitoring"
```

**2. Testing & Quality:**
```bash
# Run tests locally
make test-all

# Check code quality
make quality-check

# Fix any issues
ruff check --fix .
mypy services/
```

**3. Create Pull Request:**
```bash
# Push feature branch
git push origin feature/agent-performance-optimization

# Create PR via GitHub CLI or web interface
gh pr create --title "feat: optimize agent execution performance" \
             --body "Improves agent performance by 40% through connection pooling and caching"
```

### Bug Fix Workflow

**1. Reproduce Issue:**
```bash
# Create bug fix branch
git checkout -b bugfix/workflow-timeout-handling

# Write failing test
# tests/test_workflow_timeout.py

# Verify test fails
pytest tests/test_workflow_timeout.py -v
```

**2. Implement Fix:**
```bash
# Fix the issue
# services/orchestrator/app/workflows/session.py

# Verify test passes
pytest tests/test_workflow_timeout.py -v

# Run full test suite
make test-all
```

**3. Submit Fix:**
```bash
# Commit fix
git add .
git commit -m "fix: handle workflow timeouts gracefully

- Add proper timeout handling in session workflows
- Implement exponential backoff for retries
- Add comprehensive error logging
- Update timeout configuration documentation

Fixes #123"

# Push and create PR
git push origin bugfix/workflow-timeout-handling
gh pr create --title "fix: handle workflow timeouts gracefully"
```

---

## 📊 Development Metrics

### Code Quality Metrics

**Coverage Targets:**
- **Unit Tests**: > 80% line coverage
- **Integration Tests**: > 70% feature coverage
- **E2E Tests**: > 90% critical path coverage

**Performance Targets:**
- **Build Time**: < 5 minutes for full build
- **Test Execution**: < 10 minutes for full test suite
- **Local Startup**: < 2 minutes for development environment

**Quality Gates:**
- **Linting**: Zero violations (enforced by CI)
- **Type Checking**: Zero errors (enforced by CI)
- **Security Scanning**: Zero high/critical vulnerabilities
- **Documentation**: All public APIs documented

### Development Velocity

**Sprint Metrics:**
- **Story Points Completed**: Track team velocity
- **Cycle Time**: Time from commit to production
- **Lead Time**: Time from idea to production
- **Deployment Frequency**: Daily deployments target

**Quality Metrics:**
- **Bug Escape Rate**: < 5% of stories have post-release bugs
- **Technical Debt**: < 20% of sprint capacity
- **Code Review Time**: < 24 hours average
- **PR Size**: < 400 lines changed average

---

## 🔍 Debugging & Troubleshooting

### Local Development Issues

**Service Won't Start:**
```bash
# Check dependencies
make dev-up
kubectl get pods -n soma-agent-hub

# Check service logs
docker logs somaagenthub_gateway-api
kubectl logs -n soma-agent-hub deployment/gateway-api

# Check configuration
cat .env
# Validate with actual tools
make validate-config
```

**Tests Failing:**
```bash
# Run specific test with verbose output
pytest tests/test_specific.py -v -s

# Run with debugger
pytest tests/test_specific.py --pdb

# Check test dependencies
make test-deps-check
```

**Performance Issues:**
```bash
# Profile Python code
python -m cProfile -o profile.stats app/main.py
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"

# Memory profiling
pip install memory-profiler
python -m memory_profiler app/main.py
```

### Integration Debugging

**Service Communication:**
```bash
# Test service connectivity
curl -f http://localhost:10000/healthz
curl -f http://localhost:10001/ready

# Check network policies
kubectl get networkpolicies -n soma-agent-hub

# Trace requests
kubectl logs -f deployment/gateway-api -n soma-agent-hub
```

**Database Issues:**
```bash
# Check database connectivity
kubectl exec -it deployment/app-postgres -n soma-agent-hub -- psql -U somaagent -d somaagent

# Check Redis connectivity
kubectl exec -it deployment/redis -n soma-agent-hub -- redis-cli ping

# Check Temporal connectivity
kubectl exec -it deployment/temporal-server -n soma-agent-hub -- tctl cluster health
```

---

## 📚 Learning Resources

### Getting Started

**Essential Reading:**
1. **[Local Setup](local-setup.md)** - Set up your development environment
2. **[Coding Standards](coding-standards.md)** - Learn our coding conventions
3. **[Testing Guidelines](testing-guidelines.md)** - Understand our testing approach
4. **[Contribution Process](contribution-process.md)** - Learn our Git workflow

**Video Tutorials:**
- **"SomaAgentHub Development Environment Setup"** (15 minutes)
- **"Creating Your First Service"** (30 minutes)
- **"Testing Strategies and Best Practices"** (25 minutes)
- **"Debugging Distributed Systems"** (20 minutes)

### Advanced Topics

**Architecture Deep Dives:**
- **Microservices Communication Patterns**
- **Temporal Workflow Development**
- **Kubernetes Operator Development**
- **Performance Optimization Techniques**

**Specialized Development:**
- **Agent Development SDK**
- **Custom Integration Development**
- **Frontend Component Library**
- **Infrastructure as Code Patterns**

### Community Resources

**Internal Resources:**
- **Engineering Wiki** - Internal documentation and processes
- **Tech Talks** - Weekly presentations on technical topics
- **Code Review Guidelines** - Best practices for code reviews
- **Architecture Decision Records (ADRs)** - Design decisions and rationale

**External Resources:**
- **FastAPI Documentation** - Web framework documentation
- **Temporal Documentation** - Workflow engine documentation
- **Kubernetes Documentation** - Container orchestration
- **React Documentation** - Frontend framework

---

## 🤝 Contributing

### Contribution Guidelines

**Code Contributions:**
1. **Fork the repository** and create a feature branch
2. **Follow coding standards** and write tests
3. **Submit a pull request** with clear description
4. **Respond to code review** feedback promptly
5. **Ensure CI passes** before requesting final review

**Documentation Contributions:**
1. **Identify documentation gaps** or outdated content
2. **Follow the style guide** for consistency
3. **Include examples** and practical guidance
4. **Test documentation** with real scenarios
5. **Submit PR** with documentation updates

**Bug Reports:**
1. **Search existing issues** to avoid duplicates
2. **Provide detailed reproduction steps**
3. **Include environment information**
4. **Attach relevant logs** and error messages
5. **Follow up** on requests for additional information

### Recognition & Rewards

**Contributor Recognition:**
- **Monthly contributor highlights** in team meetings
- **Contribution leaderboard** on internal wiki
- **Conference speaking opportunities** for major contributions
- **Mentorship opportunities** for experienced contributors

**Career Development:**
- **Technical leadership** opportunities on major features
- **Cross-team collaboration** on platform initiatives
- **Open source maintainer** roles for external projects
- **Technical writing** and documentation leadership

---

## 🔄 What's Next?

### Immediate Actions

1. **Set up your development environment** with [Local Setup](local-setup.md)
2. **Review [Coding Standards](coding-standards.md)** to understand our conventions
3. **Read [Testing Guidelines](testing-guidelines.md)** for our testing approach
4. **Follow [Contribution Process](contribution-process.md)** for your first PR

### Advanced Development

- **[API Reference](api-reference.md)** - Detailed API documentation
- **[Agent Development](agent-development.md)** - Create custom agents
- **[Frontend Development](frontend-development.md)** - UI and dashboard development
- **[Infrastructure Development](infrastructure-development.md)** - Platform and tooling

### Continuous Learning

- **Attend tech talks** and engineering meetings
- **Participate in code reviews** to learn from others
- **Contribute to open source** projects and community
- **Share knowledge** through documentation and presentations

---

**Ready to start developing? Begin with [Local Setup](local-setup.md) to configure your development environment, then explore our [Coding Standards](coding-standards.md) to understand our development practices.**
