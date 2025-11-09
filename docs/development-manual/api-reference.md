# SomaAgentHub API Reference

**A guide to the SomaAgentHub APIs, authentication, and usage patterns.**

This document provides developers with the information needed to interact with the SomaAgentHub platform programmatically.

---

## 🎯 API Philosophy

- **OpenAPI Specification**: Every service exposes an OpenAPI 3.0 specification (usually at `/docs`). Treat the running service as the source of truth.
- **RESTful Principles**: APIs adhere to standard RESTful design.
- **Session-Oriented**: The Gateway and Orchestrator expose session-focused endpoints that coordinate long‑running workflows.
- **Authentication**: Most endpoints are protected and require a JWT token.

---

## 🚀 Accessing the API Documentation

Interactive API docs are generated from the code at runtime:

- **Gateway API**: `http://localhost:10000/docs`
- **Orchestrator API**: `http://localhost:10001/docs`
- **Memory Gateway API (optional)**: default container port `8000` → `http://<memory-gateway-host>:8000/docs`
- *(and so on for each service...)*

These interactive docs (provided by Swagger UI) allow you to explore and even try out the API endpoints directly from your browser.

---

## 🔑 Authentication

All requests to the SomaAgentHub API must be authenticated using a **Bearer Token**.

1.  **Obtain a Token**: Tokens are issued by the Identity Service. In a development environment, you can use a pre-configured demo token.
2.  **Include the Token**: Provide the token in the `Authorization` header of your HTTP requests.

```bash
curl -X GET http://localhost:10000/v1/status \
  -H "Authorization: Bearer <your-jwt-token>"
```

---

## 📦 Core APIs

This section highlights the primary, code-backed endpoints. See each service’s `/docs` for full details.

### 1. Gateway API (`:10000`)
Public entrypoint and session creation.

- **`POST /v1/sessions`**: Create a new session; forwards to the orchestrator.
- **`GET /v1/status`**: Basic gateway status and request context.
- **`GET /healthz`**: Health check endpoint.

### 2. Orchestrator API (`:10001`)
Temporal-backed workflow coordination.

- **`POST /v1/sessions/start`**: Start a Temporal session workflow.
- **`GET /v1/sessions/{workflow_id}`**: Get the status (and result if completed).

### 3. Memory Gateway API (optional, default container port `8000`)
Vector/KV memory access when enabled.

- **`POST /v1/remember`**: Store a value by key (embeds via LLM Hub and indexes when Qdrant is available).
- **`GET /v1/recall/{key}`**: Retrieve a value by key.
- **`POST /v1/rag/retrieve`**: Semantic retrieval using embeddings when configured.

---

## 💡 Example Usage (Python)

This example demonstrates a common workflow using the Python `requests` library.

```python
import requests
import time

ORCHESTRATOR_URL = "http://localhost:10001"
TOKEN = "your-demo-token"  # Replace with a valid token

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

def start_session(prompt: str) -> str:
    """Starts a session workflow and returns the workflow_id."""
    payload = {
        "tenant": "demo-tenant",
        "user": "demo-user",
        "prompt": prompt,
        "metadata": {},
    }
    resp = requests.post(
        f"{ORCHESTRATOR_URL}/v1/sessions/start",
        headers=HEADERS,
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["workflow_id"]

def check_session(workflow_id: str) -> dict:
    resp = requests.get(
        f"{ORCHESTRATOR_URL}/v1/sessions/{workflow_id}",
        headers=HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()

if __name__ == "__main__":
    wid = start_session("Research the impact of AI in healthcare")
    print(f"Started session with workflow_id: {wid}")
    while True:
        status = check_session(wid)
        print(f"Current status: {status['status']}")
        if status["status"] in {"completed", "failed"}:
            break
        time.sleep(5)
    print("Done.")
```

---
## 🔗 Related Documentation
- **[Testing Guidelines](testing-guidelines.md)**: For how to write tests for the API.
- **[Contribution Process](contribution-process.md)**: For how to add or modify API endpoints.
```
