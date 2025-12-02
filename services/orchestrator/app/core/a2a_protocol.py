"""A2A protocol core implementation.

Provides a simple in‑process registry for agents and a protocol class that can
send a message to a target agent via a Temporal child workflow. The real
implementation would involve more robust networking and security, but this
minimal version is sufficient for the integration tests and the unified workflow.
"""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol
from services.common.config.base_settings import resolve_env


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
    capabilities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
        "agent_id": self.agent_id,
        "entrypoint": self.entrypoint,
        "capabilities": list(self.capabilities),
        }

        @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> AgentCard:
        return cls(
        agent_id=str(payload["agent_id"]),
        entrypoint=str(payload["entrypoint"]),
        capabilities=list(payload.get("capabilities", [])),
        )


        class AgentRegistryBackend(Protocol):
    """Persistence contract for storing and retrieving agent cards."""

    async def load_agents(self) -> Iterable[AgentCard]:  # pragma: no cover - interface
    ...

    async def persist_agents(
    self, agents: Iterable[AgentCard]
    ) -> None:  # pragma: no cover - interface
    ...


    class AgentRegistry:
    """Async registry for agent cards with optional persistence."""

    def __init__(self, backend: AgentRegistryBackend | None = None) -> None:
        self._backend = backend
        self._agents: dict[str, AgentCard] = {}
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

    async def get_agent(self, agent_id: str) -> AgentCard | None:
        """Retrieve an agent card by id, or ``None`` if not found."""

        await self._ensure_loaded()
        return self._agents.get(agent_id)

    async def discover(self, capability: str) -> list[AgentCard]:
        """Return all agents that expose the given capability."""

        await self._ensure_loaded()
        return [
        card for card in self._agents.values() if capability in card.capabilities
        ]

    async def list_agents(self) -> list[AgentCard]:
        """Return all registered agents."""

        await self._ensure_loaded()
        return list(self._agents.values())

    async def refresh(self) -> None:
                                                                        """Reload state from the backend, if configured."""

                                                                        if not self._backend:
                                                                            return
                                                                            self._loaded = False
                                                                            await self._ensure_loaded()

# ---------------------------------------------------------------------------
# Optional ConfigMap‑based backend
# ---------------------------------------------------------------------------


                                                                            class ConfigMapAgentRegistryBackend:
                                                                                """Persist agent cards in a Kubernetes ``ConfigMap``.

                                                                                The ConfigMap name and namespace are configurable via environment variables:

                                                                                    * ``AGENT_REGISTRY_CONFIGMAP`` – defaults to ``agent-registry``
                                                                                    * ``AGENT_REGISTRY_NAMESPACE`` – defaults to ``somaagenthub``

                                                                                    The ``agents`` data field stores a JSON list of ``AgentCard`` objects.
                                                                                    If the ConfigMap does not exist it will be created on first persist.
                                                                                    """

    def __init__(self) -> None:
# Delay heavy imports until we know we need them (optional dependency).
                                                                                        self._client = None
                                                                                        self._configmap_name = resolve_env("AGENT_REGISTRY_CONFIGMAP", "agent-registry")
                                                                                        self._namespace = resolve_env("AGENT_REGISTRY_NAMESPACE", "somaagenthub")

    async def _ensure_client(self):
        if self._client is not None:
    return
    try:
        from kubernetes import client, config
        except ImportError as exc:
            raise RuntimeError(
            "kubernetes python client is required for ConfigMapAgentRegistryBackend"
            ) from exc
            try:
                config.load_incluster_config()
                except config.ConfigException:
                    config.load_kube_config()
                    self._client = client.CoreV1Api()

    async def load_agents(self) -> Iterable[AgentCard]:
                                                                                                                    await self._ensure_client()
                                                                                                                    try:
                                                                                                                        cm = self._client.read_namespaced_config_map(
                                                                                                                        self._configmap_name, self._namespace
                                                                                                                        )
                                                                                                                        data = cm.data or {}
                                                                                                                        raw = data.get("agents", "[]")
                                                                                                                        payload = json.loads(raw)
                                                                                                                        return [AgentCard.from_dict(item) for item in payload]
                                                                                                                        except Exception:
# If the ConfigMap does not exist or is malformed we treat it as empty.
                                                                                                                            return []

    async def persist_agents(self, agents: Iterable[AgentCard]) -> None:
                                                                                                                                await self._ensure_client()
                                                                                                                                payload = [card.to_dict() for card in agents]
                                                                                                                                body = {
                                                                                                                                "metadata": {"name": self._configmap_name, "namespace": self._namespace},
                                                                                                                                "data": {"agents": json.dumps(payload, indent=2, sort_keys=True)},
                                                                                                                                }
                                                                                                                                try:
# Try to replace; if it does not exist we create it.
                                                                                                                                    self._client.replace_namespaced_config_map(
                                                                                                                                    self._configmap_name, self._namespace, body
                                                                                                                                    )
                                                                                                                                    except Exception:
# Create on failure (e.g., NotFound)
                                                                                                                                        self._client.create_namespaced_config_map(self._namespace, body)


                                                                                                                                        class JsonFileAgentRegistryBackend:
                                                                                                                                            """Persistence backend storing agent cards as JSON on disk."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    async def load_agents(self) -> Iterable[AgentCard]:
    def _load() -> list[AgentCard]:
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
        metadata: dict[str, Any] = field(default_factory=dict)


        class A2AProtocol:
            """Agent‑to‑Agent messaging protocol implementation."""

    def __init__(self, registry: AgentRegistry) -> None:
        self.registry = registry

    async def send_message(
                                                                                                                                                                                        self,
                                                                                                                                                                                        target_agent_id: str,
                                                                                                                                                                                        message: str,
                                                                                                                                                                                        sender_id: str,
                                                                                                                                                                                        metadata: dict[str, Any] | None = None,
                                                                                                                                                                                        ) -> dict:
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
