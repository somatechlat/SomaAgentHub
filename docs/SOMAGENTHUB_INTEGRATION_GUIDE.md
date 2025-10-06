# SomaAgentHub Integration Guide

**Version:** 1.0.0  
**Last Updated:** October 5, 2025  
**Platform Status:** Production Ready 🚀

---

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [Quick Start](#quick-start)
4. [Authentication & Identity](#authentication--identity)
5. [Core Platform Services](#core-platform-services)
6. [Building Your First Agent](#building-your-first-agent)
7. [Advanced Integrations](#advanced-integrations)
8. [Tool Adapters](#tool-adapters)
9. [Memory & RAG](#memory--rag)
10. [Workflows & Orchestration](#workflows--orchestration)
11. [Observability & Monitoring](#observability--monitoring)
12. [Production Deployment](#production-deployment)
13. [SDK Reference](#sdk-reference)
14. [Troubleshooting](#troubleshooting)

---

## 🎯 Introduction

Welcome to **SomaAgentHub** - your comprehensive platform for building, deploying, and managing AI agents at scale. This guide will walk you through integrating your first agent and leveraging all 14 microservices, 12 infrastructure components, and 16 tool adapters.

### What You'll Learn

- How to authenticate and establish agent identity
- How to use each platform service (Gateway, Orchestrator, Memory, Tools, etc.)
- How to build intelligent agents with memory, tools, and workflows
- How to monitor, scale, and deploy production-ready agents
- Best practices for multi-agent collaboration

### Prerequisites

```bash
# Required
- Python 3.11+
- Docker & Docker Compose (for local development)
- Kubernetes cluster (for production)

# Optional
- Node.js 18+ (for React Native mobile app)
- Helm 3.x (for K8s deployment)
```

---

## 🏗️ Architecture Overview

### Platform Services Map

```
┌─────────────────────────────────────────────────────────────────┐
│                        SOMAGENTHUB PLATFORM                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │  Gateway API │─────▶│ Orchestrator │─────▶│ Identity Svc │  │
│  │  (Port 8000) │      │  (Port 8001) │      │  (Port 8002) │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
│         │                      │                      │          │
│         │                      │                      │          │
│         ▼                      ▼                      ▼          │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │  SLM Service │      │Memory Gateway│      │ Tool Service │  │
│  │  (Port 8003) │      │  (Port 8004) │      │  (Port 8005) │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
│         │                      │                      │          │
│         └──────────────────────┴──────────────────────┘          │
│                                │                                 │
│                                ▼                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │           INFRASTRUCTURE LAYER (12 Components)             │ │
│  │  PostgreSQL • Redis • Kafka • Keycloak • OPA • Qdrant     │ │
│  │  ClickHouse • Temporal • Ray • MinIO • Prometheus • Grafana│ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Service Responsibilities

| Service | Port | Purpose | Key Features |
|---------|------|---------|-------------|
| **Gateway API** | 8000 | Public entry point | Authentication, rate limiting, routing |
| **Orchestrator** | 8001 | Workflow coordination | Temporal workflows, multi-agent coordination |
| **Identity Service** | 8002 | Auth & identity | JWT tokens, user management, audit logging |
| **SLM Service** | 8003 | Local language models | Text generation, embeddings, no external API costs |
| **Memory Gateway** | 8004 | Vector memory & RAG | Qdrant integration, semantic search, memory management |
| **Tool Service** | 8005 | External integrations | 16 adapters (GitHub, Slack, AWS, etc.) |
| **Task Capsule Repo** | 8006 | Reusable task library | Versioned task definitions, marketplace |
| **Policy Engine** | 8007 | Authorization & governance | OPA policies, compliance enforcement |
| **Analytics Service** | 8008 | Usage analytics | ClickHouse queries, cost tracking |
| **Settings Service** | 8009 | Configuration | User preferences, tenant settings |
| **Billing Service** | 8010 | Usage metering | Token tracking, cost allocation |
| **Constitution Service** | 8011 | Ethical constraints | Value alignment, safety guardrails |
| **Notification Service** | 8012 | Alerts & notifications | Email, Slack, Discord webhooks |
| **Marketplace** | 8013 | Capsule marketplace | Search, download, ratings |

---

## 🚀 Quick Start

### 1. Install the SDK

```bash
# Python SDK
pip install somaagent

# Or install from source
cd sdk/python
pip install -e .
```

### 2. Set Environment Variables

```bash
# .env file
export SOMAAGENT_API_URL="http://localhost:8000"
export SOMAAGENT_API_KEY="your-api-key-here"

# For production
export SOMAAGENT_API_URL="https://api.somaagent.io"
export SOMAAGENT_API_KEY="prod-key-xxxxxxxx"
```

### 3. Your First Agent (5 Minutes)

```python
from somaagent import SomaAgentClient

# Initialize client
client = SomaAgentClient(
    api_key="your-api-key",
    base_url="http://localhost:8000"
)

# Create an agent
agent = client.create_agent(
    name="MyFirstAgent",
    instructions="You are a helpful assistant with access to GitHub and Slack.",
    model="somasuite-markov-v1",
    tools=["github", "slack"]
)

# Run the agent
result = client.run_agent(
    agent_id=agent.id,
    prompt="Create a GitHub issue for bug tracking and notify the team on Slack"
)

print(result)
```

**Output:**
```json
{
  "status": "completed",
  "result": "Created GitHub issue #123 and sent Slack notification to #dev-team",
  "tool_calls": [
    {"tool": "github", "action": "create_issue", "status": "success"},
    {"tool": "slack", "action": "send_message", "status": "success"}
  ]
}
```

---

## 🔐 Authentication & Identity

### Identity Service Integration

The Identity Service (port 8002) manages all authentication, user identities, and JWT tokens.

#### 1. User Registration

```python
import httpx

async def register_user(username: str, email: str, password: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8002/v1/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password
            }
        )
        return response.json()

# Example
user = await register_user("john_doe", "john@example.com", "secure_password")
# Returns: {"user_id": "usr_xxx", "status": "registered"}
```

#### 2. Login & Token Generation

```python
async def login(username: str, password: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8002/v1/auth/login",
            json={
                "username": username,
                "password": password
            }
        )
        data = response.json()
        return data["access_token"], data["refresh_token"]

# Example
access_token, refresh_token = await login("john_doe", "secure_password")
```

#### 3. JWT Token Usage

All subsequent requests to SomaAgentHub services require the JWT token:

```python
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Use in all API calls
response = await client.get(
    "http://localhost:8000/v1/agents",
    headers=headers
)
```

#### 4. Token Refresh

JWT tokens expire after 24 hours (configurable). Use the refresh token:

```python
async def refresh_access_token(refresh_token: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8002/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        return response.json()["access_token"]
```

#### 5. Service Account Authentication

For server-to-server communication (recommended for production agents):

```python
async def create_service_account(name: str, scopes: list[str]):
    """Create a service account with specific permissions."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8002/v1/service-accounts",
            json={
                "name": name,
                "scopes": scopes  # e.g., ["read:agents", "write:workflows"]
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        return response.json()

# Returns API key that doesn't expire
service_account = await create_service_account(
    "production-agent-1",
    ["read:*", "write:workflows", "execute:tools"]
)
api_key = service_account["api_key"]  # Use this for the agent
```

---

## 🎛️ Core Platform Services

### 1. Gateway API (Port 8000)

**Purpose:** Central entry point for all external requests. Handles authentication, rate limiting, and routing to backend services.

**When to Connect:** 
- First point of contact for all client applications (web, mobile, CLI)
- For OpenAI-compatible API requests
- When you need unified access to all platform services
- For session management and conversation tracking

**Why Connect:**
- Single endpoint for simplified client integration
- Built-in rate limiting and authentication
- Request/response logging and audit trails
- Load balancing across backend services
- API versioning and backward compatibility

---

#### 📋 Complete API Reference

##### **1.1 Chat Completions API**

**Endpoint:** `POST /v1/chat/completions`

**Purpose:** Generate text completions using local SLM models (OpenAI-compatible)

**Authentication:** Required (Bearer token)

**Request Schema:**
```json
{
  "model": "string",              // Required: Model ID (e.g., "somasuite-markov-v1")
  "messages": [                   // Required: Conversation history
    {
      "role": "string",           // Required: "user", "assistant", or "system"
      "content": "string",        // Required: Message content
      "name": "string"            // Optional: Participant name
    }
  ],
  "max_tokens": 64,               // Optional: Max completion tokens (1-256, default: 64)
  "temperature": 0.8,             // Optional: Randomness (0.0-2.0, default: 0.8)
  "top_p": 1.0,                   // Optional: Nucleus sampling (0.0-1.0)
  "n": 1,                         // Optional: Number of completions (default: 1)
  "stream": false,                // Optional: Enable streaming (default: false)
  "stop": ["string"],             // Optional: Stop sequences
  "presence_penalty": 0.0,        // Optional: Presence penalty (-2.0 to 2.0)
  "frequency_penalty": 0.0,       // Optional: Frequency penalty (-2.0 to 2.0)
  "user": "string"                // Optional: User identifier for tracking
}
```

**Response Schema:**
```json
{
  "id": "chatcmpl-xxx",           // Completion ID
  "object": "chat.completion",    // Object type
  "created": 1234567890,          // Unix timestamp
  "model": "somasuite-markov-v1", // Model used
  "choices": [
    {
      "index": 0,                 // Choice index
      "message": {
        "role": "assistant",      // Always "assistant"
        "content": "string"       // Generated response
      },
      "finish_reason": "stop"     // "stop", "length", or "content_filter"
    }
  ],
  "usage": {
    "prompt_tokens": 10,          // Input token count
    "completion_tokens": 25,      // Output token count
    "total_tokens": 35            // Total tokens used
  }
}
```

**Example Implementation:**
```python
import httpx
from typing import List, Dict, Optional

class ChatCompletionClient:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "somasuite-markov-v1",
        max_tokens: int = 64,
        temperature: float = 0.8,
        stream: bool = False
    ):
        """Create a chat completion."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": stream
                }
            )
            response.raise_for_status()
            return response.json()

# Usage Example
async def main():
    client = ChatCompletionClient(api_key="your-token")
    
    # Simple conversation
    result = await client.create_completion(
        messages=[
            {"role": "system", "content": "You are a helpful Python expert."},
            {"role": "user", "content": "Write a function to reverse a string."}
        ],
        max_tokens=150
    )
    
    print(result["choices"][0]["message"]["content"])
    print(f"Tokens used: {result['usage']['total_tokens']}")

# Output:
# Here's a function to reverse a string in Python:
# def reverse_string(s):
#     return s[::-1]
# Tokens used: 42
```

**Use Cases:**
1. **Chatbots** - Build conversational AI with context
2. **Code Generation** - Generate code snippets based on requirements
3. **Content Creation** - Write articles, emails, documentation
4. **Question Answering** - Answer questions with context from conversation history
5. **Text Transformation** - Summarize, translate, or rewrite text

**Rate Limits:**
- Free tier: 10 requests/minute
- Pro tier: 100 requests/minute
- Enterprise tier: 1000 requests/minute

**Error Responses:**
```json
// 401 Unauthorized
{
  "error": {
    "message": "Invalid authentication token",
    "type": "authentication_error",
    "code": "invalid_token"
  }
}

// 429 Rate Limit Exceeded
{
  "error": {
    "message": "Rate limit exceeded. Retry after 60 seconds.",
    "type": "rate_limit_error",
    "code": "rate_limit_exceeded"
  }
}

// 400 Bad Request
{
  "error": {
    "message": "Invalid model specified",
    "type": "invalid_request_error",
    "code": "invalid_model"
  }
}
```

---

##### **1.2 Models API**

**Endpoint:** `GET /v1/models`

**Purpose:** List all available models and their capabilities

**Authentication:** Required (Bearer token)

**Request:** No parameters required

**Response Schema:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "somasuite-markov-v1",        // Model identifier
      "object": "model",                   // Object type
      "created": 1234567890,               // Unix timestamp
      "owned_by": "somaagent",             // Owner
      "permission": [...],                 // Model permissions
      "root": "somasuite-markov-v1",       // Base model
      "parent": null,                      // Parent model (if fine-tuned)
      "capabilities": {
        "completion": true,                // Supports text completion
        "chat": true,                      // Supports chat
        "embeddings": true,                // Supports embeddings
        "fine_tuning": false               // Supports fine-tuning
      },
      "context_window": 2048,              // Max context tokens
      "max_tokens": 256                    // Max output tokens
    }
  ]
}
```

**Example:**
```python
async def list_models(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/v1/models",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()

models = await list_models(access_token)
for model in models["data"]:
    print(f"Model: {model['id']}")
    print(f"  Context: {model['context_window']} tokens")
    print(f"  Max output: {model['max_tokens']} tokens")
    print(f"  Capabilities: {', '.join([k for k, v in model['capabilities'].items() if v])}")
```

**Use Cases:**
1. **Model Discovery** - Find available models before making requests
2. **Capability Check** - Verify model supports required features
3. **Dynamic UI** - Populate model selection dropdowns
4. **Validation** - Ensure requested model exists before expensive operations

---

##### **1.3 Sessions API**

**Endpoint:** `POST /v1/sessions`

**Purpose:** Create persistent conversation sessions with state management

**Authentication:** Required (Bearer token)

**When to Use:**
- Multi-turn conversations with context retention
- User-specific agent interactions
- Long-running dialogues requiring state persistence
- When you need session-level analytics

**Request Schema:**
```json
{
  "agent_id": "string",           // Optional: Agent to use for this session
  "user_id": "string",            // Optional: User identifier
  "metadata": {                   // Optional: Custom metadata
    "source": "web",
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "custom_field": "value"
  },
  "settings": {                   // Optional: Session-specific settings
    "temperature": 0.8,
    "max_history": 50,            // Max messages to retain
    "timeout_minutes": 30         // Session timeout
  }
}
```

**Response Schema:**
```json
{
  "session_id": "sess_xxx",       // Unique session identifier
  "agent_id": "agent_xxx",        // Assigned agent
  "user_id": "user_123",          // User identifier
  "status": "active",             // "active", "expired", or "terminated"
  "created_at": "2025-10-05T12:00:00Z",
  "expires_at": "2025-10-05T12:30:00Z",
  "message_count": 0,             // Messages in session
  "metadata": {...}               // Custom metadata
}
```

**Example - Complete Session Workflow:**
```python
class ConversationSession:
    """Manages a conversation session with state."""
    
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.session_id = None
    
    async def start_session(self, user_id: str, agent_id: str = None):
        """Create a new session."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/sessions",
                headers=self.headers,
                json={
                    "agent_id": agent_id,
                    "user_id": user_id,
                    "metadata": {
                        "source": "python_sdk",
                        "version": "1.0.0"
                    },
                    "settings": {
                        "max_history": 50,
                        "timeout_minutes": 60
                    }
                }
            )
            data = response.json()
            self.session_id = data["session_id"]
            return data
    
    async def send_message(self, content: str):
        """Send a message in the session."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/sessions/{self.session_id}/messages",
                headers=self.headers,
                json={"content": content, "role": "user"}
            )
            return response.json()
    
    async def get_history(self, limit: int = 10):
        """Retrieve conversation history."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v1/sessions/{self.session_id}/messages",
                headers=self.headers,
                params={"limit": limit}
            )
            return response.json()
    
    async def end_session(self):
        """Terminate the session."""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/v1/sessions/{self.session_id}",
                headers=self.headers
            )
            return response.json()

# Usage Example
async def customer_support_session():
    session = ConversationSession(api_key="your-token")
    
    # Start session
    info = await session.start_session(user_id="user_123", agent_id="support_agent")
    print(f"Session started: {info['session_id']}")
    
    # User asks questions
    response1 = await session.send_message("What are your pricing tiers?")
    print(f"Agent: {response1['message']['content']}")
    
    response2 = await session.send_message("How do I upgrade to Pro?")
    print(f"Agent: {response2['message']['content']}")
    
    # Get conversation history
    history = await session.get_history(limit=10)
    print(f"Messages in session: {len(history['messages'])}")
    
    # End session
    await session.end_session()
    print("Session ended")
```

**Use Cases:**
1. **Customer Support** - Track customer conversations across interactions
2. **Multi-turn Interviews** - Conduct structured dialogues with context
3. **Form Filling** - Guide users through complex forms conversationally
4. **Tutoring Systems** - Maintain learning context across lessons
5. **Sales Conversations** - Track prospect interactions with full history

---

### 2. Orchestrator Service (Port 8001)

**Purpose:** Coordinates complex workflows using Temporal. Manages multi-agent collaboration, long-running tasks, and state management.

**When to Connect:**
- Executing multi-step workflows that span multiple services
- Coordinating multiple agents working together
- Running long-running processes (hours, days, or weeks)
- When you need guaranteed execution with retries and fault tolerance
- For complex business processes with human-in-the-loop steps

**Why Connect:**
- **Durable Execution** - Workflows survive crashes and restarts
- **State Management** - Automatic state persistence and recovery
- **Retry Logic** - Built-in retry with exponential backoff
- **Visibility** - Track workflow progress and history
- **Versioning** - Deploy new workflow versions without breaking running instances

---

#### 📋 Complete API Reference

##### **2.1 Start Workflow**

**Endpoint:** `POST /v1/workflows/start`

**Purpose:** Initiate a new workflow execution with specified inputs

**Authentication:** Required (Bearer token)

**Request Schema:**
```json
{
  "workflow_type": "string",      // Required: Workflow name/type
  "inputs": {                     // Required: Workflow input parameters
    "key": "value"
  },
  "workflow_id": "string",        // Optional: Custom workflow ID (default: auto-generated)
  "task_queue": "string",         // Optional: Task queue name (default: "default")
  "timeout_seconds": 3600,        // Optional: Workflow timeout (default: 3600)
  "retry_policy": {               // Optional: Retry configuration
    "max_attempts": 3,
    "initial_interval_seconds": 1,
    "backoff_coefficient": 2.0,
    "maximum_interval_seconds": 100
  },
  "metadata": {                   // Optional: Custom metadata
    "user_id": "user_123",
    "source": "api"
  }
}
```

**Response Schema:**
```json
{
  "run_id": "wf_xxx",             // Unique workflow run identifier
  "workflow_id": "custom_id",     // Workflow identifier (custom or auto-generated)
  "workflow_type": "data_pipeline",
  "status": "running",            // "running", "completed", "failed", "cancelled"
  "started_at": "2025-10-05T12:00:00Z",
  "inputs": {...},                // Input parameters
  "metadata": {...}               // Custom metadata
}
```

**Available Workflow Types:**
```python
WORKFLOW_TYPES = {
    # Single Agent Workflows
    "simple_task": "Execute a single task with retry logic",
    "data_processing": "ETL pipeline with validation steps",
    "scheduled_job": "Cron-like scheduled execution",
    
    # Multi-Agent Workflows
    "multi_agent_research": "Coordinated research by multiple agents",
    "collaborative_writing": "Writer, editor, reviewer workflow",
    "code_review_pipeline": "Automated code review process",
    
    # Business Workflows
    "approval_workflow": "Multi-stage approval process",
    "customer_onboarding": "New customer setup workflow",
    "incident_response": "Automated incident handling",
    
    # Data Workflows
    "data_pipeline": "Extract, transform, load data",
    "ml_training_pipeline": "Model training and deployment",
    "batch_processing": "Process large datasets in chunks",
    
    # Integration Workflows
    "github_sync": "Sync GitHub issues and PRs",
    "slack_notification_campaign": "Send scheduled notifications",
    "multi_cloud_deployment": "Deploy across AWS, Azure, GCP"
}
```

**Example 1: Simple Data Processing Workflow**
```python
async def run_data_pipeline(token: str):
    """Execute a data processing workflow."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/v1/workflows/start",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workflow_type": "data_pipeline",
                "inputs": {
                    "source": "s3://my-bucket/raw-data.csv",
                    "transformations": [
                        {"type": "filter", "column": "status", "value": "active"},
                        {"type": "aggregate", "group_by": "category", "function": "sum"},
                        {"type": "sort", "column": "total", "order": "desc"}
                    ],
                    "destination": "postgres://db/processed_data",
                    "notification_email": "team@company.com"
                },
                "timeout_seconds": 7200,  # 2 hours
                "retry_policy": {
                    "max_attempts": 3,
                    "initial_interval_seconds": 60
                }
            }
        )
        return response.json()

# Execute
result = await run_data_pipeline(access_token)
print(f"Workflow started: {result['run_id']}")
print(f"Status: {result['status']}")
```

**Example 2: Multi-Agent Research Workflow**
```python
async def start_research_project(
    topic: str,
    num_sources: int,
    deadline: str,
    token: str
):
    """Start a collaborative research project."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/v1/workflows/start",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workflow_type": "multi_agent_research",
                "inputs": {
                    "topic": topic,
                    "num_sources": num_sources,
                    "deadline": deadline,
                    "agents": {
                        "researcher": {
                            "role": "primary_researcher",
                            "tools": ["github", "notion", "confluence"],
                            "search_depth": "comprehensive"
                        },
                        "analyzer": {
                            "role": "data_analyst",
                            "tools": ["python", "jupyter"],
                            "analysis_type": "statistical"
                        },
                        "writer": {
                            "role": "content_creator",
                            "tools": ["notion", "grammarly"],
                            "style": "technical"
                        },
                        "reviewer": {
                            "role": "quality_checker",
                            "tools": ["notion"],
                            "criteria": ["accuracy", "clarity", "completeness"]
                        }
                    },
                    "deliverables": {
                        "research_doc": "notion://workspace/research",
                        "data_analysis": "s3://bucket/analysis.ipynb",
                        "final_report": "notion://workspace/final-report"
                    }
                },
                "workflow_id": f"research_{topic.replace(' ', '_')}",
                "timeout_seconds": 86400,  # 24 hours
                "metadata": {
                    "project_id": "PROJ-123",
                    "priority": "high",
                    "requester": "john@company.com"
                }
            }
        )
        return response.json()

# Execute
workflow = await start_research_project(
    topic="AI Safety Regulations 2025",
    num_sources=50,
    deadline="2025-10-10T00:00:00Z",
    token=access_token
)
print(f"Research project started: {workflow['run_id']}")
```

**Example 3: Approval Workflow (Human-in-the-Loop)**
```python
async def start_approval_workflow(
    document: dict,
    approvers: list[str],
    token: str
):
    """Start a multi-stage approval workflow."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/v1/workflows/start",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "workflow_type": "approval_workflow",
                "inputs": {
                    "document": document,
                    "approval_stages": [
                        {
                            "stage": "technical_review",
                            "approvers": [approvers[0]],
                            "timeout_hours": 48,
                            "notification_channel": "slack"
                        },
                        {
                            "stage": "legal_review",
                            "approvers": [approvers[1]],
                            "timeout_hours": 72,
                            "notification_channel": "email"
                        },
                        {
                            "stage": "executive_approval",
                            "approvers": [approvers[2]],
                            "timeout_hours": 24,
                            "notification_channel": "slack"
                        }
                    ],
                    "auto_reject_on_timeout": False,
                    "notification_settings": {
                        "on_approval": True,
                        "on_rejection": True,
                        "on_timeout_warning": True
                    }
                },
                "timeout_seconds": 604800,  # 1 week
                "metadata": {
                    "document_id": document["id"],
                    "department": "engineering"
                }
            }
        )
        return response.json()

# Execute
workflow = await start_approval_workflow(
    document={"id": "DOC-123", "title": "Q4 Budget Proposal"},
    approvers=["tech_lead@co.com", "legal@co.com", "ceo@co.com"],
    token=access_token
)
```

---

##### **2.2 Get Workflow Status**

**Endpoint:** `GET /v1/workflows/{run_id}`

**Purpose:** Check the current status and progress of a running or completed workflow

**Authentication:** Required (Bearer token)

**Request:** No body required, run_id in URL path

**Response Schema:**
```json
{
  "run_id": "wf_xxx",
  "workflow_id": "custom_id",
  "workflow_type": "data_pipeline",
  "status": "running",            // "running", "completed", "failed", "cancelled"
  "progress": 45.5,               // Percentage complete (0-100)
  "current_step": "transform_data",
  "started_at": "2025-10-05T12:00:00Z",
  "updated_at": "2025-10-05T12:15:00Z",
  "completed_at": null,           // Null if still running
  "inputs": {...},                // Original inputs
  "outputs": {...},               // Results (if completed)
  "error": null,                  // Error details (if failed)
  "execution_history": [          // Step-by-step execution log
    {
      "step": "validate_source",
      "status": "completed",
      "started_at": "2025-10-05T12:00:00Z",
      "completed_at": "2025-10-05T12:01:00Z",
      "duration_seconds": 60
    },
    {
      "step": "extract_data",
      "status": "completed",
      "started_at": "2025-10-05T12:01:00Z",
      "completed_at": "2025-10-05T12:10:00Z",
      "duration_seconds": 540
    },
    {
      "step": "transform_data",
      "status": "running",
      "started_at": "2025-10-05T12:10:00Z",
      "completed_at": null,
      "duration_seconds": null
    }
  ],
  "metadata": {...}
}
```

**Example - Polling Workflow Status:**
```python
import asyncio

async def wait_for_workflow_completion(
    run_id: str,
    token: str,
    poll_interval: int = 5,
    timeout: int = 3600
):
    """Poll workflow status until completion or timeout."""
    start_time = asyncio.get_event_loop().time()
    
    async with httpx.AsyncClient() as client:
        while True:
            # Check timeout
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"Workflow {run_id} exceeded timeout of {timeout}s")
            
            # Get status
            response = await client.get(
                f"http://localhost:8001/v1/workflows/{run_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            status_data = response.json()
            
            # Log progress
            print(f"Status: {status_data['status']}, "
                  f"Progress: {status_data['progress']:.1f}%, "
                  f"Step: {status_data['current_step']}")
            
            # Check if done
            if status_data["status"] == "completed":
                print(f"✅ Workflow completed successfully!")
                return status_data
            elif status_data["status"] == "failed":
                print(f"❌ Workflow failed: {status_data['error']}")
                raise Exception(f"Workflow failed: {status_data['error']}")
            elif status_data["status"] == "cancelled":
                print(f"⚠️ Workflow was cancelled")
                return status_data
            
            # Wait before next poll
            await asyncio.sleep(poll_interval)

# Usage
result = await wait_for_workflow_completion(
    run_id="wf_xxx",
    token=access_token,
    poll_interval=10,  # Check every 10 seconds
    timeout=7200       # 2 hour timeout
)
print(f"Final outputs: {result['outputs']}")
```

---

##### **2.3 Cancel Workflow**

**Endpoint:** `POST /v1/workflows/{run_id}/cancel`

**Purpose:** Cancel a running workflow

**Authentication:** Required (Bearer token)

**Request Schema:**
```json
{
  "reason": "string",             // Optional: Cancellation reason
  "force": false                  // Optional: Force immediate cancellation (default: false)
}
```

**Response Schema:**
```json
{
  "run_id": "wf_xxx",
  "status": "cancelled",
  "cancelled_at": "2025-10-05T12:30:00Z",
  "reason": "User requested cancellation",
  "cleanup_status": "completed"   // "pending", "completed", "failed"
}
```

**Example:**
```python
async def cancel_workflow(run_id: str, reason: str, token: str):
    """Cancel a running workflow."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:8001/v1/workflows/{run_id}/cancel",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "reason": reason,
                "force": False  # Graceful shutdown
            }
        )
        return response.json()

# Usage
result = await cancel_workflow(
    run_id="wf_xxx",
    reason="Requirements changed, restarting with new parameters",
    token=access_token
)
```

---

##### **2.4 List Workflows**

**Endpoint:** `GET /v1/workflows`

**Purpose:** List workflows with filtering and pagination

**Authentication:** Required (Bearer token)

**Query Parameters:**
```
?status=running              // Filter by status (running, completed, failed, cancelled)
?workflow_type=data_pipeline // Filter by workflow type
?user_id=user_123           // Filter by user
?limit=20                   // Results per page (default: 20, max: 100)
?offset=0                   // Pagination offset
?sort_by=started_at         // Sort field (started_at, completed_at, status)
?sort_order=desc            // Sort order (asc, desc)
?start_date=2025-10-01      // Filter by start date range
?end_date=2025-10-31
```

**Response Schema:**
```json
{
  "total": 156,
  "limit": 20,
  "offset": 0,
  "workflows": [
    {
      "run_id": "wf_001",
      "workflow_type": "data_pipeline",
      "status": "completed",
      "progress": 100,
      "started_at": "2025-10-05T10:00:00Z",
      "completed_at": "2025-10-05T11:30:00Z",
      "duration_seconds": 5400
    },
    // ... more workflows
  ]
}
```

**Example - Dashboard View:**
```python
async def get_workflow_dashboard(token: str):
    """Get workflow statistics for dashboard."""
    async with httpx.AsyncClient() as client:
        # Get running workflows
        running = await client.get(
            "http://localhost:8001/v1/workflows",
            headers={"Authorization": f"Bearer {token}"},
            params={"status": "running", "limit": 100}
        )
        
        # Get recent completions
        completed = await client.get(
            "http://localhost:8001/v1/workflows",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "status": "completed",
                "sort_by": "completed_at",
                "sort_order": "desc",
                "limit": 10
            }
        )
        
        # Get failures
        failed = await client.get(
            "http://localhost:8001/v1/workflows",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "status": "failed",
                "start_date": "2025-10-05",
                "limit": 100
            }
        )
        
        return {
            "running_count": running.json()["total"],
            "recent_completions": completed.json()["workflows"],
            "failed_count": failed.json()["total"],
            "failed_workflows": failed.json()["workflows"]
        }

# Usage
dashboard = await get_workflow_dashboard(access_token)
print(f"Running: {dashboard['running_count']}")
print(f"Failed today: {dashboard['failed_count']}")
```

**Use Cases:**
1. **ETL Pipelines** - Orchestrate data extraction, transformation, and loading
2. **Multi-Agent Coordination** - Coordinate multiple AI agents on complex tasks
3. **Approval Processes** - Implement multi-stage approval workflows
4. **Scheduled Jobs** - Run periodic tasks with guaranteed execution
5. **Long-Running Operations** - Handle tasks that take hours, days, or weeks
6. **Retry Logic** - Automatically retry failed operations with backoff
7. **Saga Pattern** - Implement distributed transactions with compensation
8. **Event-Driven Workflows** - React to external events and trigger actions

---

### 3. SLM Service (Port 8003)

**Purpose:** Provides local language model inference (text generation and embeddings) without external API costs. Runs on-premises for privacy, cost savings, and low latency.

**When to Connect:**
- Need text generation without external API dependencies
- Require embeddings for semantic search or RAG
- Working with sensitive data that cannot leave your infrastructure
- Want predictable costs (no per-token pricing)
- Need consistent low-latency responses (<100ms)
- Building prototypes or development environments

**Why Connect:**
- **Zero External Costs** - No OpenAI/Anthropic API bills
- **Privacy** - Data never leaves your infrastructure
- **Low Latency** - Local inference ~50-80ms vs API calls ~500-2000ms
- **Offline Operation** - Works without internet connectivity
- **Deterministic** - Same input always produces similar output
- **No Rate Limits** - Only limited by your hardware

---

#### 📋 Complete API Reference

##### **3.1 Text Generation (Synchronous)**

**Endpoint:** `POST /v1/infer/sync`

**Purpose:** Generate text completions using local language models

**Authentication:** Required (Bearer token)

**Request Schema:**
```json
{
  "prompt": "string",             // Required: Input prompt (1-2048 chars)
  "max_tokens": 64,               // Optional: Max tokens to generate (1-256, default: 64)
  "temperature": 0.8,             // Optional: Randomness (0.0-2.0, default: 0.8)
  "top_p": 1.0,                   // Optional: Nucleus sampling (0.0-1.0, default: 1.0)
  "top_k": 50,                    // Optional: Top-k sampling (1-100, default: 50)
  "repetition_penalty": 1.0,      // Optional: Penalize repetition (0.0-2.0, default: 1.0)
  "stop_sequences": ["string"],   // Optional: Stop generation at these sequences
  "seed": null                    // Optional: Random seed for reproducibility
}
```

**Response Schema:**
```json
{
  "model": "somasuite-markov-v1",
  "completion": "string",         // Generated text
  "usage": {
    "prompt_tokens": 10,          // Input token count
    "completion_tokens": 25,      // Output token count
    "total_tokens": 35            // Total tokens
  },
  "finish_reason": "stop",        // "stop", "length", or "content_filter"
  "latency_ms": 67.3              // Generation time in milliseconds
}
```

**Example 1: Simple Text Generation**
```python
async def generate_text(prompt: str, token: str, max_tokens: int = 64):
    """Generate text completion."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8003/v1/infer/sync",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": 0.8
            }
        )
        return response.json()

# Usage
result = await generate_text(
    prompt="Write a Python function to calculate fibonacci numbers:",
    token=access_token,
    max_tokens=150
)
print(result["completion"])
print(f"Generated in {result['latency_ms']:.1f}ms")
```

**Example 2: Code Generation with Temperature Control**
```python
class CodeGenerator:
    """Generate code with configurable creativity."""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "http://localhost:8003"
    
    async def generate_function(
        self,
        description: str,
        language: str = "python",
        deterministic: bool = False
    ):
        """Generate a code function from description."""
        prompt = f"Generate a {language} function that {description}:\n\n```{language}\n"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/infer/sync",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "prompt": prompt,
                    "max_tokens": 200,
                    "temperature": 0.0 if deterministic else 0.7,
                    "stop_sequences": ["```"],
                    "seed": 42 if deterministic else None
                }
            )
            result = response.json()
            return result["completion"].strip()
    
    async def generate_docstring(self, code: str):
        """Generate docstring for existing code."""
        prompt = f"Write a detailed docstring for this function:\n\n{code}\n\nDocstring:"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/infer/sync",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "prompt": prompt,
                    "max_tokens": 150,
                    "temperature": 0.5,
                    "repetition_penalty": 1.2
                }
            )
            return response.json()["completion"].strip()

# Usage
generator = CodeGenerator(token=access_token)

# Generate deterministic code (same every time)
func = await generator.generate_function(
    "reverses a string",
    language="python",
    deterministic=True
)
print(func)

# Generate docstring
docs = await generator.generate_docstring(func)
print(docs)
```

**Example 3: Batch Processing**
```python
async def batch_generate(prompts: list[str], token: str):
    """Generate completions for multiple prompts concurrently."""
    async def generate_one(prompt: str):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8003/v1/infer/sync",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "prompt": prompt,
                    "max_tokens": 100,
                    "temperature": 0.8
                }
            )
            return response.json()
    
    # Process all prompts concurrently
    results = await asyncio.gather(*[generate_one(p) for p in prompts])
    return results

# Usage - Process 10 prompts in parallel
prompts = [
    "Explain machine learning in one sentence:",
    "What is a neural network?",
    "Define deep learning:",
    # ... 7 more prompts
]
results = await batch_generate(prompts, access_token)
for i, result in enumerate(results):
    print(f"Prompt {i}: {result['completion']}")
```

**Performance Characteristics:**
- **Latency:** P50: ~50ms, P95: ~80ms, P99: ~120ms
- **Throughput:** ~20 requests/second per CPU core
- **Max Tokens:** 256 output tokens per request
- **Context Window:** 2048 input tokens

---

##### **3.2 Embeddings Generation**

**Endpoint:** `POST /v1/embeddings`

**Purpose:** Generate vector embeddings for semantic search and similarity

**Authentication:** Required (Bearer token)

**Request Schema:**
```json
{
  "input": ["string"],            // Required: Array of texts (1-100 items, max 512 chars each)
  "model": "somasuite-embed-v1",  // Optional: Embedding model (default: somasuite-embed-v1)
  "normalize": true               // Optional: L2 normalize vectors (default: true)
}
```

**Response Schema:**
```json
{
  "model": "somasuite-embed-v1",
  "vectors": [
    {
      "embedding": [0.123, -0.456, ...],  // 768-dimensional float array
      "index": 0                           // Index in input array
    }
  ],
  "vector_length": 768,           // Dimensions (always 768)
  "usage": {
    "total_tokens": 25            // Total tokens processed
  },
  "latency_ms": 42.1              // Processing time
}
```

**Example 1: Basic Embeddings**
```python
async def get_embeddings(texts: list[str], token: str):
    """Generate embeddings for texts."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8003/v1/embeddings",
            headers={"Authorization": f"Bearer {token}"},
            json={"input": texts}
        )
        return response.json()

# Usage
embeddings = await get_embeddings(
    texts=[
        "What is machine learning?",
        "How do neural networks work?",
        "Explain deep learning"
    ],
    token=access_token
)

# Each embedding is 768 dimensions
for idx, vec in enumerate(embeddings["vectors"]):
    print(f"Text {idx}: {len(vec['embedding'])} dimensions")
    print(f"First 5 values: {vec['embedding'][:5]}")
```

**Example 2: Semantic Search Engine**
```python
import numpy as np
from typing import List, Tuple

class SemanticSearch:
    """Semantic search using embeddings."""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "http://localhost:8003"
        self.documents = []
        self.embeddings = []
    
    async def index_documents(self, documents: List[str]):
        """Index documents by generating embeddings."""
        # Generate embeddings in batches of 100
        all_embeddings = []
        for i in range(0, len(documents), 100):
            batch = documents[i:i+100]
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/embeddings",
                    headers={"Authorization": f"Bearer {self.token}"},
                    json={"input": batch}
                )
                result = response.json()
                batch_embeddings = [v["embedding"] for v in result["vectors"]]
                all_embeddings.extend(batch_embeddings)
        
        self.documents = documents
        self.embeddings = np.array(all_embeddings)
        print(f"✅ Indexed {len(documents)} documents")
    
    async def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Search for similar documents."""
        # Generate query embedding
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/embeddings",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"input": [query]}
            )
            query_embedding = np.array(response.json()["vectors"][0]["embedding"])
        
        # Calculate cosine similarity
        similarities = np.dot(self.embeddings, query_embedding)
        
        # Get top K results
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        results = [
            (self.documents[idx], float(similarities[idx]))
            for idx in top_indices
        ]
        
        return results

# Usage
search = SemanticSearch(token=access_token)

# Index knowledge base
await search.index_documents([
    "Python is a high-level programming language.",
    "Machine learning is a subset of artificial intelligence.",
    "Neural networks are inspired by biological neurons.",
    "Deep learning uses multiple layers of neural networks.",
    "Natural language processing deals with human language.",
    # ... hundreds more documents
])

# Search
results = await search.search("What is AI?", top_k=3)
for doc, score in results:
    print(f"Score {score:.3f}: {doc}")
```

**Example 3: Duplicate Detection**
```python
async def find_duplicates(
    texts: list[str],
    token: str,
    threshold: float = 0.95
):
    """Find duplicate or near-duplicate texts."""
    # Generate embeddings
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8003/v1/embeddings",
            headers={"Authorization": f"Bearer {token}"},
            json={"input": texts}
        )
        embeddings = np.array([v["embedding"] for v in response.json()["vectors"]])
    
    # Calculate pairwise similarities
    similarities = np.dot(embeddings, embeddings.T)
    
    # Find duplicates
    duplicates = []
    for i in range(len(texts)):
        for j in range(i+1, len(texts)):
            if similarities[i][j] > threshold:
                duplicates.append({
                    "text1_idx": i,
                    "text2_idx": j,
                    "text1": texts[i],
                    "text2": texts[j],
                    "similarity": float(similarities[i][j])
                })
    
    return duplicates

# Usage
texts = [
    "The quick brown fox jumps over the lazy dog",
    "A fast brown fox leaps over a lazy dog",
    "Python is a programming language",
    "The speedy brown fox jumps over the sleepy dog"
]

duplicates = await find_duplicates(texts, access_token, threshold=0.90)
for dup in duplicates:
    print(f"Similarity: {dup['similarity']:.3f}")
    print(f"  Text 1: {dup['text1']}")
    print(f"  Text 2: {dup['text2']}")
```

**Use Cases:**
1. **Semantic Search** - Find documents by meaning, not just keywords
2. **Clustering** - Group similar documents together
3. **Recommendation Systems** - Recommend similar items
4. **Duplicate Detection** - Find duplicate or near-duplicate content
5. **Classification** - Classify text by similarity to examples
6. **RAG Systems** - Retrieve relevant context for LLM prompts
7. **Question Answering** - Find answers by semantic similarity
8. **Chatbot Context** - Retrieve relevant conversation history

**Performance Characteristics:**
- **Latency:** P50: ~35ms, P95: ~42ms per batch of 100 texts
- **Throughput:** ~2,500 texts/second
- **Batch Size:** 1-100 texts per request (recommended: 50-100)
- **Vector Dimensions:** 768 (compatible with Qdrant)

---

### 4. Memory Gateway (Port 8004)

**Purpose:** Manages agent memory using Qdrant vector database. Provides persistent storage, semantic search, and RAG (Retrieval-Augmented Generation) capabilities.

**When to Connect:**
- Store conversation history and context
- Implement semantic search across documents
- Build RAG systems for context-aware responses
- Create long-term agent memory
- Store and retrieve structured knowledge
- Implement recommendation systems
- Build question-answering systems

**Why Connect:**
- **Vector Search** - Semantic similarity search with 768-dim embeddings
- **Persistent Memory** - Data survives restarts and crashes
- **Fast Retrieval** - <50ms p95 latency for searches
- **Scalable** - Handle millions of memory entries
- **Structured + Unstructured** - Store both vectors and metadata
- **RAG Support** - Built-in retrieval-augmented generation

---

#### 📋 Complete API Reference

##### **4.1 Store Memory (Remember)**

**Endpoint:** `POST /v1/remember`

**Purpose:** Store information in vector memory with semantic indexing

**Authentication:** Required (Bearer token)

**Request Schema:**
```json
{
  "key": "string",                // Required: Unique identifier
  "value": "any",                 // Required: Data to store (JSON-serializable)
  "metadata": {                   // Optional: Additional metadata
    "category": "string",
    "tags": ["string"],
    "timestamp": "2025-10-05T12:00:00Z",
    "custom_field": "value"
  },
  "ttl_seconds": null             // Optional: Time-to-live (null = permanent)
}
```

**Response Schema:**
```json
{
  "key": "string",
  "status": "stored",
  "vector_id": "vec_xxx",         // Qdrant vector ID
  "embedding_dimensions": 768,
  "indexed_at": "2025-10-05T12:00:00Z"
}
```

**Example 1: Store Conversation Context**
```python
async def remember_conversation(
    conversation_id: str,
    message: dict,
    token: str
):
    """Store conversation message in memory."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8004/v1/remember",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "key": f"conversation:{conversation_id}:msg_{message['id']}",
                "value": {
                    "role": message["role"],
                    "content": message["content"],
                    "timestamp": message["timestamp"],
                    "tokens": message.get("tokens", 0)
                },
                "metadata": {
                    "conversation_id": conversation_id,
                    "role": message["role"],
                    "timestamp": message["timestamp"],
                    "category": "conversation"
                }
            }
        )
        return response.json()

# Usage
await remember_conversation(
    conversation_id="conv_123",
    message={
        "id": "msg_001",
        "role": "user",
        "content": "How do I deploy my agent?",
        "timestamp": "2025-10-05T12:00:00Z",
        "tokens": 15
    },
    token=access_token
)
```

**Example 2: Store Knowledge Base**
```python
class KnowledgeBase:
    """Manage knowledge base in vector memory."""
    
    def __init__(self, token: str, namespace: str = "kb"):
        self.token = token
        self.namespace = namespace
        self.base_url = "http://localhost:8004"
    
    async def add_document(
        self,
        doc_id: str,
        title: str,
        content: str,
        tags: list[str] = None
    ):
        """Add a document to knowledge base."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/remember",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "key": f"{self.namespace}:doc:{doc_id}",
                    "value": {
                        "title": title,
                        "content": content,
                        "word_count": len(content.split())
                    },
                    "metadata": {
                        "doc_id": doc_id,
                        "title": title,
                        "tags": tags or [],
                        "category": "document",
                        "indexed_at": datetime.utcnow().isoformat()
                    }
                }
            )
            return response.json()
    
    async def add_fact(
        self,
        subject: str,
        predicate: str,
        object: str,
        source: str = None,
        confidence: float = 1.0
    ):
        """Add a fact triple to knowledge base."""
        fact_id = f"{subject}_{predicate}_{object}".replace(" ", "_").lower()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/remember",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "key": f"{self.namespace}:fact:{fact_id}",
                    "value": {
                        "subject": subject,
                        "predicate": predicate,
                        "object": object,
                        "source": source,
                        "confidence": confidence
                    },
                    "metadata": {
                        "type": "fact",
                        "subject": subject,
                        "category": "knowledge_graph"
                    }
                }
            )
            return response.json()

