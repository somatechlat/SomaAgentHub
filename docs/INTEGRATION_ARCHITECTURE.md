⚠️ WE DO NOT MOCK, WE DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, WE USE MATH — PERFECT MATH — TO SURPASS ANY PROBLEM AND WE ONLY ABIDE TRUTH AND REAL SERVERS, REAL DATA.

# 🎯 SomaAgentHub Integration Architecture

**Date**: October 8, 2025  
**Strategy**: **INTEGRATE** existing frameworks (not rebuild)  
**Execution Tracks**: Track A — Observability & Telemetry • Track B — Multi-Framework Orchestration  
**Timeline**: 3-week accelerated rollout (Sprint 0 + Weeks 1-3)  
**Approach**: Temporal-first orchestration, policy guardrails, and proven agent frameworks

## Reality Check — October 8, 2025

- AutoGen, CrewAI, and LangGraph adapters exist in `services/orchestrator/app/integrations/` and are callable via Temporal activities; they currently lack automated tests, retries, and cost/latency instrumentation.
- The unified workflow in `services/orchestrator/app/workflows/unified_multi_agent.py` runs the router-backed orchestration path, but there is no load testing data, benchmarking, or CI coverage guarding regressions.
- The A2A adapter is present, yet the agent registry is in-memory, no persistence or discovery API exists, and there are no production call sites exercising the pathway.
- Track A observability work (Langfuse/OpenLLMetry/Giskard) has not begun; there are no Helm charts, tracing helpers, or evaluation jobs checked into the repository.
- Framework dependencies (`pyautogen`, `crewai`, `langgraph`) live in `services/orchestrator/requirements.txt`, but they are missing from the root `requirements-dev.txt`; fresh developer environments that only install the dev bundle will not have the frameworks available.
- Documentation sections describing load testing, Grafana dashboards, and production launch are legacy goals; no artifacts supporting those claims exist in `infra/`, `monitoring/`, or `runbooks/`.

> **Action:** Treat everything below as an aspirational plan unless cross-referenced with live code. Update each section once the corresponding implementation lands with tests and observability.

---

## 🏆 THE STRATEGY: Stand on Giants' Shoulders

### **Core Decision**

After analyzing **9 world-class frameworks** and comparing with our current implementation, we made a critical decision:

**❌ DON'T BUILD FROM SCRATCH** (40+ weeks, high risk)  
**✅ INTEGRATE PROVEN FRAMEWORKS** (3 weeks, low risk)

### **Why This Makes Sense**

| Approach | Time | Risk | Quality | Maintenance |
|----------|------|------|---------|-------------|
| Build from scratch | 40+ weeks | High | Unknown | High burden |
| **Integrate frameworks** | **3 weeks** | **Low** | **Proven** | **Community-driven** |

**ROI**: 13:1 (integrate vs. build)

---

## 🏗️ THE ARCHITECTURE

### **Layered Integration Model**

