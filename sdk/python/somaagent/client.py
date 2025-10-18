"""
Synchronous client for SomaAgent API.
"""

import os
import requests
from typing import List, Dict, Optional, Any, Iterator
from .models import Message, Conversation, Capsule, Agent, Task, WorkflowRun
from .exceptions import APIError, AuthenticationError, RateLimitError


class SomaAgentClient:
    """Synchronous client for SomaAgent API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize SomaAgent client.
        
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
        self.timeout = timeout
        self.session = requests.Session()
        headers = {"User-Agent": "somaagent-python/0.1.0"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        self.session.headers.update(headers)
    
    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request to API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            Response JSON
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method,
                url,
                timeout=self.timeout,
                **kwargs
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            elif response.status_code >= 400:
                raise APIError(
                    f"API error: {response.status_code}",
                    status_code=response.status_code,
                    response=response.json() if response.content else {}
                )
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {e}")
    
    # Conversations
    def create_conversation(
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
        
        response = self._request("POST", "/v1/conversations", json=data)
        return Conversation(**response)
    
    def send_message(
        self,
        conversation_id: str,
        content: str,
        role: str = "user",
        stream: bool = False
    ) -> Message:
        """
        Send a message in a conversation.
        
        Args:
            conversation_id: Conversation ID
            content: Message content
            role: Message role (user, assistant, system)
            stream: Enable streaming
            
        Returns:
            Assistant's response message
        """
        data = {
            "content": content,
            "role": role,
            "stream": stream
        }
        
        response = self._request(
            "POST",
            f"/v1/conversations/{conversation_id}/messages",
            json=data
        )
        return Message(**response)
    
    def get_conversation(self, conversation_id: str) -> Conversation:
        """Get conversation by ID."""
        response = self._request("GET", f"/v1/conversations/{conversation_id}")
        return Conversation(**response)

    def health(self) -> Dict[str, Any]:
        """Return API health status."""

        return self._request("GET", "/health")
    
    # Capsules
    def list_capsules(
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
        
        response = self._request("GET", "/v1/capsules", params=params)
        return [Capsule(**c) for c in response["capsules"]]
    
    def install_capsule(self, capsule_id: str) -> Dict[str, Any]:
        """Install a capsule."""
        return self._request("POST", f"/v1/capsules/{capsule_id}/install")
    
    def execute_capsule(
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
        return self._request(
            "POST",
            f"/v1/capsules/{capsule_id}/execute",
            json=data
        )
    
    # Agents
    def create_agent(
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
        
        response = self._request("POST", "/v1/agents", json=data)
        return Agent(**response)
    
    def run_agent(
        self,
        agent_id: str,
        prompt: str,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Run an agent.
        
        Args:
            agent_id: Agent ID
            prompt: User prompt
            stream: Enable streaming
            
        Returns:
            Agent run result
        """
        data = {"prompt": prompt, "stream": stream}
        return self._request("POST", f"/v1/agents/{agent_id}/run", json=data)
    
    # Workflows
    def start_workflow(
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
        
        response = self._request("POST", "/v1/workflows/start", json=data)
        return WorkflowRun(**response)
    
    def get_workflow_status(self, run_id: str) -> WorkflowRun:
        """Get workflow run status."""
        response = self._request("GET", f"/v1/workflows/{run_id}")
        return WorkflowRun(**response)
    
    # Streaming
    def stream_completion(
        self,
        conversation_id: str,
        content: str
    ) -> Iterator[str]:
        """
        Stream a completion.
        
        Args:
            conversation_id: Conversation ID
            content: Message content
            
        Yields:
            Completion chunks
        """
        url = f"{self.base_url}/v1/conversations/{conversation_id}/messages"
        data = {"content": content, "stream": True}
        
        with self.session.post(
            url,
            json=data,
            stream=True,
            timeout=self.timeout
        ) as response:
            if response.status_code != 200:
                raise APIError(f"Stream failed: {response.status_code}")
            
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith('data: '):
                        chunk = decoded[6:]
                        if chunk != '[DONE]':
                            yield chunk
    
    def close(self):
        """Close the client session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