# Usage
kb = KnowledgeBase(token=access_token, namespace="company_kb")

# Add documentation
await kb.add_document(
    doc_id="deployment_guide",
    title="Kubernetes Deployment Guide",
    content="To deploy SomaAgent on Kubernetes, first create a namespace...",
    tags=["kubernetes", "deployment", "devops"]
)

# Add facts
await kb.add_fact(
    subject="SomaAgent",
    predicate="supports",
    object="Kubernetes deployment",
    source="documentation",
    confidence=1.0
)
```

**Example 3: Store User Preferences**
```python
async def store_user_preferences(user_id: str, preferences: dict, token: str):
    """Store user preferences in memory."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8004/v1/remember",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "key": f"user_prefs:{user_id}",
                "value": {
                    "theme": preferences.get("theme", "dark"),
                    "language": preferences.get("language", "en"),
                    "notifications": preferences.get("notifications", True),
                    "model": preferences.get("model", "somasuite-markov-v1"),
                    "temperature": preferences.get("temperature", 0.8)
                },
                "metadata": {
                    "user_id": user_id,
                    "category": "preferences",
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        return response.json()
```

---

##### **4.2 Retrieve Memory (Recall)**

**Endpoint:** `GET /v1/recall/{key}`

**Purpose:** Retrieve stored memory by exact key

**Authentication:** Required (Bearer token)

**Response Schema:**
```json
{
  "key": "string",
  "value": "any",                 // Stored data
  "metadata": {...},              // Metadata
  "created_at": "2025-10-05T12:00:00Z",
  "accessed_count": 5,            // Number of times accessed
  "last_accessed": "2025-10-05T14:30:00Z"
}
```

**Example:**
```python
async def recall_memory(key: str, token: str):
    """Retrieve memory by key."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8004/v1/recall/{key}",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 404:
            return None
        return response.json()

