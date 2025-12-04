# SomaAgent Python SDK

The official Python client for the SomaAgent Platform.

## Installation

```bash
pip install somaagent
```

## Configuration

Set the following environment variables:

```bash
export SOMAAGENT_API_KEY="your-api-key"
export SOMAAGENT_API_URL="https://api.somaagent.io"  # Optional, defaults to production
```

## Usage

### Client Initialization

```python
from somaagent import SomaAgentClient

client = SomaAgentClient()
# Or with explicit credentials
# client = SomaAgentClient(api_key="...", base_url="...")
```

### Multi-Tenancy

```python
# Create a new tenant
tenant = client.create_tenant(name="My Startup", tier="pro")
print(f"Created tenant: {tenant['id']}")

# Get tenant details
details = client.get_tenant(tenant['id'])
```

### Task Management

```python
# Create a task
task = client.create_task(
    name="Analyze Q3 Revenue",
    workflow_instance_id="wf-123",
    priority="high"
)
print(f"Task created: {task['id']}")

# List tasks
tasks = client.list_tasks(workflow_instance_id="wf-123")
```

### Role-Based Agents

```python
# Define a role
role = client.create_role(
    name="Financial Analyst",
    description="Analyzes financial data and generates reports",
    capabilities=["data.read", "report.write"]
)

# Bind an agent to the role
binding = client.bind_agent_to_role(
    role_id=role['id'],
    agent_id="agent-gpt4-finance"
)
```

### Memory Management

```python
# Create a memory binding for a task
memory = client.create_memory_binding(
    name="Q3 Analysis Context",
    type="vector_store",
    config={"collection": "finance_docs"}
)
```

### Blueprints & Planning

```python
# Create a blueprint
blueprint = client.create_blueprint(
    name="Financial Report Generator",
    version="1.0.0",
    content={
        "steps": ["gather_data", "analyze", "summarize"],
        "constraints": {"max_cost": 5.0}
    }
)
```

### Reinforcement Learning (RL)

```python
# Create a reasoning pipeline
pipeline = client.create_reasoning_pipeline(
    name="Market Trader",
    steps=[
        {"role": "analyst", "action": "predict"},
        {"role": "trader", "action": "execute"}
    ]
)
```

### Human-in-the-Loop (HITL)

```python
# Assign a reviewer to a workflow node
assignment = client.assign_reviewer(
    workflow_instance_id="wf-123",
    node_id="approval_node",
    reviewer_id="user-456"
)
```

### Async Client

For asynchronous applications, use `AsyncSomaAgentClient`:

```python
import asyncio
from somaagent import AsyncSomaAgentClient

async def main():
    async with AsyncSomaAgentClient() as client:
        tenant = await client.create_tenant("Async Startup")
        print(tenant)

if __name__ == "__main__":
    asyncio.run(main())
```

## Error Handling

The SDK raises specific exceptions for API errors:

```python
from somaagent import SomaAgentClient, APIError, AuthenticationError

try:
    client = SomaAgentClient()
    client.get_tenant("non-existent")
except AuthenticationError:
    print("Invalid API key")
except APIError as e:
    print(f"API Error: {e.status_code} - {e.message}")
```
