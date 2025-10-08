from __future__ import annotations

import pytest

from services.orchestrator.app.core.framework_router import FrameworkRouter, MultiAgentPattern


def test_detect_pattern_explicit() -> None:
    router = FrameworkRouter()
    assert router.detect_pattern({"pattern": "group_chat"}) == MultiAgentPattern.GROUP_CHAT

    with pytest.raises(ValueError):
        router.detect_pattern({"pattern": "unknown"})


def test_detect_pattern_graph_routes_to_langgraph() -> None:
    router = FrameworkRouter()
    pattern = router.detect_pattern({"graph": {"nodes": []}})
    assert pattern == MultiAgentPattern.STATE_MACHINE_ROUTING


def test_detect_pattern_manager_and_workers() -> None:
    router = FrameworkRouter()
    pattern = router.detect_pattern(
        {
            "manager": {"role": "Lead"},
            "workers": [{"role": "Engineer"}],
            "tasks": [{"description": "Build"}],
        }
    )
    assert pattern == MultiAgentPattern.TASK_DELEGATION


def test_detect_pattern_defaults_to_group_chat() -> None:
    router = FrameworkRouter()
    pattern = router.detect_pattern({"agents": [{}, {}, {}]})
    assert pattern == MultiAgentPattern.GROUP_CHAT


def test_select_framework() -> None:
    router = FrameworkRouter()
    assert router.select_framework(MultiAgentPattern.GROUP_CHAT) == "autogen-group-chat"
    assert router.select_framework(MultiAgentPattern.TASK_DELEGATION) == "crewai-delegation"
    assert router.select_framework(MultiAgentPattern.STATE_MACHINE_ROUTING) == "langgraph-routing"


def test_route_end_to_end() -> None:
    router = FrameworkRouter()
    payload = {
        "manager": {"role": "Lead"},
        "workers": [{"role": "Engineer"}],
        "tasks": [{"description": "Build"}],
    }
    assert router.route(payload) == "crewai-delegation"