# Usage
memory = await recall_memory("user_prefs:user_123", access_token)
if memory:
    print(f"Theme: {memory['value']['theme']}")
    print(f"Language: {memory['value']['language']}")
else:
    print("Memory not found")
```

---

##### **4.3 RAG Retrieval**

**Endpoint:** `POST /v1/rag/retrieve`

**Purpose:** Semantic search across all memories using Retrieval-Augmented Generation

**Authentication:** Required (Bearer token)

**Request Schema:**
```json
{
  "query": "string",              // Required: Search query
  "top_k": 5,                     // Optional: Number of results (1-20, default: 5)
  "score_threshold": 0.7,         // Optional: Minimum similarity (0.0-1.0, default: 0.7)
  "filter": {                     // Optional: Metadata filters
    "category": "string",
    "tags": ["string"]
  },
  "include_metadata": true        // Optional: Include metadata (default: true)
}
```

**Response Schema:**
```json
{
  "query": "string",
  "results": [
    {
      "key": "string",
      "value": "any",
      "score": 0.95,              // Similarity score (0.0-1.0)
      "metadata": {...},
      "rank": 1                   // Result ranking
    }
  ],
  "total_results": 5,
  "answer": "string",             // Optional: Generated answer using results
  "sources": ["string"],          // Keys of source documents
  "latency_ms": 42.5
}
```

**Example 1: Basic RAG Search**
```python
async def rag_search(query: str, token: str, top_k: int = 5):
    """Perform semantic search using RAG."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8004/v1/rag/retrieve",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "query": query,
                "top_k": top_k,
                "score_threshold": 0.7
            }
        )
        return response.json()

# Usage
results = await rag_search(
    "How do I deploy to Kubernetes?",
    access_token,
    top_k=3
)

print(f"Answer: {results['answer']}")
print(f"\nSources ({len(results['results'])}):")
for result in results["results"]:
    print(f"  - {result['key']} (score: {result['score']:.3f})")
    print(f"    {result['value']['content'][:100]}...")
```

**Example 2: Context-Aware Agent**
```python
class ContextAwareAgent:
    """Agent with RAG-powered memory."""
    
    def __init__(self, token: str, agent_id: str):
        self.token = token
        self.agent_id = agent_id
        self.memory_url = "http://localhost:8004"
        self.slm_url = "http://localhost:8003"
    
    async def answer_with_context(self, question: str):
        """Answer question using retrieved context."""
        # 1. Retrieve relevant context
        async with httpx.AsyncClient() as client:
            rag_response = await client.post(
                f"{self.memory_url}/v1/rag/retrieve",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "query": question,
                    "top_k": 3,
                    "score_threshold": 0.75
                }
            )
            rag_data = rag_response.json()
        
        # 2. Build context from results
        context_parts = []
        for result in rag_data["results"]:
            context_parts.append(f"- {result['value'].get('content', str(result['value']))}")
        context = "\n".join(context_parts)
        
        # 3. Generate answer with context
        prompt = f"""Context from knowledge base:
{context}

