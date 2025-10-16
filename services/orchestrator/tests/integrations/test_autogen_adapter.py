from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

from services.orchestrator.app.integrations import autogen_adapter

# FIXME: These tests use DummyAssistantAgent/DummyUserProxyAgent/etc instead of real AutoGen.
# The monkeypatch prevents real AutoGen from executing.
# Tests prove NOTHING about real multi-agent group chat behavior.
# Replace with real integration tests using actual autogen library,
# or delete these tests if AutoGen is not actually used in production.
# See TEST_REFACTORING_ROADMAP.md for details.


class DummyLogger:
    def info(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - simple stub
        pass

    def exception(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - simple stub
        pass


class DummyAssistantAgent:
    def __init__(self, name: str, system_message: str, llm_config: Dict[str, Any]):
        self.name = name
        self.system_message = system_message
        self.llm_config = llm_config


class DummyUserProxyAgent:
    def __init__(self, name: str, human_input_mode: str, is_termination_msg, max_consecutive_auto_reply: int):
        self.name = name
        self._is_termination_msg = is_termination_msg
        self.max_consecutive_auto_reply = max_consecutive_auto_reply

    def initiate_chat(self, manager: "DummyGroupChatManager", message: str) -> None:
        manager.groupchat.messages.append({"name": self.name, "role": "user", "content": message})
        for agent in manager.groupchat.agents[1:]:
            response = f"Reply from {agent.name}"
            manager.groupchat.messages.append({"name": agent.name, "role": "assistant", "content": response})


class DummyGroupChat:
    def __init__(self, agents: List[Any], messages: List[Dict[str, Any]], max_round: int):
        self.agents = agents
        self.messages = messages
        self.max_round = max_round


class DummyGroupChatManager:
    def __init__(self, groupchat: DummyGroupChat):
        self.groupchat = groupchat


@pytest.fixture(autouse=True)
def patch_autogen(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        autogen_adapter,
        "_get_autogen_components",
        lambda: (DummyAssistantAgent, DummyGroupChat, DummyGroupChatManager, DummyUserProxyAgent),
    )
    monkeypatch.setattr(autogen_adapter, "activity", SimpleNamespace(logger=DummyLogger()))


@pytest.mark.asyncio
async def test_autogen_group_chat_basic() -> None:
    result = await autogen_adapter.run_autogen_group_chat(
        {
            "agents": [
                {"name": "researcher", "model": "gpt-4o-mini"},
                {"name": "writer", "model": "gpt-4o-mini"},
            ],
            "task": "Summarise the latest AI news",
            "tenant": "tenant-123",
            "max_rounds": 5,
            "termination_keywords": ["done"],
        }
    )

    assert result["framework"] == "autogen"
    assert result["pattern"] == "group_chat"
    assert result["tenant"] == "tenant-123"
    assert len(result["conversation"]) == 3
    assert {msg["speaker"] for msg in result["conversation"]} == {"user", "researcher", "writer"}


@pytest.mark.asyncio
async def test_autogen_group_chat_validation_error() -> None:
    with pytest.raises(ValueError):
        await autogen_adapter.run_autogen_group_chat({"agents": [], "task": "Do something"})
