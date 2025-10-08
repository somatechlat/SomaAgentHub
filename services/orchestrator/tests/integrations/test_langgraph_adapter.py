from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest

from services.orchestrator.app.integrations import langgraph_adapter


class DummyLogger:
    def info(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - stub
        pass

    def exception(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - stub
        pass


END_SENTINEL = object()


class DummyCompiledGraph:
    def __init__(self, nodes: Dict[str, Any], edges: Dict[str, List[str]], conditionals: Dict[str, Any], start: str):
        self.nodes = nodes
        self.edges = edges
        self.conditionals = conditionals
        self.start = start

    async def ainvoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        current = self.start
        while current and current is not END_SENTINEL:
            handler = self.nodes[current]
            result = handler(state)
            if hasattr(result, "__await__"):  # pragma: no cover - defensive
                result = await result
            if current in self.conditionals:
                condition, mapping = self.conditionals[current]
                key = condition(state)
                target = mapping.get(key, mapping.get("__default__", END_SENTINEL))
            elif self.edges.get(current):
                target = self.edges[current][0]
            else:
                target = END_SENTINEL
            if target is END_SENTINEL:
                break
            current = target
        return state


class DummyStateGraph:
    def __init__(self, _state_type: Any):
        self.nodes: Dict[str, Any] = {}
        self.edges: Dict[str, List[str]] = {}
        self.conditionals: Dict[str, Any] = {}
        self.start: Optional[str] = None

    def add_node(self, name: str, handler: Any) -> None:
        self.nodes[name] = handler

    def add_edge(self, source: str, target: str) -> None:
        self.edges.setdefault(source, []).append(target)

    def add_conditional_edges(self, source: str, condition, mapping: Dict[str, Any]) -> None:
        mapping = {
            key: (END_SENTINEL if value == LangGraphFixtures.END else value)
            for key, value in mapping.items()
        }
        self.conditionals[source] = (condition, mapping)

    def set_entry_point(self, name: str) -> None:
        self.start = name

    def compile(self) -> DummyCompiledGraph:
        return DummyCompiledGraph(self.nodes, self.edges, self.conditionals, self.start or "")


class LangGraphFixtures:
    END = END_SENTINEL

    @staticmethod
    def install_handlers_module(module_name: str = "tests.langgraph_handlers") -> str:
        module = ModuleType(module_name)

        def classifier(state: Dict[str, Any]) -> Dict[str, Any]:
            state.setdefault("history", [])
            state["topic"] = state.get("input", "")
            return state

        def resolver(state: Dict[str, Any]) -> str:
            return "support" if "support" in state.get("input", "") else "__default__"

        def support_handler(state: Dict[str, Any]) -> Dict[str, Any]:
            state["handled_by"] = "support"
            return state

        module.classifier = classifier
        module.resolver = resolver
        module.support_handler = support_handler
        sys.modules[module_name] = module
        return module_name


@pytest.fixture(autouse=True)
def patch_langgraph(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        langgraph_adapter,
        "_get_langgraph_components",
        lambda: (DummyStateGraph, LangGraphFixtures.END),
    )
    monkeypatch.setattr(langgraph_adapter, "activity", SimpleNamespace(logger=DummyLogger()))


@pytest.mark.asyncio
async def test_langgraph_routing_basic() -> None:
    module_name = LangGraphFixtures.install_handlers_module()

    result = await langgraph_adapter.run_langgraph_routing(
        {
            "graph": {
                "nodes": [
                    {"name": "classifier", "handler": f"{module_name}.classifier"},
                    {"name": "support", "handler": f"{module_name}.support_handler"},
                ],
                "edges": [
                    {
                        "from": "classifier",
                        "condition": f"{module_name}.resolver",
                        "routes": {"support": "support", "default": "END"},
                    },
                ],
                "start": "classifier",
            },
            "state": {"input": "support ticket"},
            "tenant": "tenant-xyz",
        }
    )

    assert result["framework"] == "langgraph"
    assert result["pattern"] == "state_machine_routing"
    assert result["tenant"] == "tenant-xyz"
    assert any(step["node"] == "support" for step in result["history"])
    assert result["state"]["handled_by"] == "support"


@pytest.mark.asyncio
async def test_langgraph_routing_requires_nodes() -> None:
    with pytest.raises(ValueError):
        await langgraph_adapter.run_langgraph_routing({"graph": {}, "state": {}})


@pytest.mark.asyncio
async def test_langgraph_routing_edge_validation() -> None:
    module_name = LangGraphFixtures.install_handlers_module("tests.langgraph_handlers_alt")

    with pytest.raises(ValueError):
        await langgraph_adapter.run_langgraph_routing(
            {
                "graph": {
                    "nodes": [{"name": "classifier", "handler": f"{module_name}.classifier"}],
                    "edges": [{"from": "classifier"}],
                },
                "state": {"input": "hi"},
            }
        )