User question: {question}

Based on the context above, provide an accurate and helpful answer:
"""
        
        async with httpx.AsyncClient() as client:
            slm_response = await client.post(
                f"{self.slm_url}/v1/infer/sync",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "prompt": prompt,
                    "max_tokens": 200,
                    "temperature": 0.7
                }
            )
            slm_data = slm_response.json()
        
        # 4. Store interaction in memory
        await self.remember_interaction(question, slm_data["completion"])
        
        return {
            "answer": slm_data["completion"],
            "sources": rag_data["sources"],
            "confidence_scores": [r["score"] for r in rag_data["results"]]
        }
    
    async def remember_interaction(self, question: str, answer: str):
        """Store Q&A interaction in memory."""
        interaction_id = f"{self.agent_id}_{datetime.utcnow().timestamp()}"
        
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.memory_url}/v1/remember",
                headers={"Authorization": f"Bearer {self.token}"},
                json={
                    "key": f"interaction:{interaction_id}",
                    "value": {
                        "question": question,
                        "answer": answer,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    "metadata": {
                        "agent_id": self.agent_id,
                        "category": "interaction"
                    }
                }
            )

# Usage
agent = ContextAwareAgent(token=access_token, agent_id="support_agent_1")

result = await agent.answer_with_context(
    "What are the system requirements for running SomaAgent?"
)

print(f"Answer: {result['answer']}")
print(f"Sources: {', '.join(result['sources'])}")
print(f"Confidence: {max(result['confidence_scores']):.3f}")
```

**Example 3: Filtered Search**
```python
async def search_by_category(
    query: str,
    category: str,
    token: str
):
    """Search within specific category."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8004/v1/rag/retrieve",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "query": query,
                "top_k": 10,
                "filter": {
                    "category": category
                },
                "score_threshold": 0.6
            }
        )
        return response.json()

