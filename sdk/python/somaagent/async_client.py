"""
Asynchronous client for SomaAgent API.
"""

import os
import aiohttp
from typing import List, Dict, Optional, Any, AsyncIterator
from .models import Message, Conversation, Capsule, Agent, WorkflowRun
from .exceptions import APIError, AuthenticationError, RateLimitError


class AsyncSomaAgentClient:
    """Asynchronous client for SomaAgent API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize async SomaAgent client.
        
        Args:
            api_key: API key (default: SOMAAGENT_API_KEY env var)
            base_url: API base URL (default: https://api.somaagent.io)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("SOMAAGENT_API_KEY")
        self.base_url = base_url or os.getenv(
            "SOMAAGENT_API_URL",
            "https://api.somaagent.io"
        )
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        headers = {"User-Agent": "somaagent-python/0.1.0"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.session = aiohttp.ClientSession(headers=headers, timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the client session."""
        if self.session:
            await self.session.close()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make async HTTP request to API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            Response JSON
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use async with statement.")
        
        url = f"{self.base_url}{endpoint}"
        
        async with self.session.request(method, url, **kwargs) as response:
            if response.status == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status == 429:
                raise RateLimitError("Rate limit exceeded")
            elif response.status >= 400:
                error_data = await response.json() if response.content_type == 'application/json' else {}
                raise APIError(
                    f"API error: {response.status}",
                    status_code=response.status,
                    response=error_data
                )
            
            return await response.json()
    
    # Conversations
    async def create_conversation(
        self,
        messages: Optional[List[Dict[str, str]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """
        Create a new conversation.
        
        Args:
            messages: Initial messages
            metadata: Conversation metadata
            
        Returns:
            Created conversation
        """
        data = {
            "messages": messages or [],
            "metadata": metadata or {}
        }
        
        response = await self._request("POST", "/v1/conversations", json=data)
        return Conversation(**response)
    
    async def send_message(
        self,
        conversation_id: str,
        content: str,
        role: str = "user"
    ) -> Message:
        """
        Send a message in a conversation.
        
        Args:
            conversation_id: Conversation ID
            content: Message content
            role: Message role (user, assistant, system)
            
        Returns:
            Assistant's response message
        """
        data = {
            "content": content,
            "role": role
        }
        
        response = await self._request(
            "POST",
            f"/v1/conversations/{conversation_id}/messages",
            json=data
        )
        return Message(**response)
    
    async def get_conversation(self, conversation_id: str) -> Conversation:
        """Get conversation by ID."""
        response = await self._request("GET", f"/v1/conversations/{conversation_id}")
        return Conversation(**response)

    async def health(self) -> Dict[str, Any]:
        """Return API health status."""

        return await self._request("GET", "/health")
    
    # Capsules
    async def list_capsules(
        self,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[Capsule]:
        """
        List available capsules.
        
        Args:
            category: Filter by category
            limit: Maximum number of results
            
        Returns:
            List of capsules
        """
        params = {"limit": limit}
        if category:
            params["category"] = category
        
        response = await self._request("GET", "/v1/capsules", params=params)
        return [Capsule(**c) for c in response["capsules"]]
    
    async def install_capsule(self, capsule_id: str) -> Dict[str, Any]:
        """Install a capsule."""
        return await self._request("POST", f"/v1/capsules/{capsule_id}/install")
    
    async def execute_capsule(
        self,
        capsule_id: str,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a capsule.
        
        Args:
            capsule_id: Capsule ID
            inputs: Capsule inputs
            
        Returns:
            Execution result
        """
        data = {"inputs": inputs}
        return await self._request(
            "POST",
            f"/v1/capsules/{capsule_id}/execute",
            json=data
        )
    
    # Agents
    async def create_agent(
        self,
        name: str,
        instructions: str,
        model: Optional[str] = None,
        tools: Optional[List[str]] = None
    ) -> Agent:
        """
        Create a new agent.
        
        Args:
            name: Agent name
            instructions: System instructions
            model: Model to use
            tools: List of tool/capsule IDs
            
        Returns:
            Created agent
        """
        data = {
            "name": name,
            "instructions": instructions,
            "model": model,
            "tools": tools or []
        }
        
        response = await self._request("POST", "/v1/agents", json=data)
        return Agent(**response)
    
    async def run_agent(
        self,
        agent_id: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        Run an agent.
        
        Args:
            agent_id: Agent ID
            prompt: User prompt
            
        Returns:
            Agent run result
        """
        data = {"prompt": prompt}
        return await self._request("POST", f"/v1/agents/{agent_id}/run", json=data)
    
    # Workflows
    async def start_workflow(
        self,
        workflow_type: str,
        inputs: Dict[str, Any]
    ) -> WorkflowRun:
        """
        Start a workflow.
        
        Args:
            workflow_type: Type of workflow
            inputs: Workflow inputs
            
        Returns:
            Workflow run
        """
        data = {
            "workflow_type": workflow_type,
            "inputs": inputs
        }
        
        response = await self._request("POST", "/v1/workflows/start", json=data)
        return WorkflowRun(**response)
    
    async def get_workflow_status(self, run_id: str) -> WorkflowRun:
        """Get workflow run status."""
        response = await self._request("GET", f"/v1/workflows/{run_id}")
        return WorkflowRun(**response)
    
    # Streaming
    async def stream_completion(
        self,
        conversation_id: str,
        content: str
    ) -> AsyncIterator[str]:
        """
        Stream a completion.
        
        Args:
            conversation_id: Conversation ID
            content: Message content
            
        Yields:
            Completion chunks
        """
        if not self.session:
            raise RuntimeError("Client not initialized")
        
        url = f"{self.base_url}/v1/conversations/{conversation_id}/messages"
        data = {"content": content, "stream": True}
        
        async with self.session.post(url, json=data) as response:
            if response.status != 200:
                raise APIError(f"Stream failed: {response.status}")
            
            async for line in response.content:
                decoded = line.decode('utf-8').strip()
                if decoded.startswith('data: '):
                    chunk = decoded[6:]
                    if chunk != '[DONE]':
                        yield chunk
