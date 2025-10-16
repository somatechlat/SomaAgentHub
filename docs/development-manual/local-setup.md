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

## 🚀 Local Development Workflows

You now have two perfect, parallel workflows for local development. Choose the one that best fits your needs.

### **Workflow 1: Kubernetes-Based Development (Recommended)**
This workflow provides the closest experience to the production environment.

**To start or verify your environment:**
```bash
make dev-env
```

**To stop the environment:**
```bash
make stop-cluster
```

### **Workflow 2: Pure Docker-Based Development**
This workflow is slightly faster and uses less memory, as it does not run Kubernetes.

**To start the full application cluster:**
```bash
make docker-cluster-up
```

**To stop the cluster and remove volumes:**
```bash
make docker-cluster-down
```

---

## ✅ You are now ready to code!

Your local development environment is fully configured, persistent, and intelligent.

### Daily Workflow Commands
```bash
# The only command you need to start or check your environment
make dev-env

# Stop the cluster
make stop-cluster

# Run all tests and linters
make lint
make test
```

---

## 💾 **New: Persistent Data Storage**

**The local development cluster is now configured for persistent storage.**

-   **What this means**: Any data stored in the databases (PostgreSQL, Qdrant, etc.) will **survive** if you delete and recreate the cluster using `kind delete cluster` and `make start-cluster`.
-   **How it works**: The cluster is configured to store all its data in the `.persistent_volumes/` directory in your project root. This directory is safely on your local machine.
-   **To perform a full data reset**: If you need to start with a completely clean slate, you can manually delete the `.persistent_volumes/` directory before recreating the cluster:
    ```bash
    rm -rf .persistent_volumes/
    make start-cluster
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