# Search only in documentation
docs = await search_by_category(
    "authentication setup",
    category="document",
    token=access_token
)

# Search only in conversations
convos = await search_by_category(
    "deployment issues",
    category="conversation",
    token=access_token
)
```

**Use Cases:**
1. **Chatbot Memory** - Remember conversation history and context
2. **Knowledge Base Search** - Semantic search across documentation
3. **Question Answering** - Answer questions using stored knowledge
4. **Recommendation** - Recommend similar items based on preferences
5. **Context Retention** - Maintain long-term agent context
6. **User Profiles** - Store and retrieve user preferences
7. **Anomaly Detection** - Find unusual patterns in stored data
8. **Content Discovery** - Help users find relevant content

**Performance Characteristics:**
- **Write Latency:** P50: ~45ms, P95: ~67ms
- **Read Latency:** P50: ~12ms, P95: ~23ms
- **RAG Search Latency:** P50: ~38ms, P95: ~52ms
- **Storage:** Unlimited (depends on Qdrant capacity)
- **Vector Dimensions:** 768 (compatible with SLM Service)
- **Throughput:** ~1000 writes/sec, ~5000 reads/sec

---

### 5. Tool Service (Port 8005)

**Purpose:** Provides 16 pre-built adapters for external systems (GitHub, Slack, AWS, etc.).

#### Available Tools

```python
# List all available tools
GET /v1/tools

