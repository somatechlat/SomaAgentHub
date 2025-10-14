# SomaAgentHub API Reference

This document provides a comprehensive reference for the SomaAgentHub API. It includes detailed information on all endpoints, request and response schemas, and practical examples.

**Version:** 1.0.0
**Last Updated:** October 14, 2025

## 1. Authentication

All API endpoints are protected and require a valid JWT Bearer token in the `Authorization` header. Tokens can be obtained from the **Identity Service**.

### 1.1. Obtain Access Token

*   **Endpoint:** `POST /v1/auth/login` (on Identity Service, Port 8002)
*   **Purpose:** Authenticate with a username and password to receive an access token.

**Request Body:**

```json
{
  "username": "string",
  "password": "string"
}
```

**Example:**

```python
import httpx

async def get_access_token(username, password):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8002/v1/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        return response.json()["access_token"]

# access_token = await get_access_token("admin", "admin123")
```

## 2. Gateway API (Port 8000)

The Gateway API is the main entry point for all external clients.

### 2.1. Chat Completions

*   **Endpoint:** `POST /v1/chat/completions`
*   **Purpose:** An OpenAI-compatible endpoint for generating text completions.

### 2.2. List Models

*   **Endpoint:** `GET /v1/models`
*   **Purpose:** Retrieve a list of available language models.

### 2.3. Start Session

*   **Endpoint:** `POST /v1/sessions/start`
*   **Purpose:** Initiate a new conversational session.

## 3. Orchestrator Service (Port 8001)

The Orchestrator Service manages Temporal-backed workflows.

### 3.1. Start Session Workflow

*   **Endpoint:** `POST /v1/sessions/start`
*   **Purpose:** Start a new single-agent session workflow.

**Request Body:**

```json
{
  "tenant": "string",
  "user": "string",
  "prompt": "string",
  "model": "string",
  "metadata": {}
}
```

### 3.2. Check Session Status

*   **Endpoint:** `GET /v1/sessions/{workflow_id}`
*   **Purpose:** Check the status of a running session workflow.

### 3.3. Start Multi-Agent Orchestration

*   **Endpoint:** `POST /v1/mao/start`
*   **Purpose:** Launch a new multi-agent orchestration workflow.

**Request Body:**

```json
{
  "tenant": "string",
  "initiator": "string",
  "directives": [
    {
      "agent_id": "string",
      "goal": "string",
      "prompt": "string"
    }
  ]
}
```

### 3.4. Check Multi-Agent Status

*   **Endpoint:** `GET /v1/mao/{workflow_id}`
*   **Purpose:** Check the status of a running multi-agent orchestration.

## 4. SLM Service (Port 8003)

The SLM Service provides local language model inference.

### 4.1. Text Generation

*   **Endpoint:** `POST /v1/infer/sync`
*   **Purpose:** Generate text completions synchronously.

**Request Body:**

```json
{
  "prompt": "string",
  "max_tokens": "integer",
  "temperature": "float"
}
```

### 4.2. Embeddings Generation

*   **Endpoint:** `POST /v1/embeddings`
*   **Purpose:** Generate vector embeddings for a list of texts.

**Request Body:**

```json
{
  "input": ["string"],
  "model": "string"
}
```

## 5. Memory Gateway (Port 8004)

The Memory Gateway manages agent memory.

### 5.1. Store Memory (Remember)

*   **Endpoint:** `POST /v1/remember`
*   **Purpose:** Store a key-value pair in the vector memory.

**Request Body:**

```json
{
  "key": "string",
  "value": "any",
  "metadata": {}
}
```

### 5.2. Retrieve Memory (Recall)

*   **Endpoint:** `GET /v1/recall/{key}`
*   **Purpose:** Retrieve a memory by its exact key.

### 5.3. RAG Retrieval

*   **Endpoint:** `POST /v1/rag/retrieve`
*   **Purpose:** Perform a semantic search over the memory.

**Request Body:**

```json
{
  "query": "string",
  "top_k": "integer",
  "filter": {}
}
```
