# SomaAgent Python SDK

Official Python SDK for [SomaAgent](https://somaagent.io) - AI agents with task capsules.

## Installation

```bash
pip install somaagent
```

## Quick Start

### Synchronous Client

```python
from somaagent import SomaAgentClient

# Initialize client
client = SomaAgentClient(api_key="your-api-key")

# Create a conversation
conversation = client.create_conversation()

# Send a message
response = client.send_message(
    conversation_id=conversation.id,
    content="Hello! How can you help me?"
)

print(response.content)
```

### Asynchronous Client

```python
import asyncio
from somaagent import AsyncSomaAgentClient

async def main():
    async with AsyncSomaAgentClient(api_key="your-api-key") as client:
        # Create conversation
        conversation = await client.create_conversation()
        
        # Send message
        response = await client.send_message(
            conversation_id=conversation.id,
            content="Hello!"
        )
        
        print(response.content)

asyncio.run(main())
```

### Streaming Responses

```python
# Sync streaming
for chunk in client.stream_completion(conversation.id, "Tell me a story"):
    print(chunk, end="", flush=True)

# Async streaming
async for chunk in client.stream_completion(conversation.id, "Tell me a story"):
    print(chunk, end="", flush=True)
```

## Features

### Conversations

```python
# Create conversation
conversation = client.create_conversation(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."}
    ],
    metadata={"user_id": "123"}
)

# Send message
response = client.send_message(
    conversation_id=conversation.id,
    content="What's the weather?"
)

# Get conversation
conversation = client.get_conversation(conversation.id)
```

### Task Capsules

```python
# List available capsules
capsules = client.list_capsules(category="data-analysis", limit=10)

# Install capsule
client.install_capsule("capsule-id")

# Execute capsule
result = client.execute_capsule(
    capsule_id="capsule-id",
    inputs={"data": "input data"}
)
```

### AI Agents

```python
# Create agent
agent = client.create_agent(
    name="My Agent",
    instructions="You are a coding assistant",
    model="gpt-4",
    tools=["tool-id-1", "tool-id-2"]
)

# Run agent
result = client.run_agent(
    agent_id=agent.id,
    prompt="Write a Python function to sort a list"
)
```

### Workflows

```python
# Start workflow
run = client.start_workflow(
    workflow_type="kamachiq",
    inputs={
        "project_description": "Build a web app",
        "requirements": ["React", "FastAPI"]
    }
)

# Check status
status = client.get_workflow_status(run.id)
print(f"Status: {status.status}")
print(f"Outputs: {status.outputs}")
```

## Configuration

### Environment Variables

```bash
export SOMAAGENT_API_KEY="your-api-key"
export SOMAAGENT_API_URL="https://api.somaagent.io"  # Optional
```

### Client Options

```python
client = SomaAgentClient(
    api_key="your-api-key",
    base_url="https://api.somaagent.io",
    timeout=30  # Request timeout in seconds
)
```

## Error Handling

```python
from somaagent.exceptions import (
    SomaAgentError,
    APIError,
    AuthenticationError,
    RateLimitError,
    ValidationError
)

try:
    response = client.send_message(conversation_id, "Hello")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limit exceeded")
except APIError as e:
    print(f"API error: {e.status_code}")
```

## Models

```python
from somaagent.models import (
    Message,
    Conversation,
    Capsule,
    Agent,
    WorkflowRun
)

# All models are dataclasses with type hints
message: Message = client.send_message(...)
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black somaagent

# Type checking
mypy somaagent
```

## Links

- [Documentation](https://docs.somaagent.io)
- [API Reference](https://api.somaagent.io/docs)
- [Examples](https://github.com/somaagent/examples)
- [Support](https://somaagent.io/support)

## License

MIT
