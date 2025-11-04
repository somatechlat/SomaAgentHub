# Contributing to SomaAgentHub

We welcome contributions! This guide outlines the process for setting up a development environment, making changes, and submitting pull requests.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Fork & Clone](#fork--clone)
3. [Development Environment](#development-environment)
4. [Building & Running Locally](#building--running-locally)
5. [Adding a New Service](#adding-a-new-service)
6. [Testing](#testing)
7. [Documentation Updates](#documentation-updates)
8. [Submitting a Pull Request](#submitting-a-pull-request)
9. [Code Style & Linting](#code-style--linting)
10. [License](#license)

---

### Prerequisites
- **Docker** (Desktop or Engine) with at least 8 GB RAM.
- **Python 3.11+** (for tooling and services).
- **Kind** (or a Kubernetes cluster) and **kubectl**.
- **Helm 3**.
- **Make** (standard on macOS/Linux).
- Optional but recommended: **VS Code** with the Remote Containers extension.

### Fork & Clone
```bash
# Fork the repository on GitHub first.
git clone git@github.com:YOUR_USERNAME/SomaAgentHub.git
cd SomaAgentHub
```

### Development Environment
```bash
# Create a virtual environment for Python tooling
python -m venv .venv
source .venv/bin/activate
# Install development dependencies
pip install -r requirements-dev.txt
```

### Building & Running Locally
The quickest way to spin up the whole stack is:
```bash
make start-cluster   # Deletes any existing Kind cluster, rebuilds images, and runs Helm install.
```
For iterative development you can use the split workflow:
```bash
# Start supporting services (Temporal, Redis, etc.)
make dev-up
# Build only changed images (fast)
make build-changed
# Run core services locally (no K8s)
make dev-start-services
# Port‑forward the gateway for API access
make port-forward-gateway LOCAL=8080 REMOTE=10000
```

### Adding a New Service
1. Create a directory under `services/` (e.g., `services/my-service`).
2. Add a `Dockerfile` that follows the existing pattern – copy from `services/gateway-api/Dockerfile`.
3. Add a `requirements.txt` and `app/` package.
4. Ensure the service name matches the folder name; the `build‑changed.sh` script will automatically discover it.
5. Add a Helm entry under `k8s/helm/soma-agent/values.yaml` (see **Adding a Service Guide**).

### Testing
- **Unit / Integration**: `pytest -q tests/`
- **K8s Smoke**: `make k8s-smoke`
- **End‑to‑End**: `make test-e2e`
All CI jobs run these steps automatically.

### Documentation Updates
When you modify code that impacts configuration, architecture, or usage, update the relevant docs in `docs/` and the top‑level `README.md`. Keep the documentation in sync with the code to avoid drift.

### Submitting a Pull Request
1. Create a feature branch: `git checkout -b feat/my‑feature`
2. Commit your changes with clear messages.
3. Push to your fork and open a PR against `main`.
4. Ensure the CI pipeline passes.
5. Add reviewers and a concise description of what the PR accomplishes.

### Code Style & Linting
- Run `ruff check .` for Python linting.
- Use `prettier` for any JSON/YAML/Markdown if you have it installed.
- Keep line length ≤ 120 characters.

### License
SomaAgentHub is licensed under the Apache 2.0 License – see `LICENSE` for details.

---

Thank you for contributing! 🎉