```
┌─────────────────────────────────────────────────────────────────┐
│                    SomaAgentHub Platform                        │
│                   (Our Unique Value Layer)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         LAYER 1: Temporal Orchestration (OUR VALUE)      │  │
│  │                                                          │  │
│  │  • Fault tolerance & durability                         │  │
│  │  • Workflow execution & retries                         │  │
│  │  • Long-running processes                               │  │
│  │  • Event sourcing & history                             │  │
│  │  • Observability & tracing                              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │      LAYER 2: Policy & Security Layer (OUR VALUE)        │  │
│  │                                                          │  │
│  │  • Policy evaluation before execution                   │  │
│  │  • Identity & access management                         │  │
│  │  • Audit trail & compliance                             │  │
│  │  • Rate limiting & quotas                               │  │
│  │  • Tenant isolation                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │     LAYER 3: Multi-Framework Router (OUR VALUE)          │  │
│  │                                                          │  │
│  │  Pattern Detection (2025 scope):                        │  │
│  │    "group_chat"        → AutoGen activity               │  │
│  │    "task_delegation"   → CrewAI activity                │  │
│  │    "state_machine"     → LangGraph activity             │  │
│  │    "a2a"               → A2A message activity           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │   LAYER 4: Framework Integration Layer (ADAPTERS)        │  │
│  │                                                          │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │  │
│  │  │ AutoGen  │ │ CrewAI   │ │LangGraph │ │  A2A     │ │  │
│  │  │ Adapter  │ │ Adapter  │ │ Adapter  │ │ Adapter  │ │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ │  │
│  │      ↓            ↓            ↓            ↓         │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │  │
│  │  │ AutoGen  │ │ CrewAI   │ │LangGraph │ │ Soma A2A │ │  │
│  │  │Framework │ │Framework │ │Framework │ │ Protocol │ │  │
│  │  │(MIT Lic) │ │(MIT Lic) │ │(MIT Lic) │ │ (in-house)│ │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │        LAYER 5: A2A Protocol Layer (STANDARD)            │  │
│  │                                                          │  │
│  │  • Agent discovery via agent cards                      │  │
│  │  • Agent-to-agent messaging                             │  │
│  │  • Federation with external agents                      │  │
│  │  • Protocol-based interoperability                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 WHAT WE BUILD vs. WHAT WE USE

### **What We BUILD (Our Unique Value)**

| Component | Purpose | Lines | Value |
|-----------|---------|-------|-------|
| **Temporal Orchestration** | Fault-tolerant workflow execution | 500 | Production-grade reliability |
| **Policy Engine Integration** | Security, compliance, governance | 300 | Enterprise security |
| **Multi-Framework Router** | Smart pattern detection & routing | 250 | Flexibility |
| **Unified Workflow API** | Single entrypoint for every pattern | 220 | Developer experience |
| **Adapter Layer (AutoGen/CrewAI/LangGraph)** | Temporal ↔ Framework integration | 650 | Seamless integration |
| **Somatrace Observability** | Metrics, traces, logging | 180 | Production visibility |

**Total We Build (Track A + Track B)**: ~2,100 lines delivered/maintained by SomaAgent

### **What We USE (Proven Frameworks)**

| Framework | What We Get | Lines (Theirs) | Battle-Tested |
|-----------|-------------|----------------|---------------|
| **AutoGen** | Group chat, speaker selection, termination | 50,000+ | ✅ 2+ years |
| **CrewAI** | Role-based design, task delegation | 30,000+ | ✅ 1+ year |
| **LangGraph** | State machines, conditional routing | 40,000+ | ✅ 1+ year |

**Total We Use (current scope)**: ~120,000 lines (proven, community maintained)

**Leverage Ratio**: 57:1 (we maintain 2,100 lines, benefit from 120,000+)

> 🔭 **Future Expansion Backlog**: CAMEL role-play adapters and Rowboat-style pipelines remain on the roadmap once the current integrations are production-hardened.

---

## 📦 INTEGRATION PATTERNS

### **Pattern 1: AutoGen Integration (Group Chat)** *(Implemented)*

```python
# File: services/orchestrator/app/integrations/autogen_adapter.py

"""AutoGen integration for group-chat style multi-agent conversations."""

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Optional

from temporalio import activity


@dataclass(slots=True)
class AgentConfig:
    name: str
    model: str
    system_message: str = ""
    llm_config: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "AgentConfig":
        # ... validation logic ...
        return cls(
            name=str(payload["name"]).strip(),
            model=str(payload.get("model", "gpt-4o-mini")).strip(),
            system_message=str(payload.get("system_message", "")),
            llm_config=payload.get("llm_config"),
        )


def _get_autogen_components():
    from autogen import AssistantAgent, GroupChat, GroupChatManager, UserProxyAgent

    return AssistantAgent, GroupChat, GroupChatManager, UserProxyAgent


def _build_llm_config(agent: AgentConfig, default_temperature: float) -> Dict[str, Any]:
    if agent.llm_config:
        return agent.llm_config
    return {
        "config_list": [{"model": agent.model}],
        "temperature": default_temperature,
    }


def _termination_predicate(keywords: Iterable[str]):
    lowered = [kw.lower() for kw in keywords if kw]

    def _is_termination(message: Dict[str, Any]) -> bool:
        if not lowered:
            return False
        content = message.get("content") or ""
        return any(keyword in content.lower() for keyword in lowered)

    return _is_termination


