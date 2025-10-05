"""
Python SDK for SomaAgent.

Provides async and sync clients for interacting with the SomaAgent API.
"""

__version__ = "0.1.0"

from .client import SomaAgentClient
from .async_client import AsyncSomaAgentClient
from .models import (
    Message,
    Conversation,
    Capsule,
    Agent,
    Task,
    WorkflowRun
)
from .exceptions import (
    SomaAgentError,
    APIError,
    AuthenticationError,
    RateLimitError,
    ValidationError
)

__all__ = [
    "SomaAgentClient",
    "AsyncSomaAgentClient",
    "Message",
    "Conversation",
    "Capsule",
    "Agent",
    "Task",
    "WorkflowRun",
    "SomaAgentError",
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
]
