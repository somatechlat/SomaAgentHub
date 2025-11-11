"""
Python SDK for SomaAgent.

Provides async and sync clients for interacting with the SomaAgent API.
"""

__version__ = "0.1.0"

from .async_client import AsyncSomaAgentClient
from .client import SomaAgentClient
from .exceptions import (
    APIError,
    AuthenticationError,
    RateLimitError,
    SomaAgentError,
    ValidationError,
)
from .models import Agent, Capsule, Conversation, Message, Task, WorkflowRun
from services.common.config.base_settings import resolve_env

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