def _serialize_conversation(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    serialized: List[Dict[str, Any]] = []
    for msg in messages:
        serialized.append(
            {
                "speaker": msg.get("name") or msg.get("role", "unknown"),
                "role": msg.get("role", "assistant"),
                "content": msg.get("content", ""),
                "metadata": {
                    "thought": msg.get("thought"),
                    "summary": msg.get("summary"),
                },
            }
        )
    return serialized


@activity.defn(name="autogen-group-chat")
async def run_autogen_group_chat(payload: Dict[str, Any]) -> Dict[str, Any]:
    agents = payload.get("agents")
    task = payload.get("task")
    tenant = payload.get("tenant", "default")
    metadata = payload.get("metadata")
    max_rounds = int(payload.get("max_rounds", 20))
    temperature = float(payload.get("temperature", 0.7))
    termination_keywords = payload.get("termination_keywords")

    if agents is None:
        raise ValueError("at least one agent configuration is required")
    if task is None:
        raise ValueError("task description is required")
    if not agents:
        raise ValueError("at least one agent configuration is required")
    if max_rounds <= 0:
        raise ValueError("max_rounds must be positive")

    agent_configs = [AgentConfig.from_dict(agent) for agent in agents]
    AssistantAgent, GroupChat, GroupChatManager, UserProxyAgent = _get_autogen_components()

    autogen_agents: List[AssistantAgent] = []
    for config in agent_configs:
        llm_config = _build_llm_config(config, default_temperature=temperature)
        autogen_agents.append(
            AssistantAgent(
                name=config.name,
                system_message=config.system_message,
                llm_config=llm_config,
            )
        )

    term_keywords = termination_keywords or ["TERMINATE", "DONE"]
    user_proxy = UserProxyAgent(
        name="user",
        human_input_mode="NEVER",
        is_termination_msg=_termination_predicate(term_keywords),
        max_consecutive_auto_reply=0,
    )

    groupchat = GroupChat(agents=[user_proxy, *autogen_agents], messages=[], max_round=max_rounds)
    manager = GroupChatManager(groupchat=groupchat)

    user_proxy.initiate_chat(manager, message=task)

    conversation = _serialize_conversation(groupchat.messages)

    return {
        "framework": "autogen",
        "pattern": "group_chat",
        "tenant": tenant,
        "metadata": metadata or {},
        "agents": [asdict(config) for config in agent_configs],
        "conversation": conversation,
        "turns": len(conversation),
    }
```

### **Pattern 2: CrewAI Integration (Task Delegation)** *(Implemented)*

```python
# File: services/orchestrator/app/integrations/crewai_adapter.py

"""CrewAI integration activity for hierarchical and sequential delegation."""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from temporalio import activity


@dataclass(slots=True)
class ManagerConfig:
    role: str
    goal: str
    backstory: str = ""
    verbose: bool = True
    allow_delegation: bool = True

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ManagerConfig":
        # ... validation logic ...
        return cls(
            role=str(payload["role"]).strip(),
            goal=str(payload["goal"]).strip(),
            backstory=str(payload.get("backstory", "")),
            verbose=bool(payload.get("verbose", True)),
            allow_delegation=bool(payload.get("allow_delegation", True)),
        )


@dataclass(slots=True)
class WorkerConfig:
    role: str
    goal: str
    backstory: str = ""
    tools: Optional[List[str]] = None
    verbose: bool = False

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "WorkerConfig":
        # ... validation logic ...
        return cls(
            role=str(payload["role"]).strip(),
            goal=str(payload["goal"]).strip(),
            backstory=str(payload.get("backstory", "")),
            tools=payload.get("tools") or None,
            verbose=bool(payload.get("verbose", False)),
        )


@dataclass(slots=True)
class TaskConfig:
    description: str
    agent_role: Optional[str] = None
    expected_output: str | None = None

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TaskConfig":
        # ... validation logic ...
        return cls(
            description=str(payload.get("description", "")).strip(),
            agent_role=str(payload.get("agent", "") or None) or None,
            expected_output=str(payload.get("expected_output")) if payload.get("expected_output") else None,
        )


def _get_crewai_components():
    from crewai import Agent, Crew, Process, Task

    return Agent, Task, Crew, Process


@activity.defn(name="crewai-delegation")
async def run_crewai_delegation(payload: Dict[str, Any]) -> Dict[str, Any]:
    manager = payload.get("manager")
    workers = payload.get("workers")
    tasks = payload.get("tasks")
    tenant = payload.get("tenant", "default")
    metadata = payload.get("metadata")
    process_type = str(payload.get("process_type", "sequential"))

    # ... validation and logging omitted for brevity ...

    manager_config = ManagerConfig.from_dict(manager)
    worker_configs = [WorkerConfig.from_dict(cfg) for cfg in workers]
    task_configs = [TaskConfig.from_dict(cfg) for cfg in tasks]

    Agent, Task, Crew, Process = _get_crewai_components()

    manager_agent = Agent(
        role=manager_config.role,
        goal=manager_config.goal,
        backstory=manager_config.backstory,
        verbose=manager_config.verbose,
        allow_delegation=manager_config.allow_delegation,
    )

    worker_agents = {}
    agents = [manager_agent]
    for config in worker_configs:
        agent = Agent(
            role=config.role,
            goal=config.goal,
            backstory=config.backstory,
            tools=config.tools,
            verbose=config.verbose,
        )
        worker_agents[config.role] = agent
        agents.append(agent)

    crew_tasks = []
    for task_config in task_configs:
        assigned_agent = worker_agents.get(task_config.agent_role or "") or manager_agent
        crew_tasks.append(
            Task(
                description=task_config.description,
                agent=assigned_agent,
                expected_output=task_config.expected_output,
            )
        )

    process = (Process.hierarchical if process_type == "hierarchical" else Process.sequential)

    crew = Crew(agents=agents, tasks=crew_tasks, process=process, verbose=False)
    result = crew.kickoff()

    return {
        "framework": "crewai",
        "pattern": "task_delegation",
        "tenant": tenant,
        "metadata": metadata or {},
        "manager": asdict(manager_config),
        "workers": [asdict(cfg) for cfg in worker_configs],
        "tasks": [asdict(cfg) for cfg in task_configs],
        "tasks_completed": len(crew_tasks),
        "result": str(result) if result is not None else None,
        "process_type": process_type,
    }
```

### **Pattern 3: LangGraph Integration (State Machine Routing)** *(Implemented)*

```python
# File: services/orchestrator/app/integrations/langgraph_adapter.py

"""LangGraph integration for configurable state-machine style routing."""

import importlib
import inspect
from typing import Any, Awaitable, Callable, Dict

from temporalio import activity


def _get_langgraph_components():
    from langgraph.graph import END, StateGraph

    return StateGraph, END


def _resolve_callable(path: str) -> Callable[[Dict[str, Any]], Any]:
    module_path, _, attr = path.rpartition(".")
    if not module_path or not attr:
        raise ValueError(f"callable path '{path}' is invalid; expected 'module.function'")

    module = importlib.import_module(module_path)
    return getattr(module, attr)


def _wrap_handler(name: str, handler: Callable[[Dict[str, Any]], Any]) -> Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]] | Dict[str, Any]]:
    async def _async_wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
        history = state.setdefault("history", [])
        history.append({"node": name})
        result = handler(state)
        if inspect.isawaitable(result):
            result = await result  # type: ignore[assignment]
        return result or state

    def _sync_wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
        history = state.setdefault("history", [])
        history.append({"node": name})
        result = handler(state)
        return result or state

    if inspect.iscoroutinefunction(handler):
        return _async_wrapper
    return _sync_wrapper


