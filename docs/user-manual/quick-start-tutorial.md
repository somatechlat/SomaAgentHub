# SomaAgentHub Quick Start Tutorial

Welcome! In this tutorial, you'll learn SomaAgentHub fundamentals by creating your first autonomous agent workflow in under 10 minutes.

By the end of this guide, you'll have:
- ✅ Set up a local SomaAgentHub instance
- ✅ Created your first AI agent conversation
- ✅ Executed a multi-step workflow
- ✅ Explored the monitoring dashboard

---

## 📋 Prerequisites

Before starting, make sure you've completed the [Installation Guide](installation.md) and have SomaAgentHub running locally.

**Required:**
- SomaAgentHub installed and running
- Docker and Docker Compose
- curl or a REST client (Postman, Insomnia, etc.)

**Verify Installation:**
```bash
# Check that services are running
curl http://localhost:10000/health
# Expected: {"status": "healthy"}
```

---

## 🚀 Tutorial Overview

We'll build a **"Smart Research Assistant"** that:
1. Takes a research topic as input
2. Breaks down research into sub-tasks
3. Coordinates multiple agents to gather information
4. Synthesizes findings into a final report

This showcases SomaAgentHub's core capabilities: **multi-agent orchestration**, **workflow management**, and **intelligent task coordination**.

---

## Step 1: Your First API Call

Let's start with a simple conversation using the Gateway API.

### 1.1 Test Basic Chat Completion

```bash
curl -X POST http://localhost:10000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "user", 
        "content": "Hello! Can you help me understand what SomaAgentHub does?"
      }
    ],
    "max_tokens": 150
  }'
```

**Expected Response:**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1699123456,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "SomaAgentHub is an enterprise agent orchestration platform that coordinates multiple AI agents to complete complex workflows..."
      },
      "finish_reason": "stop"
    }
  ]
}
```

✅ **Success!** You've made your first API call to SomaAgentHub.

### 1.2 Check Available Models

```bash
curl http://localhost:10000/v1/models \
  -H "Authorization: Bearer demo-token"
```

This shows all available AI models and their capabilities.

---

## Step 2: Create a Session-Based Conversation

Now let's create a persistent conversation session that maintains context across multiple interactions.

### 2.1 Start a New Session

```bash
curl -X POST http://localhost:10000/v1/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "user_id": "tutorial-user",
    "metadata": {
      "session_name": "Research Assistant Tutorial",
      "purpose": "learning_session"
    }
  }'
```

**Save the session_id** from the response - you'll need it for subsequent calls.

### 2.2 Continue the Conversation

```bash
# Replace SESSION_ID with the actual session ID from step 2.1
curl -X POST http://localhost:10000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "user",
        "content": "I need to research artificial intelligence in healthcare. Can you help me break this down into specific research tasks?"
      }
    ],
    "session_id": "SESSION_ID",
    "max_tokens": 300
  }'
```

The assistant will remember the context from your previous interactions within this session.

---

## Step 3: Launch a Multi-Agent Workflow

Now for the exciting part - let's create a complex workflow that coordinates multiple specialized agents.

### 3.1 Start a Research Workflow

```bash
curl -X POST http://localhost:10001/v1/workflows/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "workflow_type": "research_project",
    "input": {
      "topic": "AI in Healthcare: Current Applications and Future Trends",
      "scope": "academic_and_industry",
      "depth": "comprehensive",
      "deliverables": ["executive_summary", "detailed_report", "key_insights"]
    },
    "metadata": {
      "user_id": "tutorial-user",
      "priority": "normal",
      "deadline": "2024-01-15T18:00:00Z"
    }
  }'
```

**Save the workflow_run_id** - you'll use it to track progress.

### 3.2 Monitor Workflow Progress

```bash
# Replace WORKFLOW_RUN_ID with the actual run ID
curl http://localhost:10001/v1/workflows/WORKFLOW_RUN_ID \
  -H "Authorization: Bearer demo-token"