# Returns:
{
    "tools": [
        {"id": "github", "name": "GitHub", "category": "development"},
        {"id": "slack", "name": "Slack", "category": "communication"},
        {"id": "aws", "name": "AWS", "category": "cloud"},
        {"id": "kubernetes", "name": "Kubernetes", "category": "orchestration"},
        # ... 12 more
    ]
}
```

#### Execute Tool

```python
async def execute_tool(tool_id: str, action: str, params: dict, token: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:8005/v1/tools/{tool_id}/execute",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "action": action,
                "parameters": params
            }
        )
        return response.json()

# Example: Create GitHub issue
issue = await execute_tool(
    "github",
    "create_issue",
    {
        "repo": "somatechlat/somagent",
        "title": "Bug: Memory leak in orchestrator",
        "body": "Found memory leak when processing 1000+ workflows",
        "labels": ["bug", "high-priority"]
    },
    access_token
)
print(f"Created issue: {issue['url']}")
```

#### Tool Chaining

```python
# Example: Research -> Write -> Share workflow
async def research_and_share(topic: str, token: str):
    # 1. Use GitHub to search for related issues
    issues = await execute_tool(
        "github",
        "search_issues",
        {"query": topic, "repo": "somatechlat/somagent"},
        token
    )
    
    # 2. Use Notion to create research document
    doc = await execute_tool(
        "notion",
        "create_page",
        {
            "title": f"Research: {topic}",
            "content": f"Found {len(issues['items'])} related issues"
        },
        token
    )
    
    # 3. Share on Slack
    await execute_tool(
        "slack",
        "send_message",
        {
            "channel": "#research",
            "text": f"New research doc: {doc['url']}"
        },
        token
    )
    
    return doc["url"]
```

---

## 🤖 Building Your First Agent

### Complete Agent Example

This example demonstrates a production-ready agent that uses multiple platform services.

```python
"""
Customer Support Agent
- Uses memory for conversation context
- Accesses knowledge base via RAG
- Creates GitHub issues for bugs
- Sends Slack notifications
- Tracks usage and costs
"""

import asyncio
from somaagent import SomaAgentClient
from datetime import datetime

class CustomerSupportAgent:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.client = SomaAgentClient(api_key=api_key, base_url=base_url)
        self.conversation_history = []
        
    async def initialize(self):
        """Set up agent with required tools and memory."""
        # 1. Create agent identity
        self.agent = self.client.create_agent(
            name="CustomerSupportAgent",
            instructions="""
            You are a helpful customer support agent for SomaAgent platform.
            Your responsibilities:
            - Answer customer questions using the knowledge base
            - Create GitHub issues for reported bugs
            - Notify the team on Slack for urgent issues
            - Maintain conversation context using memory
            Always be polite, accurate, and proactive.
            """,
            model="somasuite-markov-v1",
            tools=["github", "slack", "notion"]
        )
        
        # 2. Load knowledge base into memory
        await self.load_knowledge_base()
        
        print(f"✅ Agent initialized: {self.agent.id}")
        
    async def load_knowledge_base(self):
        """Load common questions/answers into vector memory."""
        knowledge = [
            {
                "key": "pricing",
                "value": "SomaAgent offers three tiers: Free (1000 requests/month), "
                        "Pro ($99/month, 100K requests), Enterprise (custom pricing)"
            },
            {
                "key": "api_limits",
                "value": "Rate limits: Free tier 10 req/min, Pro tier 100 req/min, "
                        "Enterprise tier 1000 req/min"
            },
            {
                "key": "supported_models",
                "value": "We support local models (somasuite-markov-v1) and all OpenAI "
                        "compatible models via proxy"
            },
            # Add more knowledge...
        ]
        
        for item in knowledge:
            await self.remember(item["key"], item["value"])
            
    async def remember(self, key: str, value: str):
        """Store information in vector memory."""
        import httpx
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.client.base_url.replace('8000', '8004')}/v1/remember",
                headers={"Authorization": f"Bearer {self.client.api_key}"},
                json={"key": key, "value": value}
            )
    
    async def rag_search(self, query: str):
        """Search knowledge base using RAG."""
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.client.base_url.replace('8000', '8004')}/v1/rag/retrieve",
                headers={"Authorization": f"Bearer {self.client.api_key}"},
                json={"query": query}
            )
            return response.json()
    
    async def create_bug_issue(self, title: str, description: str):
        """Create a GitHub issue for bug reports."""
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.client.base_url.replace('8000', '8005')}/v1/tools/github/execute",
                headers={"Authorization": f"Bearer {self.client.api_key}"},
                json={
                    "action": "create_issue",
                    "parameters": {
                        "repo": "somatechlat/somagent",
                        "title": title,
                        "body": description,
                        "labels": ["bug", "from-support"]
                    }
                }
            )
            return response.json()
    
    async def notify_team(self, message: str, urgent: bool = False):
        """Send Slack notification to support team."""
        import httpx
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.client.base_url.replace('8000', '8005')}/v1/tools/slack/execute",
                headers={"Authorization": f"Bearer {self.client.api_key}"},
                json={
                    "action": "send_message",
                    "parameters": {
                        "channel": "#support-urgent" if urgent else "#support",
                        "text": message
                    }
                }
            )
    
    async def handle_message(self, user_message: str, user_id: str):
        """Process user message and generate response."""
        # 1. Store conversation in memory
        timestamp = datetime.utcnow().isoformat()
        await self.remember(
            f"conversation_{user_id}_{timestamp}",
            {"user": user_message, "timestamp": timestamp}
        )
        
        # 2. Search knowledge base
        rag_result = await self.rag_search(user_message)
        context = rag_result.get("answer", "")
        
        # 3. Detect intent
        is_bug_report = any(word in user_message.lower() 
                          for word in ["bug", "error", "broken", "not working"])
        is_urgent = any(word in user_message.lower() 
                       for word in ["urgent", "critical", "production down"])
        
        # 4. Generate response using SLM
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.client.base_url.replace('8000', '8003')}/v1/infer/sync",
                headers={"Authorization": f"Bearer {self.client.api_key}"},
                json={
                    "prompt": f"Context: {context}\n\nUser question: {user_message}\n\nProvide helpful response:",
                    "max_tokens": 150,
                    "temperature": 0.7
                }
            )
            ai_response = response.json()["completion"]
        
        # 5. Handle bug reports
        if is_bug_report:
            issue = await self.create_bug_issue(
                f"Bug report from {user_id}",
                f"User message: {user_message}\n\nTimestamp: {timestamp}"
            )
            ai_response += f"\n\n✅ I've created issue #{issue.get('number')} to track this bug."
            
            if is_urgent:
                await self.notify_team(
                    f"🚨 Urgent bug report from {user_id}: {user_message[:100]}...",
                    urgent=True
                )
        
        # 6. Store response in memory
        await self.remember(
            f"response_{user_id}_{timestamp}",
            {"assistant": ai_response, "timestamp": timestamp}
        )
        
        return ai_response
    
    async def run_interactive(self):
        """Run interactive support session."""
        print("\n🤖 Customer Support Agent Ready!")
        print("Type 'quit' to exit\n")
        
        user_id = "user_demo_123"
        
        while True:
            user_input = input("You: ")
            if user_input.lower() == "quit":
                break
                
            response = await self.handle_message(user_input, user_id)
            print(f"\nAgent: {response}\n")

