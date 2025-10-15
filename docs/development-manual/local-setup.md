# Local Development Environment Setup

**A one-page guide to setting up a complete local development environment for SomaAgentHub.**

This guide provides step-by-step instructions to get you from a clean machine to a fully functional local development setup, ready for coding and testing.

---

## 🎯 Prerequisites

Ensure you have the following tools installed on your system before you begin.

| Tool | Minimum Version | Installation Command / Link |
|---|---|---|
| **Git** | 2.30+ | `brew install git` or [Official Website](https://git-scm.com/downloads) |
| **Docker** | 20.10+ | [Docker Desktop](https://www.docker.com/products/docker-desktop/) |
| **Python** | 3.11 | `brew install python@3.11` or [Official Website](https://www.python.org/) |
| **make** | 3.81+ | Included with Xcode Command Line Tools on macOS. |
| **kubectl** | 1.24+ | `brew install kubectl` or [Official Docs](https://kubernetes.io/docs/tasks/tools/) |
| **Helm** | 3.8+ | `brew install helm` or [Official Website](https://helm.sh/) |
| **Kind** | 0.17+ | `brew install kind` or [Official Website](https://kind.sigs.k8s.io/) |

---

## 🚀 Setup in 5 Steps

Follow these five steps to get everything running.

### Step 1: Clone the Repository
```bash
git clone https://github.com/somatechlat/somaAgentHub.git
cd somaAgentHub
```

### Step 2: Set Up Python Environment
We use `venv` for managing Python dependencies.

```bash
# Create a virtual environment
python3.11 -m venv .venv

# Activate the environment
source .venv/bin/activate

# On Windows, use:
# .venv\Scripts\activate

# Install all required dependencies
pip install -r requirements-dev.txt
```

### Step 3: Start Local Infrastructure
This command uses Docker Compose to start all the necessary backing services (PostgreSQL, Redis, Temporal, etc.).

```bash
make dev-up
```
- **What it does**: Starts all infrastructure containers in the background.
- **Verify**: Run `docker compose ps` to see all containers in the `running` state.

### Step 4: Run the Services Locally
This command starts the core SomaAgentHub microservices locally for development.

```bash
make dev-start-services
```
- **What it does**: Starts the Gateway API, Orchestrator, and other key services. They will automatically reload on code changes.
- **Access**:
    - Gateway API: `http://localhost:8080`
    - API Docs: `http://localhost:8080/docs`
    - Temporal UI: `http://localhost:8233`

### Step 5: Run the Test Suite
Verify that your local setup is working correctly by running the full test suite.

```bash
make test
```
- **What it does**: Runs unit tests, integration tests, and code quality checks.
- **Expected Output**: All tests should pass.

---

## ✅ You are now ready to code!

Your local development environment is fully configured.

### Daily Workflow Commands
```bash
# Start everything
make dev-up
make dev-start-services

# Stop everything
make dev-down

# Run all tests and linters
make lint
make test

# Clean your environment (removes Docker volumes)
make dev-clean
```

---

## 🔧 IDE Configuration (VS Code)

For the best development experience, we recommend VS Code with the following extensions:

- **Python** (ms-python.python)
- **Ruff** (charliermarsh.ruff)
- **Docker** (ms-azuretools.vscode-docker)
- **Kubernetes** (ms-kubernetes-tools.vscode-kubernetes-tools)

**`settings.json` Configuration:**
```json
{
    "python.pythonPath": "${workspaceFolder}/.venv/bin/python",
    "python.testing.pytestArgs": [
        "tests"
    ],
    "python.testing.unittestEnabled": false,
    "python.testing.pytestEnabled": true,
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll": true,
            "source.organizeImports": true
        }
    }
}
```

---

## ❓ Troubleshooting

- **`make` command not found**: Install Xcode Command Line Tools on macOS or `build-essential` on Linux.
- **Port conflicts**: If a service fails to start, check if the required port is already in use with `lsof -i :<port>`.
- **Docker issues**: Ensure Docker Desktop is running and has sufficient memory allocated (at least 8GB).

---
## 🔗 Related Documentation
- **[Contribution Process](contribution-process.md)**: For how to submit your first change.
- **[Testing Guidelines](testing-guidelines.md)**: For details on the testing strategy.
```
