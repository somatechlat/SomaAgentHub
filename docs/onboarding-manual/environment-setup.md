# Onboarding Environment Setup

**A focused guide to getting the SomaAgentHub development environment running for the first time.**

This guide provides the essential steps for new team members to get a working local development environment up and running quickly. For a more detailed guide, see the [full Local Setup document](../development-manual/local-setup.md).

---

## 🎯 Goal

By the end of this guide, you will have:
- All required software installed.
- The SomaAgentHub codebase on your machine.
- All backing services (databases, etc.) running.
- The core application services running locally.
- A successful test run to verify your setup.

---

## 🚀 Step 1: Install Prerequisites

First, ensure you have the necessary tools. If you have these installed, you can skip to Step 2.

- **Git**: For version control.
- **Docker Desktop**: To run our containerized infrastructure.
- **Python 3.11**: The primary language for our backend services.
- **make**: To run our convenient setup commands.

*For detailed installation instructions, refer to the [Prerequisites Table](../development-manual/local-setup.md#prerequisites).*

---

## 📦 Step 2: Get the Code
Clone the repository to your local machine.

```bash
git clone https://github.com/somatechlat/somaAgentHub.git
cd somaAgentHub
```

---

## 🐍 Step 3: Set Up the Python Environment
This step creates an isolated Python environment for the project.

```bash
# Create the virtual environment
python3.11 -m venv .venv

# Activate it
source .venv/bin/activate

# Install all dependencies
pip install -r requirements-dev.txt
```

---

## 🐳 Step 4: Start the Infrastructure
This command uses Docker to start all the services SomaAgentHub depends on, like PostgreSQL and Redis.

```bash
make dev-up
```
- **Wait**: This may take a few minutes the first time as Docker downloads the necessary images.
- **Verify**: Once it's done, run `docker compose ps`. You should see several containers in the `running` state.

---

## ⚙️ Step 5: Run the Application
Now, start the core SomaAgentHub microservices.

```bash
make dev-start-services
```
- **What's happening?**: This command starts several services in your terminal. You will see a lot of log output. This is normal.
- **Keep it running**: Leave this terminal window open while you are developing.

---

## ✅ Step 6: Verify Your Setup
Open a **new terminal window** (leave the services from Step 5 running) and follow these steps:

1.  **Activate the Python environment** in the new terminal:
    ```bash
    cd /path/to/somaAgentHub  # Navigate back to the project directory
    source .venv/bin/activate
    ```

2.  **Run the smoke tests**:
    ```bash
    make k8s-smoke HOST="localhost:10000"
    ```
    This runs a quick set of tests to ensure the core APIs are responding correctly.

**If the smoke tests pass, your environment is set up correctly!**

---

## 🎉 Congratulations!

You now have a fully functional local development environment. You are ready to start coding.

### What to do next?
- Proceed to the [**First Contribution Guide**](./first-contribution.md) to learn how to pick up a task and submit your first pull request.
```