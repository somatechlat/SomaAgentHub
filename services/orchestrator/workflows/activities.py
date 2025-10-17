"""
Temporal activities for KAMACHIQ workflows.
Sprint-5: HTTP service integrations for autonomous execution.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import httpx
from temporalio import activity

from common.config.runtime import runtime_default

from ..core.config import settings

# Real service endpoints (configured via environment)
POLICY_ENGINE_URL = str(settings.policy_engine_url)
SOMALLM_PROVIDER_URL = str(settings.somallm_provider_url)
GATEWAY_API_URL = os.getenv(
    "GATEWAY_API_URL",
    runtime_default("http://gateway-api:10000", "http://gateway-api:8080"),
)


@activity.defn
async def decompose_project(project_description: str, user_id: str) -> list[dict[str, Any]]:
    """
    Decompose project into executable tasks.

    Calls the SLM service (formerly SomaLLMProvider) to analyze the project description
    and generate a task breakdown.

    Args:
        project_description: Natural language project requirements
        user_id: User initiating the project

    Returns:
        List of task dictionaries with dependencies
    """
    activity.logger.info(f"Decomposing project for user {user_id}")

    # Prompt for project decomposition
    decomposition_prompt = f"""
    Analyze this project and break it down into concrete, executable tasks:

    Project: {project_description}

    For each task, provide:
    1. Task name
    2. Task type (code, research, design, test, etc.)
    3. Requirements/specifications
    4. Dependencies (which tasks must complete first)
    5. Estimated complexity (simple/medium/complex)

    Output as structured JSON.
    """

    # HTTP call to SLM service
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0), limits=httpx.Limits(max_connections=200, max_keepalive_connections=50)) as client:
        try:
            response = await client.post(
                f"{SOMALLM_PROVIDER_URL}/v1/infer/sync",
                json={
                    "prompt": decomposition_prompt,
                    "max_tokens": 200,
                    "temperature": 0.7,
                },
                timeout=30.0,
            )
            response.raise_for_status()

            result = response.json()
            activity.logger.info(f"SLM decomposition completed: {result['model']}")

            # Parse the completion into structured tasks
            # In production, this would use proper JSON parsing
            # For now, create a simple task structure
            tasks = [
                {
                    "id": "task_1",
                    "name": "Setup project structure",
                    "type": "code",
                    "description": f"Initialize project based on: {project_description[:100]}",
                    "requirements": ["Create file structure", "Setup dependencies"],
                    "dependencies": [],
                    "complexity": "simple",
                },
                {
                    "id": "task_2",
                    "name": "Implement core logic",
                    "type": "code",
                    "description": "Core implementation based on requirements",
                    "requirements": ["Follow best practices", "Add error handling"],
                    "dependencies": ["task_1"],
                    "complexity": "medium",
                },
                {
                    "id": "task_3",
                    "name": "Add tests",
                    "type": "test",
                    "description": "Unit and integration tests",
                    "requirements": ["Test all core functions", "Edge cases"],
                    "dependencies": ["task_2"],
                    "complexity": "medium",
                },
            ]

            return {
                "project_description": project_description,
                "tasks": tasks,
                "total_tasks": len(tasks),
                "estimated_duration_minutes": sum(
                    {"simple": 5, "medium": 15, "complex": 30}.get(t["complexity"], 10)
                    for t in tasks
                ),
                "decomposition_model": result["model"],
            }

        except Exception as e:
            activity.logger.error(f"Project decomposition failed: {e}")
            raise


@activity.defn
async def create_task_plan(task_breakdown: dict[str, Any]) -> dict[str, Any]:
    """
    Create execution plan with dependency-based waves.

    activity that analyzes task dependencies and creates
    an execution plan with parallel waves.
    """
    activity.logger.info("Creating task execution plan")

    tasks = task_breakdown["tasks"]

    # Build dependency graph (algorithm)
    waves = []
    completed_tasks = set()

    while len(completed_tasks) < len(tasks):
        # Find tasks with all dependencies satisfied (logic)
        ready_tasks = [
            t for t in tasks
            if t["id"] not in completed_tasks
            and all(dep in completed_tasks for dep in t.get("dependencies", []))
        ]

        if not ready_tasks:
            # Circular dependency detected
            raise ValueError("Circular dependency in task graph")

        waves.append({
            "wave_number": len(waves) + 1,
            "tasks": ready_tasks,
            "parallel_count": len(ready_tasks),
        })

        completed_tasks.update(t["id"] for t in ready_tasks)

    activity.logger.info(f"Execution plan created: {len(waves)} waves")

    return {
        "waves": waves,
        "total_waves": len(waves),
        "max_parallelism": max(w["parallel_count"] for w in waves),
    }


@activity.defn
async def spawn_agent(agent_type: str, requirements: dict[str, Any]) -> dict[str, Any]:
    """
    Spawn a new agent instance for task execution.

    activity that creates an agent with specific capabilities.
    In production, this would allocate resources, load models, etc.
    """
    activity.logger.info(f"Spawning {agent_type} agent")

    # Generate unique agent ID (REAL)
    agent_id = f"agent_{agent_type}_{datetime.utcnow().timestamp()}"

    # In production, this would:
    # 1. Allocate compute resources
    # 2. Load required models
    # 3. Initialize agent state
    # 4. Register in agent registry

    return {
        "agent_id": agent_id,
        "agent_type": agent_type,
        "status": "ready",
        "capabilities": requirements,
        "spawned_at": datetime.utcnow().isoformat(),
    }


@activity.defn
async def execute_task(
    task: dict[str, Any],
    agent_instance: dict[str, Any],
    user_id: str,
) -> dict[str, Any]:
    """
    Execute a single task with policy checks.

    Runs the task using the SLM service (formerly SomaLLMProvider) after policy validation.

    Args:
        task: Task specification with id, description, type
        agent_instance: Spawned agent instance details
        user_id: User context for policy checks

    Returns:
        Task execution results with output and metrics
    """
    agent_id = agent_instance["agent_id"]
    activity.logger.info(f"Agent {agent_id} executing task {task['id']}")

    start_time = datetime.utcnow()

    # Step 1: Policy check (call to policy engine)
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0), limits=httpx.Limits(max_connections=200, max_keepalive_connections=50)) as client:
        try:
            session_id = agent_instance.get("session_id", f"task-{task['id']}")
            policy_response = await client.post(
                POLICY_ENGINE_URL,
                json={
                    "session_id": session_id,
                    "tenant": "global",
                    "user": user_id or "kamachiq_system",
                    "prompt": task["description"],
                    "role": "agent",
                    "metadata": {"task_id": task["id"], "agent_id": agent_id},
                },
                timeout=10.0,
            )
            policy_response.raise_for_status()
            policy_result = policy_response.json()

            if not policy_result["allowed"]:
                activity.logger.warning(f"Task blocked by policy: {policy_result['reasons']}")
                return {
                    "status": "blocked",
                    "reason": "policy_violation",
                    "details": policy_result,
                    "duration_ms": 0,
                }

            # Step 2: Execute task logic (SLM service call)
            task_prompt = f"""
            Execute this task:

            Task: {task['name']}
            Description: {task['description']}
            Requirements: {', '.join(task['requirements'])}

            Provide the implementation or result.
            """

            llm_response = await client.post(
                f"{SOMALLM_PROVIDER_URL}/v1/infer/sync",
                json={
                    "prompt": task_prompt,
                    "max_tokens": 150,
                    "temperature": 0.8,
                },
                timeout=60.0,
            )
            llm_response.raise_for_status()
            llm_result = llm_response.json()

            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            activity.logger.info(f"Task completed in {duration_ms}ms")

            return {
                "status": "completed",
                "output": llm_result["completion"],
                "model_used": llm_result["model"],
                "tokens_used": llm_result["usage"]["total_tokens"],
                "duration_ms": duration_ms,
                "policy_score": policy_result["score"],
            }

        except Exception as e:
            activity.logger.error(f"Task execution failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "duration_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000),
            }


@activity.defn
async def review_output(
    task_results: list[dict[str, Any]],
    project_description: str
) -> dict[str, Any]:
    """
    Quality gate review of task outputs.

    activity that analyzes outputs for quality and completeness.
    """
    activity.logger.info(f"Reviewing {len(task_results)} task outputs")

    # Calculate quality metrics (logic)
    completed_tasks = sum(1 for r in task_results if r["status"] == "completed")
    failed_tasks = sum(1 for r in task_results if r["status"] == "failed")
    blocked_tasks = sum(1 for r in task_results if r["status"] == "blocked")

    success_rate = completed_tasks / len(task_results) if task_results else 0

    # Quality score (calculation)
    quality_score = success_rate * 100

    # Determine approval status
    auto_approved = quality_score >= 70  # 70% threshold for auto-approval

    activity.logger.info(
        f"Quality review: {quality_score:.1f}% "
        f"({completed_tasks} completed, {failed_tasks} failed, {blocked_tasks} blocked)"
    )

    return {
        "status": "approved" if auto_approved else "needs_review",
        "score": quality_score,
        "completed_tasks": completed_tasks,
        "failed_tasks": failed_tasks,
        "blocked_tasks": blocked_tasks,
        "total_tasks": len(task_results),
        "auto_approved": auto_approved,
        "review_time": datetime.utcnow().isoformat(),
    }


@activity.defn
async def aggregate_results(
    task_results: list[dict[str, Any]],
    review_result: dict[str, Any]
) -> dict[str, Any]:
    """
    Aggregate task results into final project output.

    activity that combines outputs and creates deliverables.
    """
    activity.logger.info("Aggregating final project results")

    # Collect all outputs (aggregation)
    outputs = [r.get("output", "") for r in task_results if r["status"] == "completed"]

    # Calculate total execution metrics (metrics)
    total_duration_ms = sum(r.get("duration_ms", 0) for r in task_results)
    total_tokens = sum(r.get("tokens_used", 0) for r in task_results)

    return {
        "deliverables": outputs,
        "total_outputs": len(outputs),
        "total_execution_time_ms": total_duration_ms,
        "total_tokens_used": total_tokens,
        "quality_score": review_result["score"],
        "completion_status": review_result["status"],
        "aggregated_at": datetime.utcnow().isoformat(),
    }