def _wrap_condition(handler: Callable[[Dict[str, Any]], str]) -> Callable[[Dict[str, Any]], str]:
    def _condition(state: Dict[str, Any]) -> str:
        result = handler(state)
        if inspect.isawaitable(result):
            raise ValueError("asynchronous condition callables are not supported")
        return str(result)

    return _condition


@activity.defn(name="langgraph-routing")
async def run_langgraph_routing(payload: Dict[str, Any]) -> Dict[str, Any]:
    graph = payload.get("graph")
    state = payload.get("state")
    input_data = payload.get("input_data")
    tenant = payload.get("tenant", "default")
    metadata = payload.get("metadata")

    logger = activity.logger
    if graph is None:
        raise ValueError("graph configuration is required")

    nodes = graph.get("nodes") or []
    if not nodes:
        raise ValueError("graph must define at least one node")

    StateGraph, END = _get_langgraph_components()
    workflow = StateGraph(dict)

    for node in nodes:
        name = str(node.get("name", "")).strip()
        handler_path = node.get("handler")
        handler = _resolve_callable(str(handler_path))
        workflow.add_node(name, _wrap_handler(name, handler))

    edges = graph.get("edges") or []
    for edge in edges:
        source = str(edge.get("from", "")).strip()
        if "condition" in edge:
            condition_path = str(edge["condition"])
            routes = edge.get("routes") or {}
            default_target = routes.get("default")
            condition_callable = _resolve_callable(condition_path)
            mapping: Dict[str, Any] = {}
            for key, value in routes.items():
                if key == "default":
                    continue
                mapping[key] = END if value == "END" else value
            mapping["__default__"] = END if default_target in {None, "END"} else default_target
            workflow.add_conditional_edges(
                source,
                _wrap_condition(condition_callable),
                mapping,
            )
        else:
            target = str(edge.get("to", "")).strip()
            workflow.add_edge(source, target)

    start_node = str(graph.get("start")) if graph.get("start") else nodes[0]["name"]
    workflow.set_entry_point(start_node)

    compiled = workflow.compile()

    execution_state: Dict[str, Any] = dict(state or {})
    execution_state.setdefault("history", [])
    if input_data is not None:
        execution_state["input"] = input_data

    result_state = await compiled.ainvoke(execution_state)

    return {
        "framework": "langgraph",
        "pattern": "state_machine_routing",
        "tenant": tenant,
        "metadata": metadata or {},
        "history": result_state.get("history", []),
        "state": {key: value for key, value in result_state.items() if key != "history"},
    }