```

**Sample Response:**
```json
{
  "run_id": "wf_abc123def456",
  "workflow_type": "research_project",
  "status": "running",
  "progress": {
    "completed_tasks": 2,
    "total_tasks": 8,
    "current_stage": "information_gathering"
  },
  "agents": [
    {
      "agent_id": "research-agent-001",
      "role": "primary_researcher", 
      "status": "active",
      "current_task": "Analyzing recent academic papers"
    },
    {
      "agent_id": "analysis-agent-001",
      "role": "data_analyst",
      "status": "waiting",
      "current_task": "Pending data from research agent"
    }
  ],
  "estimated_completion": "2024-01-15T16:30:00Z"
}
```

### 3.3 List All Your Workflows

```bash
curl "http://localhost:10001/v1/workflows?user_id=tutorial-user&limit=10" \
  -H "Authorization: Bearer demo-token"
```

This shows all workflows you've started, their status, and completion progress.

---

## Step 4: Explore Real-Time Monitoring

SomaAgentHub includes comprehensive monitoring and observability features.

### 4.1 Access the Temporal Web UI

Open your browser and navigate to:
- **Temporal Dashboard**: http://localhost:8233

Here you can see:
- Workflow execution details
- Task distribution across agents  
- Retry attempts and error handling
- Complete execution history

### 4.2 View Service Metrics

```bash
# Get platform metrics
curl http://localhost:10000/metrics

# Get orchestrator metrics  
curl http://localhost:10001/metrics

# Get policy engine metrics
curl http://localhost:10003/metrics
```

### 4.3 Check Service Health

```bash
# Health check all services
for port in 10000 10001 10002 10005 10004 10003; do
  echo "Checking port $port:"
  curl -s http://localhost:$port/health | jq .
  echo
done
```

---

## Step 5: Working with Memory and Context

SomaAgentHub's memory system allows agents to retain and recall information across sessions.

### 5.1 Store Information in Memory

```bash
curl -X POST http://localhost:10004/v1/memories \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "user_id": "tutorial-user",
    "memory_type": "research_findings",
    "content": "AI in healthcare shows 40% efficiency improvement in diagnostic accuracy according to recent Stanford study",
    "metadata": {
      "source": "Stanford Medical AI Research 2024",
      "relevance_score": 0.95,
      "topic": "healthcare_ai_diagnostics"
    }
  }'
```

### 5.2 Recall Relevant Information

```bash
curl -X POST http://localhost:10004/v1/recall \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "query": "diagnostic accuracy improvements in medical AI",
    "user_id": "tutorial-user",
    "limit": 5,
    "similarity_threshold": 0.7
  }'
```

The memory system uses semantic search to find relevant information based on meaning, not just keywords.

---

## Step 6: Advanced Features

### 6.1 Policy and Governance

SomaAgentHub includes built-in governance to ensure AI agents operate within defined boundaries.

```bash
# Check if a query would be allowed by current policies
curl -X POST http://localhost:10003/v1/evaluate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "tenant": "default",
    "user": "tutorial-user", 
    "prompt": "Generate a research report on AI in healthcare",
    "role": "researcher",
    "metadata": {
      "session_id": "tutorial-session",
      "workflow_id": "research_project"
    }
  }'
```

### 6.2 Tool Integration

SomaAgentHub can connect agents to external tools and services.

```bash
# List available tools
curl http://localhost:10006/v1/tools \
  -H "Authorization: Bearer demo-token"

# Use a specific tool (example: web search)
curl -X POST http://localhost:10006/v1/tools/web_search/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-token" \
  -d '{
    "query": "latest AI healthcare research 2024",
    "limit": 10,
    "metadata": {
      "user_id": "tutorial-user"
    }
  }'
```

---

## Step 7: Complete Workflow Example

Let's put it all together with a complete Python example that demonstrates the full workflow:

### 7.1 Python Client Example

```python
import requests
import json
import time