# Usage
async def main():
    agent = CustomerSupportAgent(
        api_key="your-api-key",
        base_url="http://localhost:8000"
    )
    await agent.initialize()
    await agent.run_interactive()

if __name__ == "__main__":
    asyncio.run(main())
```

### Running the Agent

```bash
# 1. Ensure all services are running
docker-compose up -d

# 2. Get API key
curl -X POST http://localhost:8002/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 3. Run the agent
export SOMAAGENT_API_KEY="your-token-here"
python customer_support_agent.py
```

---

## 🔧 Advanced Integrations

### Multi-Agent Collaboration

```python
"""
Multi-agent system: Research team (Researcher + Writer + Editor)
"""

class ResearchTeam:
    def __init__(self, client: SomaAgentClient):
        self.client = client
        self.agents = {}
        
    async def setup_team(self):
        # 1. Researcher agent
        self.agents["researcher"] = self.client.create_agent(
            name="Researcher",
            instructions="Search for information, analyze sources, extract key facts.",
            tools=["github", "notion", "confluence"]
        )
        
        # 2. Writer agent
        self.agents["writer"] = self.client.create_agent(
            name="Writer",
            instructions="Take research findings and write clear, engaging content.",
            tools=["notion"]
        )
        
        # 3. Editor agent
        self.agents["editor"] = self.client.create_agent(
            name="Editor",
            instructions="Review content, check accuracy, improve clarity and flow.",
            tools=["notion", "slack"]
        )
    
    async def research_topic(self, topic: str):
        """Coordinate multi-agent research workflow."""
        # Start workflow via orchestrator
        workflow = self.client.start_workflow(
            workflow_type="research_pipeline",
            inputs={
                "topic": topic,
                "agents": {
                    "researcher": self.agents["researcher"].id,
                    "writer": self.agents["writer"].id,
                    "editor": self.agents["editor"].id
                },
                "steps": [
                    {"agent": "researcher", "task": "gather_sources"},
                    {"agent": "researcher", "task": "analyze_sources"},
                    {"agent": "writer", "task": "draft_article"},
                    {"agent": "editor", "task": "review_draft"},
                    {"agent": "writer", "task": "finalize"}
                ]
            }
        )
        
        # Wait for completion
        return workflow

# Usage
team = ResearchTeam(client)
await team.setup_team()
result = await team.research_topic("Quantum computing in 2025")
```

---

## 🛠️ Tool Adapters

### Complete Tool Reference

#### 1. GitHub Adapter

```python
# Available actions
actions = [
    "create_issue",
    "update_issue",
    "create_pull_request",
    "merge_pull_request",
    "create_branch",
    "commit_file",
    "search_code",
    "list_issues",
    "get_repo_info"
]

# Example: Automated PR creation
await execute_tool(
    "github",
    "create_pull_request",
    {
        "repo": "somatechlat/somagent",
        "title": "Add new feature X",
        "body": "Implements feature X as requested in #123",
        "head": "feature/x",
        "base": "main"
    },
    token
)
```

#### 2. Slack Adapter

```python
# Available actions
actions = [
    "send_message",
    "send_dm",
    "create_channel",
    "invite_to_channel",
    "upload_file",
    "schedule_message"
]

# Example: Scheduled status update
await execute_tool(
    "slack",
    "schedule_message",
    {
        "channel": "#updates",
        "text": "Weekly deployment complete! ✅",
        "post_at": "2025-10-12T09:00:00Z"
    },
    token
)
```

#### 3. AWS Adapter

```python
# Available actions
actions = [
    "s3_upload",
    "s3_download",
    "lambda_invoke",
    "ec2_describe_instances",
    "rds_query",
    "cloudwatch_get_metrics"
]

# Example: Deploy to S3
await execute_tool(
    "aws",
    "s3_upload",
    {
        "bucket": "my-app-deployments",
        "key": "builds/v1.0.0.zip",
        "file_path": "/tmp/build.zip",
        "acl": "private"
    },
    token
)
```

#### 4. Kubernetes Adapter

```python
# Available actions
actions = [
    "create_deployment",
    "scale_deployment",
    "get_pods",
    "get_logs",
    "apply_manifest",
    "delete_resource"
]

# Example: Scale deployment
await execute_tool(
    "kubernetes",
    "scale_deployment",
    {
        "namespace": "production",
        "deployment": "api-server",
        "replicas": 5
    },
    token
)
```

#### 5-16. Other Adapters

```python
# Terraform: Infrastructure as code
await execute_tool("terraform", "apply", {...})

# Notion: Knowledge base management
await execute_tool("notion", "create_page", {...})

# Jira: Project management
await execute_tool("jira", "create_ticket", {...})

# Confluence: Documentation
await execute_tool("confluence", "create_page", {...})

# Discord: Community engagement
await execute_tool("discord", "send_message", {...})

# Figma: Design collaboration
await execute_tool("figma", "export_frame", {...})

# Playwright: Browser automation
await execute_tool("playwright", "screenshot", {...})

# Linear: Issue tracking
await execute_tool("linear", "create_issue", {...})

# Plane: Project management
await execute_tool("plane", "create_task", {...})

# Azure: Cloud services
await execute_tool("azure", "deploy_app", {...})

# GCP: Google Cloud services
await execute_tool("gcp", "deploy_function", {...})