```

### **Pattern 4: A2A Messaging (Agent-to-Agent)** *(Implemented)*

```python
# File: services/orchestrator/app/integrations/a2a_adapter.py

"""Temporal activity that delivers Agent-to-Agent messages using the A2A protocol."""

from temporalio import activity

from ..core.a2a_protocol import A2AProtocol, AgentRegistry

_registry = AgentRegistry()
_protocol = A2AProtocol(_registry)


@activity.defn(name="a2a-message")
async def run_a2a_message(payload: Dict[str, Any]) -> Dict:
    target_agent_id = str(payload.get("target_agent_id", "")).strip()
    message = str(payload.get("message", "")).strip()
    sender_id = str(payload.get("sender_id", "")).strip()
    metadata = payload.get("metadata") or {}

    if not target_agent_id:
        raise ValueError("'target_agent_id' is required for A2A messaging")
    if not message:
        raise ValueError("'message' is required for A2A messaging")
    if not sender_id:
        raise ValueError("'sender_id' is required for A2A messaging")

    result = await _protocol.send_message(
        target_agent_id=target_agent_id,
        message=message,
        sender_id=sender_id,
        metadata=metadata,
    )
    return result if isinstance(result, dict) else {"result": result}
```

```python
# File: services/orchestrator/app/core/a2a_protocol.py

@dataclass(slots=True)
class AgentCard:
    agent_id: str
    entrypoint: str
    capabilities: List[str] = field(default_factory=list)


class AgentRegistry:
    async def register(self, card: AgentCard) -> None:
        self._agents[card.agent_id] = card

    async def discover(self, capability: str) -> List[AgentCard]:
        return [card for card in self._agents.values() if capability in card.capabilities]


class A2AProtocol:
    async def send_message(...):
        target_card = await self.registry.get_agent(target_agent_id)
        if not target_card:
            raise AgentNotFoundError(target_agent_id)

        from temporalio import workflow

        result = await workflow.execute_child_workflow(
            target_card.entrypoint,
            A2AMessage(input=message, sender=sender_id, metadata=metadata or {}),
        )
        return result
```

---

## 🔄 THE MULTI-FRAMEWORK ROUTER

```python
# File: services/orchestrator/app/core/framework_router.py

"""Framework router that selects the optimal integration for each multi-agent pattern."""

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
```

---

## 🎯 THE UNIFIED API (Our Developer Experience)

```python
# File: services/orchestrator/app/workflows/unified_multi_agent.py

"""Unified multi-agent workflow orchestrating across multiple frameworks."""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict

from temporalio import workflow

from ..core.framework_router import FrameworkRouter, MultiAgentPattern
from ..integrations import (
    run_autogen_group_chat,
    run_crewai_delegation,
    run_langgraph_routing,
    run_a2a_message,
)
from ..workflows.session import PolicyEvaluationContext, evaluate_policy, emit_audit_event


