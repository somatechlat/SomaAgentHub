"""A2A protocol core implementation.

Provides a simple in‑process registry for agents and a protocol class that can
send a message to a target agent via a Temporal child workflow. The real
implementation would involve more robust networking and security, but this
minimal version is sufficient for the integration tests and the unified workflow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Protocol


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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "entrypoint": self.entrypoint,
            "capabilities": list(self.capabilities),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "AgentCard":
        return cls(
            agent_id=str(payload["agent_id"]),
            entrypoint=str(payload["entrypoint"]),
            capabilities=list(payload.get("capabilities", [])),
        )


class AgentRegistryBackend(Protocol):
    """Persistence contract for storing and retrieving agent cards."""

    async def load_agents(self) -> Iterable[AgentCard]:  # pragma: no cover - interface
        ...

    async def persist_agents(self, agents: Iterable[AgentCard]) -> None:  # pragma: no cover - interface
        ...


class AgentRegistry:
    """Async registry for agent cards with optional persistence."""

    def __init__(self, backend: AgentRegistryBackend | None = None) -> None:
        self._backend = backend
        self._agents: Dict[str, AgentCard] = {}
        self._loaded = backend is None

    async def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        if self._backend is None:  # pragma: no cover - defensive
            self._loaded = True
            return
        cards = await self._backend.load_agents()
        self._agents = {card.agent_id: card for card in cards}
        self._loaded = True

    async def _persist(self) -> None:
        if not self._backend:
            return
        await self._backend.persist_agents(self._agents.values())

    async def register(self, card: AgentCard) -> None:
        """Register an agent card and persist if a backend is configured."""

        await self._ensure_loaded()
        self._agents[card.agent_id] = card
        await self._persist()

    async def deregister(self, agent_id: str) -> None:
        """Remove an agent card if it exists."""

        await self._ensure_loaded()
        self._agents.pop(agent_id, None)
        await self._persist()

    async def get_agent(self, agent_id: str) -> Optional[AgentCard]:
        """Retrieve an agent card by id, or ``None`` if not found."""

        await self._ensure_loaded()
        return self._agents.get(agent_id)

    async def discover(self, capability: str) -> List[AgentCard]:
        """Return all agents that expose the given capability."""

        await self._ensure_loaded()
        return [card for card in self._agents.values() if capability in card.capabilities]

    async def list_agents(self) -> List[AgentCard]:
        """Return all registered agents."""

        await self._ensure_loaded()
        return list(self._agents.values())

    async def refresh(self) -> None:
        """Reload state from the backend, if configured."""

        if not self._backend:
            return
        self._loaded = False
        await self._ensure_loaded()


class JsonFileAgentRegistryBackend:
    """Persistence backend storing agent cards as JSON on disk."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    async def load_agents(self) -> Iterable[AgentCard]:
        def _load() -> List[AgentCard]:
            if not self._path.exists():
                return []
            with self._path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            return [AgentCard.from_dict(item) for item in data]

        return await asyncio.to_thread(_load)

    async def persist_agents(self, agents: Iterable[AgentCard]) -> None:
        payload = [card.to_dict() for card in agents]

        def _write() -> None:
            with self._path.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)

        await asyncio.to_thread(_write)


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