# GitLab: Version control
await execute_tool("gitlab", "create_mr", {...})
```

---

## 🧠 Memory & RAG

### Vector Memory Architecture

SomaAgentHub uses **Qdrant** (768-dimensional vectors) for semantic memory storage.

#### Memory Patterns

##### 1. Short-term Conversation Memory

```python
async def maintain_conversation_context(agent_id: str, message: str):
    """Store last N messages for context."""
    await remember(
        f"conversation:{agent_id}:latest",
        {
            "messages": recent_messages[-10:],  # Keep last 10
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

##### 2. Long-term Knowledge Memory

```python
async def build_knowledge_graph(domain: str, facts: list[dict]):
    """Build persistent knowledge base."""
    for fact in facts:
        await remember(
            f"knowledge:{domain}:{fact['id']}",
            {
                "subject": fact["subject"],
                "predicate": fact["predicate"],
                "object": fact["object"],
                "source": fact["source"],
                "confidence": fact["confidence"]
            }
        )
```

##### 3. Episodic Memory

```python
async def record_episode(agent_id: str, episode: dict):
    """Record significant events/experiences."""
    await remember(
        f"episode:{agent_id}:{episode['id']}",
        {
            "action": episode["action"],
            "outcome": episode["outcome"],
            "context": episode["context"],
            "learned": episode["learned"],
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

### RAG Implementation

```python
class RAGEngine:
    """Advanced RAG with hybrid search."""
    
    async def retrieve(self, query: str, top_k: int = 5):
        """Semantic + keyword hybrid search."""
        # 1. Get query embedding
        embedding = await get_embeddings([query])
        
        # 2. Vector search in Qdrant
        vector_results = await rag_query(query)
        
        # 3. Combine with keyword search (if needed)
        # 4. Re-rank results
        # 5. Return top K
        
        return vector_results["sources"][:top_k]
    
    async def augment_prompt(self, query: str, context_docs: list[str]):
        """Build enhanced prompt with retrieved context."""
        context = "\n\n".join([
            f"Document {i+1}: {doc}"
            for i, doc in enumerate(context_docs)
        ])
        
        prompt = f"""
Context from knowledge base:
{context}

User question: {query}

Based on the context above, provide an accurate and helpful answer:
"""
        return prompt
    
    async def generate_answer(self, query: str):
        """Complete RAG pipeline."""
        # 1. Retrieve relevant docs
        docs = await self.retrieve(query, top_k=3)
        
        # 2. Augment prompt
        prompt = await self.augment_prompt(query, docs)
        
        # 3. Generate answer
        response = await generate_text(prompt, token, max_tokens=200)
        
        return {
            "answer": response["completion"],
            "sources": docs
        }
```

---

## ⚙️ Workflows & Orchestration

### Temporal Workflow Patterns

#### 1. Simple Linear Workflow

```python
from temporalio import workflow
from datetime import timedelta

@workflow.defn
class DataProcessingWorkflow:
    @workflow.run
    async def run(self, data_url: str) -> dict:
        # Step 1: Download data
        data = await workflow.execute_activity(
            download_data,
            data_url,
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Step 2: Transform
        transformed = await workflow.execute_activity(
            transform_data,
            data,
            start_to_close_timeout=timedelta(minutes=10)
        )
        
        # Step 3: Load to database
        result = await workflow.execute_activity(
            load_to_db,
            transformed,
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        return {"status": "success", "rows_loaded": result}
```

#### 2. Parallel Execution Workflow

```python
@workflow.defn
class ParallelAnalysisWorkflow:
    @workflow.run
    async def run(self, dataset: str) -> dict:
        # Run multiple analyses in parallel
        results = await asyncio.gather(
            workflow.execute_activity(statistical_analysis, dataset),
            workflow.execute_activity(ml_analysis, dataset),
            workflow.execute_activity(visualization_analysis, dataset)
        )
        
        # Aggregate results
        return {
            "statistical": results[0],
            "ml": results[1],
            "visualization": results[2]
        }
```

#### 3. Human-in-the-Loop Workflow

```python
@workflow.defn
class ApprovalWorkflow:
    @workflow.run
    async def run(self, document: dict) -> dict:
        # Step 1: AI generates content
        draft = await workflow.execute_activity(generate_content, document)
        
        # Step 2: Wait for human approval (can wait days/weeks)
        approval = await workflow.wait_condition(
            lambda: self.approval_received,
            timeout=timedelta(days=7)
        )
        
        if not approval:
            return {"status": "timeout", "draft": draft}
        
        # Step 3: Publish approved content
        published = await workflow.execute_activity(publish_content, draft)
        
        return {"status": "published", "url": published}
    
    @workflow.signal
    async def approve(self, approved: bool):
        self.approval_received = approved
```

---

## 📊 Observability & Monitoring

### Metrics Collection

All services export Prometheus metrics on `/metrics` endpoint.

#### Key Metrics

```python
# Request metrics
http_requests_total{service="gateway-api", method="POST", endpoint="/v1/chat"}
http_request_duration_seconds{service="gateway-api", quantile="0.95"}

# SLM metrics
slm_infer_sync_requests_total{model="somasuite-markov-v1"}
slm_infer_sync_latency_seconds{model="somasuite-markov-v1", quantile="0.95"}

# Memory metrics
memory_store_operations_total{operation="remember"}
memory_vector_search_latency_seconds{quantile="0.95"}

# Workflow metrics
temporal_workflow_started_total{workflow_type="multi_agent_research"}
temporal_workflow_completed_total{workflow_type="multi_agent_research"}
temporal_workflow_duration_seconds{workflow_type="multi_agent_research"}
```

### Grafana Dashboards

Access pre-built dashboards at `http://localhost:3000`:

1. **Platform Overview** - Service health, request rates, errors
2. **Services Detail** - Per-service drill-down metrics
3. **Infrastructure** - PostgreSQL, Redis, Kafka, Qdrant health
4. **KAMACHIQ Operations** - Multi-agent workflow metrics
5. **Cost & Billing** - Token usage, cost tracking

### Alert Rules

20+ production alerts configured in `infra/monitoring/prometheus/alerts.yml`:

```yaml
# Example: High error rate
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "High error rate detected in {{ $labels.service }}"
    
# Example: Memory service down
- alert: MemoryServiceDown
  expr: up{job="memory-gateway"} == 0
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "Memory Gateway service is down"
```

### Distributed Tracing

OpenTelemetry instrumentation exports traces to Tempo:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("agent_execution")
async def execute_agent(agent_id: str, prompt: str):
    with tracer.start_as_current_span("retrieve_context"):
        context = await rag_search(prompt)
    
    with tracer.start_as_current_span("generate_response"):
        response = await generate_text(prompt, context)
    
    with tracer.start_as_current_span("execute_tools"):
        results = await execute_tools(response.tool_calls)
    
    return results
```

---

## 🚀 Production Deployment

### Kubernetes Deployment

```bash
# 1. Create namespace
kubectl create namespace somaagent

# 2. Install via Helm
cd k8s/helm/soma-agent
helm install somaagent . \
  --namespace somaagent \
  --values values.yaml \
  --set global.domain=api.yourdomain.com

# 3. Verify deployment
kubectl get pods -n somaagent
kubectl get svc -n somaagent

# 4. Check logs
kubectl logs -f deployment/gateway-api -n somaagent
```

### Environment Configuration

```yaml
# values.yaml
global:
  domain: api.yourdomain.com
  tls:
    enabled: true
    secretName: somaagent-tls

gateway:
  replicas: 3
  resources:
    requests:
      cpu: "500m"
      memory: "512Mi"
    limits:
      cpu: "2000m"
      memory: "2Gi"
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70

orchestrator:
  replicas: 2
  temporal:
    namespace: production
    host: temporal-frontend.temporal:7233

slm:
  replicas: 5
  model:
    name: "somasuite-markov-v1"
    cacheSizeMB: 1024

memory:
  replicas: 3
  qdrant:
    url: "http://qdrant:6333"
    collectionName: "agent_memory"
    vectorSize: 768

postgresql:
  enabled: true
  auth:
    username: somaagent
    database: somaagent_prod
  primary:
    persistence:
      size: 100Gi

redis:
  enabled: true
  master:
    persistence:
      size: 20Gi
  replica:
    replicaCount: 2
```

### Health Checks

```yaml
# Liveness probe
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

# Readiness probe
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

## 📚 SDK Reference

### Python SDK

#### Installation

```bash
pip install somaagent
```

#### Client Initialization

```python
from somaagent import SomaAgentClient

# Basic initialization
client = SomaAgentClient(
    api_key="your-api-key",
    base_url="https://api.somaagent.io"
)

# With custom timeout
client = SomaAgentClient(
    api_key="your-api-key",
    base_url="https://api.somaagent.io",
    timeout=60  # seconds
)

# Using environment variables
# SOMAAGENT_API_KEY and SOMAAGENT_API_URL
client = SomaAgentClient()  # Auto-loads from env
```

#### Methods

```python
# Conversations
conversation = client.create_conversation(
    messages=[{"role": "user", "content": "Hello"}],
    metadata={"user_id": "123"}
)

message = client.send_message(
    conversation_id="conv_xxx",
    content="What is SomaAgent?",
    role="user"
)

# Agents
agent = client.create_agent(
    name="MyAgent",
    instructions="You are a helpful assistant",
    model="somasuite-markov-v1",
    tools=["github", "slack"]
)

result = client.run_agent(
    agent_id="agent_xxx",
    prompt="Create a GitHub issue"
)

# Workflows
workflow = client.start_workflow(
    workflow_type="data_pipeline",
    inputs={"source": "s3://bucket/data"}
)

status = client.get_workflow_status(run_id="wf_xxx")

# Capsules
capsules = client.list_capsules(category="data", limit=20)

client.install_capsule(capsule_id="cap_xxx")

result = client.execute_capsule(
    capsule_id="cap_xxx",
    inputs={"param1": "value1"}
)

# Streaming
for chunk in client.stream_completion(
    conversation_id="conv_xxx",
    content="Write a long story"
):
    print(chunk, end="", flush=True)
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. Authentication Failed

```
Error: Invalid API key
```

**Solution:**
```python
# Verify token is valid
import httpx

async def verify_token(token: str):
    response = await httpx.AsyncClient().get(
        "http://localhost:8002/v1/auth/verify",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(response.json())
```

#### 2. Service Unavailable

```
Error: Connection refused to localhost:8004
```

**Solution:**
```bash
# Check service status
docker ps | grep memory-gateway

# View logs
docker logs somaagent-memory-gateway-1

# Restart service
docker-compose restart memory-gateway
```

#### 3. Rate Limit Exceeded

```
Error: Rate limit exceeded (429)
```

**Solution:**
```python
# Implement exponential backoff
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60)
)
async def call_api_with_retry():
    return await client.send_message(...)
```

#### 4. Workflow Timeout

```
Error: Workflow timed out after 3600s
```

**Solution:**
```python
# Increase timeout in workflow definition
@workflow.defn
class LongRunningWorkflow:
    @workflow.run
    async def run(self):
        result = await workflow.execute_activity(
            long_task,
            start_to_close_timeout=timedelta(hours=24)  # Increase
        )
```

### Debug Mode

```python
# Enable debug logging
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("somaagent")
logger.setLevel(logging.DEBUG)

# Now all API calls will be logged
client = SomaAgentClient(api_key="...")
```

### Health Check Script

```python
"""
Check health of all SomaAgentHub services.
"""

import httpx
import asyncio

SERVICES = {
    "Gateway API": "http://localhost:8000/health",
    "Orchestrator": "http://localhost:8001/health",
    "Identity": "http://localhost:8002/health",
    "SLM": "http://localhost:8003/health",
    "Memory Gateway": "http://localhost:8004/health",
    "Tool Service": "http://localhost:8005/health",
}

async def check_health():
    async with httpx.AsyncClient(timeout=5.0) as client:
        for service, url in SERVICES.items():
            try:
                response = await client.get(url)
                status = "✅ UP" if response.status_code == 200 else "❌ DOWN"
                print(f"{service:20} {status}")
            except Exception as e:
                print(f"{service:20} ❌ DOWN ({e})")

asyncio.run(check_health())
```

---

## 🎓 Best Practices

### 1. Security

```python
# ✅ DO: Use service accounts for production
service_account = await create_service_account(
    "production-agent",
    scopes=["read:agents", "execute:workflows"]
)

# ❌ DON'T: Hard-code API keys
api_key = "sk-prod-xxxxx"  # Never do this!

# ✅ DO: Use environment variables
api_key = os.getenv("SOMAAGENT_API_KEY")
```

### 2. Error Handling

```python
# ✅ DO: Implement comprehensive error handling
from somaagent.exceptions import APIError, RateLimitError

try:
    result = client.run_agent(agent_id, prompt)
except RateLimitError:
    # Wait and retry
    await asyncio.sleep(60)
    result = client.run_agent(agent_id, prompt)
except APIError as e:
    # Log error and fallback
    logger.error(f"API error: {e}")
    result = fallback_handler(prompt)
```

### 3. Resource Management

```python
# ✅ DO: Use context managers
with SomaAgentClient(api_key=key) as client:
    result = client.run_agent(agent_id, prompt)
# Client automatically closed

# ✅ DO: Limit memory usage
MAX_CONVERSATION_LENGTH = 50  # Keep only recent messages
```

### 4. Performance Optimization

```python
# ✅ DO: Batch requests when possible
embeddings = await get_embeddings(
    texts=batch_of_100_texts,  # Batch instead of 100 separate calls
    token=token
)

# ✅ DO: Use async/await for concurrent operations
results = await asyncio.gather(
    execute_tool("github", "create_issue", ...),
    execute_tool("slack", "send_message", ...),
    execute_tool("notion", "create_page", ...)
)
```

---

## 🎉 Conclusion

You now have everything you need to build production-ready AI agents on **SomaAgentHub**!

### Next Steps

1. **Build Your First Agent** - Follow the Quick Start guide
2. **Explore Examples** - Check `/examples` directory for more patterns
3. **Join Community** - Discord: discord.gg/somaagent
4. **Read Documentation** - docs.somaagent.io
5. **Deploy to Production** - Use Helm charts in `/k8s/helm`

### Support

- **Documentation**: `/docs`
- **GitHub Issues**: github.com/somatechlat/somagent/issues
- **Discord**: discord.gg/somaagent
- **Email**: support@somaagent.io

---

**Built with ❤️ by the SomaTech Team**

*Last updated: October 5, 2025*
