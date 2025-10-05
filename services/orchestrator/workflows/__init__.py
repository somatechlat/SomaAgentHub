"""
Workflow module initialization.
Real Temporal workflows for KAMACHIQ - Sprint-5.
"""

from .kamachiq_workflow import KAMACHIQProjectWorkflow, AgentTaskWorkflow
from .activities import (
    decompose_project,
    create_task_plan,
    spawn_agent,
    execute_task,
    review_output,
    aggregate_results,
)

__all__ = [
    "KAMACHIQProjectWorkflow",
    "AgentTaskWorkflow",
    "decompose_project",
    "create_task_plan",
    "spawn_agent",
    "execute_task",
    "review_output",
    "aggregate_results",
]