@workflow.defn(name="unified-multi-agent-workflow")
class UnifiedMultiAgentWorkflow:
    """Temporal workflow that selects the optimal framework per request."""

    def __init__(self) -> None:
        self.router = FrameworkRouter()

    @workflow.run
    async def run(self, request: Dict[str, Any]) -> Dict[str, Any]:
        logger = workflow.logger
        workflow_id = workflow.info().workflow_id

        policy_ctx = PolicyEvaluationContext(
            session_id=request.get("session_id", workflow_id),
            tenant=request.get("tenant", "default"),
            user=request.get("user", "anonymous"),
            payload=request,
        )

        policy = await workflow.execute_activity(
            evaluate_policy,
            policy_ctx,
            start_to_close_timeout=timedelta(seconds=30),
        )

        if not policy.get("allowed", True):
            return {"status": "rejected", "reason": "policy_denied", "policy": policy}

        pattern = self.router.detect_pattern(request)
        activity_name = self.router.select_framework(pattern)

        logger.info(
            "Dispatching multi-agent request",
            pattern=pattern.value,
            activity=activity_name,
            workflow_id=workflow_id,
        )

        if pattern is MultiAgentPattern.GROUP_CHAT:
            result = await workflow.execute_activity(
                run_autogen_group_chat,
                request,
                start_to_close_timeout=timedelta(minutes=10),
            )
        elif pattern is MultiAgentPattern.TASK_DELEGATION:
            result = await workflow.execute_activity(
                run_crewai_delegation,
                request,
                start_to_close_timeout=timedelta(minutes=15),
            )
        elif pattern is MultiAgentPattern.A2A:
            result = await workflow.execute_activity(
                run_a2a_message,
                request,
                start_to_close_timeout=timedelta(minutes=5),
            )
        else:
            result = await workflow.execute_activity(
                run_langgraph_routing,
                request,
                start_to_close_timeout=timedelta(minutes=5),
            )

        await workflow.execute_activity(
            emit_audit_event,
            {
                "workflow_id": workflow_id,
                "pattern": pattern.value,
                "activity": activity_name,
                "status": "completed",
            },
            start_to_close_timeout=timedelta(seconds=10),
        )

        return {
            "status": "completed",
            "pattern": pattern.value,
            "activity": activity_name,
            "policy": policy,
            "result": result,
        }
```

---

## 📊 IMPLEMENTATION TIMELINE *(Archived Plan)*

> This timeline reflected the original three-week launch narrative. None of the observability, load testing, or production hardening tasks have shipped. Keep the section for historical context only.

### **Week 1: AutoGen + CrewAI Integration** *(Historical Plan)*

**Days 1-2: AutoGen**
- Install: `pip install pyautogen`
- Create: `autogen_adapter.py` (activity wrapper)
- Test: Group chat with 3 agents
- Integrate: Connect to Temporal workflow

**Days 3-4: CrewAI**
- Install: `pip install crewai`
- Create: `crewai_adapter.py` (activity wrapper)
- Test: Manager + 2 workers delegation
- Integrate: Connect to Temporal workflow

**Day 5: Testing**
- Integration tests for both adapters
- Performance benchmarks
- Documentation

**Deliverables Week 1 (Actual Status):**
- ✅ AutoGen and CrewAI adapter activities exist in `services/orchestrator/app/integrations/`.
- ✅ Temporal activities registered and callable from the unified workflow.
- ☐ Integration tests or replay harnesses cover these adapters.
- ☐ End-to-end CI job or benchmarking ensures regression detection.

---

### **Week 2: LangGraph + Router** *(Historical Plan)*

**Days 1-2: LangGraph**
- Install: `pip install langgraph`
- Create: `langgraph_adapter.py` (activity wrapper)
- Test: State machine with 3 nodes
- Integrate: Connect to Temporal workflow

**Days 3-4: Multi-Framework Router**
- Create: `framework_router.py` (pattern detection)
- Create: `unified_multi_agent.py` (unified workflow)
- Test: Auto-routing to correct framework
- Add: Policy enforcement layer

**Day 5: Production Ready**
- Error handling for all integrations
- Retry logic with Temporal
- Observability (metrics, traces)
- Documentation

**Deliverables Week 2 (Actual Status):**
- ✅ LangGraph adapter, router, and unified workflow live in the repository.
- ☐ Production error handling (retries, fallbacks, structured logging) implemented.
- ☐ Observability hooks (metrics/traces) wired into the workflow path.
- ☐ Multi-pattern integration tests or Temporal replay coverage available.

---

### **Week 3: A2A Protocol + Production** *(Historical Plan)*

**Days 1-2: A2A Protocol**
- Integrate: A2A Gateway (already using it)
- Create: Agent card registry
- Test: Agent discovery and messaging
- Document: Federation patterns

**Days 3-4: Production Deployment**
- Performance optimization
- Load testing (100+ concurrent workflows)
- Monitoring dashboards (Grafana)
- Alert configuration

**Day 5: Launch**
- Final integration tests
- Documentation review
- Team training
- Production deployment

**Deliverables Week 3 (Actual Status):**
- ⚠️ A2A adapter exists but operates on an in-memory registry without persistence or federation.
- ☐ No production deployment evidence, load testing data, or release notes.
- ☐ Observability stack (Langfuse/OpenLLMetry/Giskard) not present.
- ☐ Runbooks and operational documentation incomplete; only aspirational notes exist.

---

## 📋 DEPENDENCIES & INSTALLATION

### **requirements.txt**

```txt
# Core orchestration (already have)
temporalio>=1.4.0
fastapi>=0.104.0
pydantic>=2.0.0

