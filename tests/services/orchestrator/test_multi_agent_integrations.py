"""Tests for multi-agent integration adapters and supporting utilities."""

from __future__ import annotations

import inspect
import sys
import types
from pathlib import Path
from typing import Any, Dict

import pytest

from services.orchestrator.app.core.a2a_protocol import (
	A2AProtocol,
	AgentCard,
	AgentNotFoundError,
	AgentRegistry,
	JsonFileAgentRegistryBackend,
)
from services.orchestrator.app.core.framework_router import FrameworkRouter, MultiAgentPattern
from services.orchestrator.app.integrations import autogen_adapter, crewai_adapter, langgraph_adapter


class _DummyLogger:
	def info(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - logging stub
		pass

	def exception(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - logging stub
		pass


class _FakeAssistantAgent:
	def __init__(self, name: str, system_message: str, llm_config: Dict[str, Any]) -> None:
		self.name = name
		self.system_message = system_message
		self.llm_config = llm_config


class _FakeGroupChat:
	def __init__(self, agents: list[Any], messages: list[Dict[str, Any]], max_round: int) -> None:
		self.agents = agents
		self.messages: list[Dict[str, Any]] = []
		self.max_round = max_round


class _FakeGroupChatManager:
	def __init__(self, groupchat: "_FakeGroupChat") -> None:
		self.groupchat = groupchat


class _FakeUserProxyAgent:
	def __init__(self, name: str, human_input_mode: str, is_termination_msg, max_consecutive_auto_reply: int) -> None:
		self.name = name
		self.is_termination_msg = is_termination_msg
		self.max_consecutive_auto_reply = max_consecutive_auto_reply
		self.human_input_mode = human_input_mode

	def initiate_chat(self, manager: "_FakeGroupChatManager", message: str) -> None:
		manager.groupchat.messages.append({"name": self.name, "role": "user", "content": message})
		reply = {
			"name": manager.groupchat.agents[1].name,
			"role": "assistant",
			"content": "TERMINATE",
		}
		manager.groupchat.messages.append(reply)


class _FakeAgent:
	def __init__(self, role: str, goal: str, backstory: str = "", tools=None, verbose: bool = False, allow_delegation: bool = True) -> None:
		self.role = role
		self.goal = goal
		self.backstory = backstory
		self.tools = tools
		self.verbose = verbose
		self.allow_delegation = allow_delegation


class _FakeTask:
	def __init__(self, description: str, agent: "_FakeAgent", expected_output: str | None) -> None:
		self.description = description
		self.agent = agent
		self.expected_output = expected_output


class _FakeCrew:
	def __init__(self, agents: list["_FakeAgent"], tasks: list["_FakeTask"], process: Any, verbose: bool = False) -> None:
		self.agents = agents
		self.tasks = tasks
		self.process = process
		self.verbose = verbose

	def kickoff(self) -> Dict[str, Any]:
		return {"tasks": [task.description for task in self.tasks]}


class _FakeProcess:
	sequential = "sequential"
	hierarchical = "hierarchical"


_FAKE_END = object()


class _FakeCompiledGraph:
	def __init__(self, graph: "_FakeStateGraph") -> None:
		self._graph = graph

	async def ainvoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
		current = self._graph.entry_point
		current_state = dict(state)
		while current:
			handler = self._graph.nodes[current]
			result = handler(current_state)
			if inspect.isawaitable(result):
				result = await result
			current_state = result or current_state
			next_node = self._next_node(current, current_state)
			if next_node is None:
				break
			current = next_node
		return current_state

	def _next_node(self, node: str, state: Dict[str, Any]) -> str | None:
		if node in self._graph.conditionals:
			condition, mapping = self._graph.conditionals[node]
			outcome = condition(state)
			target = mapping.get(outcome, mapping.get("__default__"))
		else:
			targets = self._graph.edges.get(node, [])
			target = targets[0] if targets else None
		if target is _FAKE_END:
			return None
		return target


class _FakeStateGraph:
	def __init__(self, _state_type: Any) -> None:
		self.nodes: Dict[str, Any] = {}
		self.edges: Dict[str, list[str]] = {}
		self.conditionals: Dict[str, Any] = {}
		self.entry_point: str | None = None

	def add_node(self, name: str, handler: Any) -> None:
		self.nodes[name] = handler

	def add_edge(self, source: str, target: str) -> None:
		self.edges.setdefault(source, []).append(target)

	def add_conditional_edges(self, source: str, condition: Any, mapping: Dict[str, Any]) -> None:
		self.conditionals[source] = (condition, mapping)

	def set_entry_point(self, name: str) -> None:
		self.entry_point = name

	def compile(self) -> "_FakeCompiledGraph":
		return _FakeCompiledGraph(self)

def _test_handler_entry(state: Dict[str, Any]) -> Dict[str, Any]:
	state = dict(state)
	state["counter"] = state.get("counter", 0) + 1
	return state

def _test_handler_finish(state: Dict[str, Any]) -> Dict[str, Any]:
	state = dict(state)
	state["finished"] = True
	return state

def _test_condition(state: Dict[str, Any]) -> str:
	return "next" if state.get("counter", 0) else "default"


@pytest.fixture(autouse=True)
def patch_activity_loggers(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Replace activity loggers with a dummy to silence output during tests."""
	dummy = _DummyLogger()
	for module in (autogen_adapter, crewai_adapter, langgraph_adapter):
		monkeypatch.setattr(module.activity, "logger", dummy, raising=False)


@pytest.mark.asyncio
async def test_run_autogen_group_chat_success(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Happy path for the AutoGen activity using faked components."""

	def fake_components():
		return (
			_FakeAssistantAgent,
			_FakeGroupChat,
			_FakeGroupChatManager,
			_FakeUserProxyAgent,
		)

	monkeypatch.setattr(autogen_adapter, "_get_autogen_components", fake_components)

	payload = {
		"agents": [
			{"name": "alpha", "model": "gpt-4o-mini"},
			{"name": "beta", "model": "gpt-4o-mini"},
		],
		"task": "Draft handoff summary",
		"tenant": "dev",
	}

	result = await autogen_adapter.run_autogen_group_chat(payload)

	assert result["framework"] == "autogen"
	assert result["turns"] == 2
	assert result["conversation"][0]["content"] == "Draft handoff summary"
	assert {agent["name"] for agent in result["agents"]} == {"alpha", "beta"}


@pytest.mark.asyncio
async def test_run_autogen_group_chat_requires_task(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Missing task should raise a ValueError."""
	monkeypatch.setattr(
		autogen_adapter,
		"_get_autogen_components",
		lambda: (_FakeAssistantAgent, _FakeGroupChat, _FakeGroupChatManager, _FakeUserProxyAgent),
	)

	with pytest.raises(ValueError):
		await autogen_adapter.run_autogen_group_chat({"agents": [{"name": "alpha", "model": "gpt-4o-mini"}]})


@pytest.mark.asyncio
async def test_run_crewai_delegation_assigns_workers(monkeypatch: pytest.MonkeyPatch) -> None:
	"""CrewAI activity should correctly map workers and tasks."""
	monkeypatch.setattr(
		crewai_adapter,
		"_get_crewai_components",
		lambda: (_FakeAgent, _FakeTask, _FakeCrew, _FakeProcess),
	)

	payload = {
		"manager": {"role": "Lead", "goal": "Ship"},
		"workers": [
			{"role": "analyst", "goal": "Research"},
			{"role": "writer", "goal": "Draft"},
		],
		"tasks": [{"description": "Collect data", "agent": "analyst"}],
	}

	result = await crewai_adapter.run_crewai_delegation(payload)
	assert result["framework"] == "crewai"
	assert result["tasks_completed"] == 1
	assert result["workers"][0]["role"] == "analyst"


@pytest.mark.asyncio
async def test_run_crewai_delegation_requires_tasks(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Empty task list should raise ValueError."""
	monkeypatch.setattr(
		crewai_adapter,
		"_get_crewai_components",
		lambda: (_FakeAgent, _FakeTask, _FakeCrew, _FakeProcess),
	)

	payload = {"manager": {"role": "Lead", "goal": "Ship"}, "workers": [], "tasks": []}
	with pytest.raises(ValueError):
		await crewai_adapter.run_crewai_delegation(payload)


@pytest.mark.asyncio
async def test_run_langgraph_routing_executes_handlers(monkeypatch: pytest.MonkeyPatch) -> None:
	"""LangGraph routing should follow conditional edges and produce expected state."""
	monkeypatch.setattr(langgraph_adapter, "_get_langgraph_components", lambda: (_FakeStateGraph, _FAKE_END))

	module_path = __name__
	payload = {
		"graph": {
			"nodes": [
				{"name": "entry", "handler": f"{module_path}._test_handler_entry"},
				{"name": "finish", "handler": f"{module_path}._test_handler_finish"},
			],
			"edges": [
				{
					"from": "entry",
					"condition": f"{module_path}._test_condition",
					"routes": {"next": "finish", "default": "END"},
				}
			],
			"start": "entry",
		},
		"state": {"counter": 0},
		"input_data": {"payload": "hello"},
	}

	result = await langgraph_adapter.run_langgraph_routing(payload)
	assert result["framework"] == "langgraph"
	assert result["state"]["finished"] is True
	assert result["history"][0]["node"] == "entry"
	assert result["history"][-1]["node"] == "finish"


def test_framework_router_detects_patterns() -> None:
	router = FrameworkRouter()
	assert router.detect_pattern({"pattern": "task_delegation"}) is MultiAgentPattern.TASK_DELEGATION
	assert router.detect_pattern({"graph": {"nodes": [{"name": "start"}]}}) is MultiAgentPattern.STATE_MACHINE_ROUTING
	assert router.detect_pattern({"target_agent_id": "agent-42"}) is MultiAgentPattern.A2A
	assert router.detect_pattern({"manager": {}, "workers": [{}], "tasks": [{"description": "x"}]}) is MultiAgentPattern.TASK_DELEGATION
	assert router.detect_pattern({"agents": [{}, {}, {}]}) is MultiAgentPattern.GROUP_CHAT


@pytest.mark.asyncio
async def test_agent_registry_persistence(tmp_path: Path) -> None:
	backend_path = tmp_path / "agents.json"
	backend = JsonFileAgentRegistryBackend(backend_path)
	registry = AgentRegistry(backend=backend)

	await registry.register(AgentCard(agent_id="alpha", entrypoint="wf.alpha", capabilities=["rag"]))
	await registry.register(AgentCard(agent_id="beta", entrypoint="wf.beta", capabilities=["audit", "rag"]))

	discovered = await registry.discover("rag")
	assert {c.agent_id for c in discovered} == {"alpha", "beta"}

	fresh = AgentRegistry(backend=backend)
	loaded = await fresh.get_agent("alpha")
	assert loaded is not None and loaded.entrypoint == "wf.alpha"

	await fresh.deregister("beta")
	assert await fresh.get_agent("beta") is None

	later = AgentRegistry(backend=backend)
	cards = await later.list_agents()
	assert {c.agent_id for c in cards} == {"alpha"}


@pytest.mark.asyncio
async def test_a2a_protocol_dispatch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
	backend = JsonFileAgentRegistryBackend(tmp_path / "agents.json")
	registry = AgentRegistry(backend=backend)
	await registry.register(AgentCard(agent_id="alpha", entrypoint="workflow.alpha"))

	protocol = A2AProtocol(registry)

	async def fake_execute_child_workflow(workflow_name: str, message: Any) -> Dict[str, Any]:
		return {"workflow": workflow_name, "sender": message.sender, "metadata": message.metadata}

	# Ensure temporalio.workflow module exists for monkeypatching
	try:
		import temporalio.workflow as workflow_mod  # pragma: no cover
	except Exception:  # pragma: no cover
		workflow_mod = types.SimpleNamespace()
		temporalio_pkg = types.SimpleNamespace(workflow=workflow_mod)
		sys.modules.setdefault("temporalio", temporalio_pkg)
		sys.modules["temporalio.workflow"] = workflow_mod

	monkeypatch.setattr(
		sys.modules["temporalio.workflow"],
		"execute_child_workflow",
		fake_execute_child_workflow,
		raising=False,
	)

	result = await protocol.send_message("alpha", "hello", "tester", {"trace_id": "42"})
	assert result["workflow"] == "workflow.alpha"
	assert result["sender"] == "tester"
	assert result["metadata"] == {"trace_id": "42"}

	with pytest.raises(AgentNotFoundError):
		await protocol.send_message("missing", "hello", "tester")