class SomaAgentHubClient:
    def __init__(self, base_url="http://localhost:10000", token="demo-token"):
        self.base_url = base_url
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def create_session(self, user_id, session_name):
        """Create a new conversation session"""
        response = requests.post(
            f"{self.base_url}/v1/sessions",
            headers=self.headers,
            json={
                "user_id": user_id,
                "metadata": {"session_name": session_name}
            }
        )
        return response.json()["session_id"]
    
    def chat(self, messages, session_id=None):
        """Send a chat message"""
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "max_tokens": 500
        }
        if session_id:
            payload["session_id"] = session_id
            
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers=self.headers,
            json=payload
        )
        return response.json()
    
    def start_workflow(self, workflow_type, input_data, metadata=None):
        """Start a multi-agent workflow"""
        orchestrator_url = self.base_url.replace("10000", "10001")
        response = requests.post(
            f"{orchestrator_url}/v1/workflows/start",
            headers=self.headers,
            json={
                "workflow_type": workflow_type,
                "input": input_data,
                "metadata": metadata or {}
            }
        )
        return response.json()["run_id"]
    
    def check_workflow_status(self, run_id):
        """Check workflow progress"""
        orchestrator_url = self.base_url.replace("10000", "10001")
        response = requests.get(
            f"{orchestrator_url}/v1/workflows/{run_id}",
            headers=self.headers
        )
        return response.json()

# Example usage
client = SomaAgentHubClient()

# Create session and start conversation
session_id = client.create_session("tutorial-user", "AI Research Session")
print(f"Created session: {session_id}")

# Have a conversation
chat_response = client.chat([
    {"role": "user", "content": "Help me research quantum computing applications"}
], session_id)

print(f"AI Response: {chat_response['choices'][0]['message']['content']}")

# Start a research workflow
workflow_id = client.start_workflow(
    workflow_type="research_project",
    input_data={
        "topic": "Quantum Computing in Cryptography",
        "scope": "technical_analysis",
        "depth": "detailed"
    },
    metadata={"user_id": "tutorial-user"}
)

print(f"Started workflow: {workflow_id}")

# Monitor progress
while True:
    status = client.check_workflow_status(workflow_id)
    print(f"Workflow status: {status['status']}")
    
    if status["status"] in ["completed", "failed", "cancelled"]:
        break
        
    time.sleep(5)

print("Workflow completed!")
```

---

## Step 8: Troubleshooting Your Setup

If you encounter issues during the tutorial:

### Common Problems

**1. Connection Refused**
```bash
# Check if services are running
docker compose ps
# Restart if needed
make dev-up
```

**2. Authentication Errors**
```bash
# Verify you're using the correct demo token
curl -H "Authorization: Bearer demo-token" http://localhost:10000/health
```

**3. Workflow Doesn't Start**
```bash
# Check orchestrator logs
docker compose logs orchestrator
# Ensure Temporal is running
curl http://localhost:8233
```

**4. Memory Operations Fail**
```bash
# Check memory gateway status
curl http://localhost:10004/health
# Verify Qdrant is running
docker compose logs qdrant
```

---

## 🎉 Congratulations!

You've successfully completed the SomaAgentHub Quick Start Tutorial! You now know how to:

✅ **Make API calls** to the Gateway API  
✅ **Create sessions** for persistent conversations  
✅ **Launch workflows** that coordinate multiple agents  
✅ **Monitor progress** using the dashboard and APIs  
✅ **Store and recall information** using the memory system  
✅ **Integrate tools** and external services  
✅ **Handle policies** and governance constraints  

---

## 🚀 Next Steps

Now that you understand the basics, explore these advanced topics:

### Immediate Next Steps
1. **[Explore Core Features](features/)** - Deep dive into specific capabilities
2. **[Review Integration Examples](../SOMAGENTHUB_INTEGRATION_GUIDE.md)** - See real-world usage patterns  
3. **[Read the FAQ](faq.md)** - Get answers to common questions

### Advanced Learning
4. **[Technical Manual](../technical-manual/)** - Learn deployment and operations
5. **[Development Manual](../development-manual/)** - Contribute code and customize
6. **[Onboarding Manual](../onboarding-manual/)** - Get your team up to speed

### Build Something Cool
- **Customer Support Bot** - Multi-agent customer service automation
- **Research Pipeline** - Automated research and analysis workflows  
- **Code Assistant** - AI pair programming with multiple specialized agents
- **Data Processing** - ETL pipelines with intelligent error handling

---

## 📞 Getting Help

- **Documentation**: Comprehensive guides in the [docs directory](../)
- **Community**: GitHub Issues and Discussions
- **Examples**: Check `examples/` directory for more sample projects
- **Integration Guide**: Detailed API documentation and examples

---

**Ready to build the future of autonomous agents? The possibilities are endless with SomaAgentHub!** 🚀