# NEW: Framework integrations
pyautogen>=0.2.0          # AutoGen - Group chat
crewai>=0.1.0             # CrewAI - Task delegation  
langgraph>=0.0.25         # LangGraph - State machines
camel-ai>=0.1.0           # CAMEL - Role playing

# LLM providers (reuse existing)
openai>=1.0.0
anthropic>=0.5.0

# Utilities
httpx>=0.25.0
pydantic-settings>=2.0.0
```

### **Installation**

```bash
# Install framework integrations
pip install pyautogen crewai langgraph camel-ai

# Verify installation
python -c "import autogen; import crewai; from langgraph.graph import StateGraph; print('✅ All frameworks installed')"
```

---

## ✅ SUCCESS CRITERIA *(Reality)*

### **Week 1 Targets**
- ✅ AutoGen group chat and CrewAI delegation pathways execute inside Temporal.
- ☐ Automated tests, replay fixtures, or CI gates cover these frameworks.
- ☐ Documented performance benchmarks or load envelopes exist.
- ☐ Policy enforcement has regression tests verifying denial scenarios.

### **Week 2 Targets**
- ✅ LangGraph routing and FrameworkRouter unify pattern selection in-code.
- ☐ Router accuracy validated via automated scenarios (currently anecdotal only).
- ☐ Unified API returns structured telemetry or metrics for ops use.
- ☐ Production-grade error handling (fallbacks, retries, circuit breaking) implemented.

### **Week 3 Targets**
- ⚠️ A2A adapter provides message dispatch, but discovery/persistence remain prototypes.
- ☐ Throughput and concurrency validated at 100+ simultaneous workflows.
- ☐ Observability stack (Langfuse/OpenLLMetry/Giskard) deployed and integrated.
- ☐ Production deployment, runbooks, and alerting baselines documented.

---

## 🎯 OUR UNIQUE VALUE SUMMARY

| Layer | What We Build | Value |
|-------|---------------|-------|
| **Temporal Orchestration** | Fault-tolerant workflow execution | Production reliability |
| **Policy Engine** | Security, compliance, governance | Enterprise-grade |
| **Smart Router** | Automatic framework selection | Developer experience |
| **Unified API** | Single interface for all patterns | Simplicity |
| **Adapter Layer** | Seamless framework integration | Flexibility |
| **Observability** | Full visibility into all patterns | Production ops |

**What We DON'T Build:** Multi-agent patterns (AutoGen, CrewAI, LangGraph already have them)

**Leverage:** We build 2,500 lines, get 145,000+ lines of battle-tested code for FREE

**Time to Production:** 3 weeks (vs. 40+ weeks if building from scratch)

---

**Status**: ⚠️ Partial — core adapters and router implemented, but testing, observability, and production hardening are outstanding.  
**Next**: Focus on automated tests, dependency packaging, and observability instrumentation before expanding into new patterns.  
**Confidence**: Medium — functionality exists, but reliability and operational readiness remain unproven.
