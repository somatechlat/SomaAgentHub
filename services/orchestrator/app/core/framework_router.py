"""Framework router that selects the optimal integration for each multi-agent pattern."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict


class MultiAgentPattern(str, Enum):
    GROUP_CHAT = "group_chat"
    TASK_DELEGATION = "task_delegation"
    STATE_MACHINE_ROUTING = "state_machine_routing"
    A2A = "a2a"


class FrameworkRouter:
    """Detect multi-agent patterns and select the best framework adapter."""

    def __init__(self, *, default_pattern: MultiAgentPattern | None = None) -> None:
        self.default_pattern = default_pattern or MultiAgentPattern.GROUP_CHAT

    def detect_pattern(self, payload: Dict[str, Any]) -> MultiAgentPattern:
        explicit = payload.get("pattern")
        if explicit:
            try:
                return MultiAgentPattern(explicit)
            except ValueError:
                raise ValueError(f"unsupported pattern '{explicit}'") from None

        if payload.get("graph"):
            return MultiAgentPattern.STATE_MACHINE_ROUTING
        # Detect A2A messaging pattern via presence of target_agent_id
        if payload.get("target_agent_id"):
            return MultiAgentPattern.A2A

        has_manager = bool(payload.get("manager"))
        has_workers = bool(payload.get("workers"))
        has_tasks = bool(payload.get("tasks"))
        if has_manager and has_workers and has_tasks:
            return MultiAgentPattern.TASK_DELEGATION

        agents = payload.get("agents") or []
        if len(agents) >= 3:
            return MultiAgentPattern.GROUP_CHAT

        return self.default_pattern

    def select_framework(self, pattern: MultiAgentPattern) -> str:
        mapping = {
            MultiAgentPattern.GROUP_CHAT: "autogen-group-chat",
            MultiAgentPattern.TASK_DELEGATION: "crewai-delegation",
            MultiAgentPattern.STATE_MACHINE_ROUTING: "langgraph-routing",
            MultiAgentPattern.A2A: "a2a-message",
        }
        try:
            return mapping[pattern]
        except KeyError:  # pragma: no cover - defensive
            raise ValueError(f"no framework mapping for pattern '{pattern}'")

    def route(self, payload: Dict[str, Any]) -> str:
        pattern = self.detect_pattern(payload)
        return self.select_framework(pattern)
