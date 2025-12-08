"""
Temporal activities for KAMACHIQ workflows.
Sprint-5: HTTP service integrations for autonomous execution.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

import httpx
from temporalio import activity

from services.common.config.base_settings import resolve_env

from ..app.core.config import settings


def _ensure_endpoint(url: str, expected_path: str) -> str:
    """Ensure *url* includes *expected_path* at the end."""

    normalized = url.rstrip("/")
    suffix = expected_path if expected_path.startswith("/") else f"/{expected_path}"
    return normalized if normalized.endswith(suffix) else f"{normalized}{suffix}"


def _coerce_positive_int(value: Any, field_name: str) -> int:
    try:
        coerced = int(value)
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive branch
        raise ValueError(
            f"{field_name} must be a positive integer (got {value!r})"
        ) from exc
    if coerced < 1:
        raise ValueError(f"{field_name} must be >= 1 (got {coerced})")
    return coerced


def _coerce_non_negative_int(value: Any, field_name: str) -> int:
    try:
        coerced = int(value)
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive branch
        raise ValueError(
            f"{field_name} must be a non-negative integer (got {value!r})"
        ) from exc
    if coerced < 0:
        raise ValueError(f"{field_name} must be >= 0 (got {coerced})")
    return coerced


def _normalize_command(command: Any) -> list[str]:
    """Return a shell-safe command list from the payload override."""

    if isinstance(command, str):
        stripped = command.strip()
        if not stripped:
            raise ValueError("command override cannot be empty")
        return ["/bin/sh", "-c", stripped]

    if isinstance(command, Sequence) and not isinstance(command, (bytes, bytearray)):
        command_list = list(command)
        if not command_list:
            raise ValueError("command override cannot be empty")
        if not all(isinstance(item, str) for item in command_list):
            raise ValueError("command sequence must only contain strings")
        return command_list

    raise ValueError("command override must be a string or sequence of strings")


def _normalize_env(env_mapping: Mapping[Any, Any]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key, value in env_mapping.items():
        if not isinstance(key, str):
            raise ValueError("environment variable names must be strings")
        normalized[key] = str(value)
    return normalized


# Real service endpoints (configured via environment)
POLICY_ENGINE_URL = _ensure_endpoint(str(settings.policy_engine_url), "/v1/evaluate")
LLM_HUB_URL = str(settings.llm_hub_url)

# Resolve the gateway API URL using the canonical resolver. The default points to the
# standard development endpoint; runtime-specific overrides are handled elsewhere via
# the `runtime_default` helper when needed.
GATEWAY_API_URL = resolve_env("GATEWAY_API_URL", "http://gateway-api:10000")


@activity.defn
async def decompose_project(
    project_description: str, user_id: str
) -> list[dict[str, Any]]:
    """
    Decompose project into executable tasks.

    Calls the LLM Hub to analyze the project description
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

    # HTTP call to LLM Hub
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(10.0, connect=5.0),
        limits=httpx.Limits(max_connections=200, max_keepalive_connections=50),
    ) as client:
        try:
            response = await client.post(
                f"{LLM_HUB_URL}/v1/infer/sync",
                json={
                    "prompt": decomposition_prompt,
                    "max_tokens": 200,
                    "temperature": 0.7,
                },
                timeout=30.0,
            )
            response.raise_for_status()

            result = response.json()
            activity.logger.info(f"LLM decomposition completed: {result['model']}")

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
            t
            for t in tasks
            if t["id"] not in completed_tasks
            and all(dep in completed_tasks for dep in t.get("dependencies", []))
        ]

        if not ready_tasks:
            # Circular dependency detected
            raise ValueError("Circular dependency in task graph")

        waves.append(
            {
                "wave_number": len(waves) + 1,
                "tasks": ready_tasks,
                "parallel_count": len(ready_tasks),
            }
        )

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
    Spawn a new agent instance for task execution using Kubernetes-native agent management.

    This activity creates a real agent instance in the database and launches it on Kubernetes
    using the official Kubernetes Python client for both Jobs and Deployments.
    """
    from uuid import uuid4

    from ..agents import (
        create_agent_instance,
        launch_agent_instance,
        update_agent_status,
    )
    from ..app.models.agent_instance import AgentStatus

    activity.logger.info(f"Spawning {agent_type} agent")

    try:
        # Extract parameters from requirements
        tenant_id = uuid4()  # In production, get from workflow context
        user_id = uuid4()  # In production, get from workflow context
        capsule_id = requirements.get("capsule_id")
        k8s_namespace = requirements.get("k8s_namespace", "default")
        is_long_running = requirements.get("is_long_running", False)
        container_image = requirements.get("container_image", "somaagent01:latest")
        resource_requests = requirements.get("resource_requests")
        resource_limits = requirements.get("resource_limits")
        env_vars = requirements.get("env_vars")

        # Step 1: Create agent instance in database
        agent_instance = await create_agent_instance(
            agent_type=agent_type,
            capsule_id=capsule_id,
            tenant_id=tenant_id,
            user_id=user_id,
            k8s_namespace=k8s_namespace,
            metadata=requirements.get("metadata", {}),
        )

        # Step 2: Launch agent on Kubernetes
        k8s_resource_name = await launch_agent_instance(
            agent_instance_id=agent_instance.id,
            agent_type=agent_type,
            k8s_namespace=k8s_namespace,
            is_long_running=is_long_running,
            container_image=container_image,
            resource_requests=resource_requests,
            resource_limits=resource_limits,
            env_vars=env_vars,
        )

        # Step 3: Update agent status to running
        await update_agent_status(agent_instance.id, AgentStatus.RUNNING)

        activity.logger.info(
            f"Successfully spawned agent {agent_instance.id} as {k8s_resource_name}"
        )

        return {
            "agent_id": str(agent_instance.id),
            "agent_type": agent_type,
            "status": "running",
            "k8s_resource_name": k8s_resource_name,
            "k8s_namespace": k8s_namespace,
            "is_long_running": is_long_running,
            "capabilities": requirements,
            "spawned_at": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        activity.logger.error(f"Failed to spawn agent: {e}")
        raise


@activity.defn
async def execute_task(
    task: dict[str, Any],
    agent_instance: dict[str, Any],
    user_id: str,
) -> dict[str, Any]:
    """
    Execute a single task with policy checks.

    Runs the task using the LLM Hub after policy validation.

    Args:
        task: Task specification with id, description, type
        agent_instance: Spawned agent instance details
        user_id: User context for policy checks

    Returns:
        Task execution results with output and metrics
    """
    agent_id = agent_instance["agent_id"]
    activity.logger.info(f"Agent {agent_id} executing task {task['id']}")

    start_time = datetime.now(UTC)

    # Step 1: Policy check (call to policy engine)
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(10.0, connect=5.0),
        limits=httpx.Limits(max_connections=200, max_keepalive_connections=50),
    ) as client:
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
                activity.logger.warning(
                    f"Task blocked by policy: {policy_result['reasons']}"
                )
                return {
                    "status": "blocked",
                    "reason": "policy_violation",
                    "details": policy_result,
                    "duration_ms": 0,
                }

            # Step 2: Execute task logic (LLM Hub call)
            task_prompt = f"""
            Execute this task:

                Task: {task["name"]}
                Description: {task["description"]}
                Requirements: {", ".join(task["requirements"])}

                Provide the implementation or result.
            """

            llm_response = await client.post(
                f"{LLM_HUB_URL}/v1/infer/sync",
                json={
                    "prompt": task_prompt,
                    "max_tokens": 150,
                    "temperature": 0.8,
                },
                timeout=60.0,
            )
            llm_response.raise_for_status()
            llm_result = llm_response.json()

            duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

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
                "duration_ms": int(
                    (datetime.now(UTC) - start_time).total_seconds() * 1000
                ),
            }


@activity.defn
async def review_output(
    task_results: list[dict[str, Any]], project_description: str
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
        "review_time": datetime.now(UTC).isoformat(),
    }


@activity.defn
async def aggregate_results(
    task_results: list[dict[str, Any]], review_result: dict[str, Any]
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
        "aggregated_at": datetime.now(UTC).isoformat(),
    }
