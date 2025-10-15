# SomaAgentHub API Reference

**A guide to the SomaAgentHub APIs, authentication, and usage patterns.**

This document provides developers with the information needed to interact with the SomaAgentHub platform programmatically.

---

## 🎯 API Philosophy

- **OpenAPI Specification**: Every service exposes an OpenAPI 3.0 specification (usually at `/docs`). This is the single source of truth for all endpoints.
- **RESTful Principles**: Our APIs adhere to RESTful design principles.
- **OpenAI Compatibility**: The Gateway API provides OpenAI-compatible endpoints for chat completions, allowing you to use existing client libraries.
- **Authentication**: All endpoints are protected and require a JWT token.

---

## 🚀 Accessing the API Documentation

The most up-to-date and interactive API documentation is generated automatically from the code and is available on your local instance.

- **Gateway API**: `http://localhost:8080/docs`
- **Orchestrator API**: `http://localhost:8001/docs`
- **Memory Gateway API**: `http://localhost:8004/docs`
- *(and so on for each service...)*

These interactive docs (provided by Swagger UI) allow you to explore and even try out the API endpoints directly from your browser.

---

## 🔑 Authentication

All requests to the SomaAgentHub API must be authenticated using a **Bearer Token**.

1.  **Obtain a Token**: Tokens are issued by the Identity Service. In a development environment, you can use a pre-configured demo token.
2.  **Include the Token**: Provide the token in the `Authorization` header of your HTTP requests.

```bash
curl -X GET http://localhost:8080/v1/models \
  -H "Authorization: Bearer <your-jwt-token>"
```

---

## 📦 Core APIs

This section provides a high-level overview of the most important APIs. For detailed endpoint specifications, refer to the interactive Swagger docs.

### 1. Gateway API (`:8080`)
This is the primary public-facing API.

- **`POST /v1/chat/completions`**: (OpenAI-compatible) Create a chat completion. Can be used for stateless requests or session-based conversations.
- **`GET /v1/models`**: (OpenAI-compatible) List the available language models.
- **`POST /v1/sessions`**: Create a new persistent conversation session.
- **`GET /health`**: Health check endpoint.

### 2. Orchestrator API (`:8001`)
Used for managing and executing complex workflows.

- **`POST /v1/workflows/start`**: Start a new workflow.
- **`GET /v1/workflows/{run_id}`**: Get the status of a running workflow.
- **`POST /v1/workflows/{run_id}/cancel`**: Cancel a workflow.
- **`GET /v1/workflows`**: List all workflows.

### 3. Memory Gateway API (`:8004`)
Used for interacting with the agent memory system.

- **`POST /v1/memories`**: Store a new piece of information in memory.
- **`POST /v1/recall`**: Perform a semantic search to retrieve relevant memories.
- **`GET /v1/memories/analytics`**: Get usage statistics for the memory system.

---

## 💡 Example Usage (Python)

This example demonstrates a common workflow using the Python `requests` library.

```python
import requests
import time

BASE_URL = "http://localhost:8080"
ORCHESTRATOR_URL = "http://localhost:8001"
TOKEN = "your-demo-token" # Replace with a valid token

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def start_research_workflow(topic: str) -> str:
    """Starts a research workflow and returns the run ID."""
    payload = {
        "workflow_type": "research_project",
        "input": {"topic": topic}
    }
    response = requests.post(
        f"{ORCHESTRATOR_URL}/v1/workflows/start",
        headers=HEADERS,
        json=payload
    )
    response.raise_for_status()
    return response.json()["run_id"]

def check_workflow_status(run_id: str) -> dict:
    """Checks the status of a workflow."""
    response = requests.get(
        f"{ORCHESTRATOR_URL}/v1/workflows/{run_id}",
        headers=HEADERS
    )
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    run_id = start_research_workflow("The future of AI in healthcare")
    print(f"Workflow started with run ID: {run_id}")

    while True:
        status = check_workflow_status(run_id)
        print(f"Current status: {status['status']}")
        if status['status'] in ['completed', 'failed']:
            break
        time.sleep(10)

    print("Workflow finished.")
```

---
## 🔗 Related Documentation
- **[Testing Guidelines](testing-guidelines.md)**: For how to write tests for the API.
- **[Contribution Process](contribution-process.md)**: For how to add or modify API endpoints.
```
