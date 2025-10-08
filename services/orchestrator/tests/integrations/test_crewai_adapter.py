from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest

from services.orchestrator.app.integrations import crewai_adapter


class DummyLogger:
    def info(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - stub
        pass

    def exception(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - stub
        pass


class DummyAgent:
    def __init__(self, *, role: str, goal: str, backstory: str = "", tools: Optional[List[str]] = None, verbose: bool = False, allow_delegation: bool = True):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.tools = tools or []
        self.verbose = verbose
        self.allow_delegation = allow_delegation


class DummyTask:
    def __init__(self, *, description: str, agent: DummyAgent, expected_output: Optional[str] = None):
        self.description = description
        self.agent = agent
        self.expected_output = expected_output


class DummyProcess:
    sequential = "sequential"
    hierarchical = "hierarchical"


class DummyCrew:
    last_instance: "DummyCrew" | None = None

    def __init__(self, *, agents: List[DummyAgent], tasks: List[DummyTask], process: str, verbose: bool = False):
        self.agents = agents
        self.tasks = tasks
        self.process = process
        self.verbose = verbose
        DummyCrew.last_instance = self

    def kickoff(self) -> Dict[str, Any]:
        return {
            "agents": [agent.role for agent in self.agents],
            "tasks": [task.description for task in self.tasks],
            "process": self.process,
        }


@pytest.fixture(autouse=True)
def patch_crewai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        crewai_adapter,
        "_get_crewai_components",
        lambda: (DummyAgent, DummyTask, DummyCrew, DummyProcess),
    )
    monkeypatch.setattr(crewai_adapter, "activity", SimpleNamespace(logger=DummyLogger()))


@pytest.mark.asyncio
async def test_crewai_delegation_basic() -> None:
    result = await crewai_adapter.run_crewai_delegation(
        {
            "manager": {"role": "Project Manager", "goal": "Deliver project"},
            "workers": [
                {"role": "Engineer", "goal": "Build features"},
                {"role": "QA", "goal": "Test features", "tools": ["pytest"]},
            ],
            "tasks": [
                {"description": "Implement feature", "agent": "Engineer"},
                {"description": "Test feature", "agent": "QA", "expected_output": "Test report"},
            ],
            "tenant": "tenant-001",
            "process_type": "hierarchical",
            "metadata": {"priority": "high"},
        }
    )

    assert result["framework"] == "crewai"
    assert result["pattern"] == "task_delegation"
    assert result["tenant"] == "tenant-001"
    assert result["tasks_completed"] == 2
    assert result["process_type"] == "hierarchical"
    assert DummyCrew.last_instance is not None
    assert [task.agent.role for task in DummyCrew.last_instance.tasks] == ["Engineer", "QA"]


@pytest.mark.asyncio
async def test_crewai_delegation_defaults_to_manager() -> None:
    result = await crewai_adapter.run_crewai_delegation(
        {
            "manager": {"role": "Lead", "goal": "Coordinate"},
            "workers": [],
            "tasks": [{"description": "Prepare plan"}],
            "process_type": "sequential",
        }
    )

    assert result["tasks_completed"] == 1
    assert DummyCrew.last_instance is not None
    assert DummyCrew.last_instance.tasks[0].agent.role == "Lead"


@pytest.mark.asyncio
async def test_crewai_delegation_requires_task() -> None:
    with pytest.raises(ValueError):
        await crewai_adapter.run_crewai_delegation(
            {
                "manager": {"role": "Lead", "goal": "Coordinate"},
                "workers": [],
                "tasks": [],
            }
        )
