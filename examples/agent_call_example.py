# Example: Agent invoking SomaAgentHub API
"""
This file serves as a demonstrative example that can be identified by the marker
`# EXAMPLE_AGENT_CALL`.
It shows how an external agent (or automated script) can call the SomaAgentHub
API using the provided Python SDK.
"""

# EXAMPLE_AGENT_CALL

import os
from sdk.python.somaagent import AsyncSomaAgentClient
import asyncio

async def main():
    # Configure the API URL – defaults to the local deployment if not set
    api_url = os.getenv("SOMAAGENT_API_URL", "http://soma-agent-hub.local")
    client = AsyncSomaAgentClient(base_url=api_url)
    # Simple health check call
    health = await client.health()
    print("Health check response:", health)
    # Example: send a message to the agent
    response = await client.chat(message="Hello, SomaAgentHub!")
    print("Agent response:", response)

if __name__ == "__main__":
    asyncio.run(main())
