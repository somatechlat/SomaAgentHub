"""A2A protocol core implementation.

Provides a simple in‑process registry for agents and a protocol class that can
send a message to a target agent via a Temporal child workflow. The real
implementation would involve more robust networking and security, but this
minimal version is sufficient for the integration tests and the unified workflow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class AgentNotFoundError(RuntimeError):
    """Raised when an agent cannot be found in the registry."""

    def __init__(self, agent_id: str) -> None:
        super().__init__(f"Agent with id '{agent_id}' not found")
        self.agent_id = agent_id


@dataclass(slots=True)
class AgentCard:
    """Metadata describing an agent that can be invoked via A2A."""

    agent_id: str
    entrypoint: str  # Temporal workflow name to invoke
    capabilities: List[str] = field(default_factory=list)


class AgentRegistry:
    """Simple async in‑memory registry for agent cards."""

    def __init__(self) -> None:
        self._agents: Dict[str, AgentCard] = {}

    async def register(self, card: AgentCard) -> None:
        """Register an agent card."""
        self._agents[card.agent_id] = card

    async def get_agent(self, agent_id: str) -> Optional[AgentCard]:
        """Retrieve an agent card by id, or ``None`` if not found."""
        return self._agents.get(agent_id)

    async def discover(self, capability: str) -> List[AgentCard]:
        """Return all agents that expose the given capability."""
        return [card for card in self._agents.values() if capability in card.capabilities]


@dataclass(slots=True)
class A2AMessage:
    """Message payload sent between agents."""

    input: str
    sender: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class A2AProtocol:
    """Agent‑to‑Agent messaging protocol implementation."""

    def __init__(self, registry: AgentRegistry) -> None:
        self.registry = registry

    async def send_message(
        self,
        target_agent_id: str,
        message: str,
        sender_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict:
        """Send a message to ``target_agent_id`` and return the child workflow result.

        The implementation looks up the ``AgentCard`` in the registry, then invokes a
        Temporal child workflow using ``workflow.execute_child_workflow``. To keep the
        core library independent of Temporal runtime, the actual call is delegated to
        the caller (the activity) which imports ``temporalio.workflow`` at runtime.
        """
        target_card = await self.registry.get_agent(target_agent_id)
        if not target_card:
            raise AgentNotFoundError(target_agent_id)

        # Import lazily to avoid circular imports in type checking environments
        from temporalio import workflow

        result = await workflow.execute_child_workflow(
            target_card.entrypoint,
            A2AMessage(input=message, sender=sender_id, metadata=metadata or {}),
        )
        return result