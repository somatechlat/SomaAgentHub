"""LangGraph integration for configurable state-machine style routing."""

from __future__ import annotations

import importlib
import inspect
from typing import Any, Awaitable, Callable, Dict

from temporalio import activity

GraphCallable = Callable[[Dict[str, Any]], Dict[str, Any] | Awaitable[Dict[str, Any] | None] | None]
ConditionCallable = Callable[[Dict[str, Any]], str | Any]


def _get_langgraph_components():
    try:  # pragma: no cover - exercised in runtime environment
        from langgraph.graph import END, StateGraph
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "LangGraph is not installed. Add `langgraph` to service dependencies before scheduling "
            "the `langgraph-routing` activity."
        ) from exc

    return StateGraph, END


def _resolve_callable(path: str) -> GraphCallable:
    module_path, _, attr = path.rpartition(".")
    if not module_path or not attr:
        raise ValueError(f"callable path '{path}' is invalid; expected 'module.function'")

    module = importlib.import_module(module_path)
    try:
        return getattr(module, attr)
    except AttributeError as exc:  # pragma: no cover - defensive
        raise ValueError(f"callable '{attr}' not found in module '{module_path}'") from exc


def _wrap_handler(name: str, handler: GraphCallable) -> GraphCallable:
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


def _wrap_condition(handler: ConditionCallable) -> Callable[[Dict[str, Any]], str]:
    def _condition(state: Dict[str, Any]) -> str:
        result = handler(state)
        if inspect.isawaitable(result):  # pragma: no cover - defensive
            raise ValueError("asynchronous condition callables are not supported")
        return str(result)

    return _condition



@activity.defn(name="langgraph-routing")
async def run_langgraph_routing(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a LangGraph state machine using the provided configuration."""

    graph = payload.get("graph")
    state = payload.get("state")
    input_data = payload.get("input_data")
    tenant = payload.get("tenant", "default")
    metadata = payload.get("metadata")

    logger = activity.logger
    if graph is None:
        raise ValueError("graph configuration is required")
    logger.info(
        "Starting LangGraph routing",
        extra={
            "tenant": tenant,
            "has_input": input_data is not None,
            "node_count": len(graph.get("nodes", [])),
        },
    )

    nodes = graph.get("nodes") or []
    if not nodes:
        raise ValueError("graph must define at least one node")

    StateGraph, END = _get_langgraph_components()
    workflow = StateGraph(dict)

    handlers: Dict[str, GraphCallable] = {}
    for node in nodes:
        name = str(node.get("name", "")).strip()
        if not name:
            raise ValueError("each node must include a non-empty 'name'")
        handler_path = node.get("handler")
        if not handler_path:
            raise ValueError(f"node '{name}' must provide a 'handler' callable path")
        handler = _resolve_callable(str(handler_path))
        workflow.add_node(name, _wrap_handler(name, handler))
        handlers[name] = handler

    edges = graph.get("edges") or []
    for edge in edges:
        source = str(edge.get("from", "")).strip()
        if not source:
            raise ValueError("edge is missing 'from'")
        if "condition" in edge:
            condition_path = str(edge["condition"])
            routes: Dict[str, str] = edge.get("routes") or {}
            default_target = routes.get("default")
            condition_callable = _resolve_callable(condition_path)
            mapping: Dict[str, Any] = {}
            for key, value in routes.items():
                if key == "default":
                    continue
                mapping[key] = END if value == "END" else value
            if default_target is None or default_target == "END":
                mapping["__default__"] = END
            else:
                mapping["__default__"] = END if default_target == "END" else default_target
            workflow.add_conditional_edges(
                source,
                _wrap_condition(condition_callable),
                mapping,
            )
        else:
            target = str(edge.get("to", "")).strip()
            if not target:
                raise ValueError(f"edge from '{source}' must include 'to'")
            workflow.add_edge(source, target)

    start_node = str(graph.get("start")) if graph.get("start") else nodes[0]["name"]
    workflow.set_entry_point(start_node)

    compiled = workflow.compile()

    execution_state: Dict[str, Any] = dict(state or {})
    execution_state.setdefault("history", [])
    if input_data is not None:
        execution_state["input"] = input_data

    result_state = await compiled.ainvoke(execution_state)

    logger.info(
        "LangGraph routing completed",
        extra={
            "tenant": tenant,
            "final_node": result_state.get("history", [{}])[-1].get("node") if result_state.get("history") else None,
        },
    )

    return {
        "framework": "langgraph",
        "pattern": "state_machine_routing",
        "tenant": tenant,
        "metadata": metadata or {},
        "history": result_state.get("history", []),
        "state": {key: value for key, value in result_state.items() if key != "history"},
    }
