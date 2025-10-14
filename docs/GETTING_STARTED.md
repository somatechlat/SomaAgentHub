# Getting Started with SomaAgentHub

This guide provides everything you need to get started with developing on the SomaAgentHub platform. It will walk you through setting up your environment, authenticating, and building a complete, production-ready agent.

## 1. Prerequisites

Before you begin, make sure you have the following installed:

*   Docker and Docker Compose
*   Python 3.10+
*   An active SomaAgentHub instance (or a local instance running via Docker Compose)

## 2. Authentication

All interactions with the SomaAgentHub API require a valid JWT. To obtain one, you need to authenticate with the Identity Service.

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

# Example:
# access_token = await get_access_token("admin", "admin123")
```

## 3. Building a Complete Agent

This example demonstrates a production-ready agent that uses multiple platform services to act as a customer support agent.

```python
import asyncio
import httpx
from datetime import datetime

class CustomerSupportAgent:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    async def remember(self, key: str, value: any, metadata: dict = None):
        """Stores information in the Memory Gateway."""
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.base_url.replace('8000', '8004')}/v1/remember",
                headers=self.headers,
                json={"key": key, "value": value, "metadata": metadata or {}},
            )

    async def rag_search(self, query: str):
        """Searches the knowledge base using RAG."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url.replace('8000', '8004')}/v1/rag/retrieve",
                headers=self.headers,
                json={"query": query},
            )
            return response.json()

    async def generate_response(self, prompt: str):
        """Generates a response using the SLM Service."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url.replace('8000', '8003')}/v1/infer/sync",
                headers=self.headers,
                json={"prompt": prompt, "max_tokens": 150},
            )
            return response.json()["completion"]

    async def create_github_issue(self, title: str, body: str):
        """Creates a GitHub issue using the Tool Service."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url.replace('8000', '8005')}/v1/tools/github/execute",
                headers=self.headers,
                json={
                    "action": "create_issue",
                    "parameters": {
                        "repo": "somatechlat/somagent",
                        "title": title,
                        "body": body,
                        "labels": ["bug", "from-support"],
                    },
                },
            )
            return response.json()

    async def handle_message(self, user_message: str, user_id: str):
        """Processes a user message and generates a response."""
        timestamp = datetime.utcnow().isoformat()
        await self.remember(
            f"conversation:{user_id}:{timestamp}",
            {"user": user_message, "timestamp": timestamp},
        )

        rag_result = await self.rag_search(user_message)
        context = rag_result.get("answer", "")

        prompt = f"Context: {context}\n\nUser question: {user_message}\n\nProvide helpful response:"
        ai_response = await self.generate_response(prompt)

        if "bug" in user_message.lower() or "error" in user_message.lower():
            issue = await self.create_github_issue(
                f"Bug report from {user_id}",
                f"User message: {user_message}\n\nTimestamp: {timestamp}",
            )
            ai_response += f"\n\nI've created issue #{issue.get('number')} to track this."

        await self.remember(
            f"conversation:{user_id}:{timestamp}:response",
            {"assistant": ai_response, "timestamp": timestamp},
        )
        return ai_response

async def main():
    # Replace with your actual credentials
    access_token = await get_access_token("admin", "admin123")
    agent = CustomerSupportAgent(api_key=access_token)

    print("Customer Support Agent is ready. Type 'quit' to exit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "quit":
            break
        response = await agent.handle_message(user_input, "user123")
        print(f"Agent: {response}")

if __name__ == "__main__":
    asyncio.run(main())
```
