"""CrewAI integration for hierarchical and sequential task delegation."""

from __future__ import annotations

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
        try:
            role = str(payload["role"]).strip()
            goal = str(payload["goal"]).strip()
        except KeyError as exc:  # pragma: no cover - validated in tests
            raise ValueError(f"manager config missing required field: {exc.args[0]}") from exc

        if not role:
            raise ValueError("manager role cannot be empty")
        if not goal:
            raise ValueError("manager goal cannot be empty")

        return cls(
            role=role,
            goal=goal,
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
        try:
            role = str(payload["role"]).strip()
            goal = str(payload["goal"]).strip()
        except KeyError as exc:  # pragma: no cover
            raise ValueError(f"worker config missing required field: {exc.args[0]}") from exc

        if not role:
            raise ValueError("worker role cannot be empty")
        if not goal:
            raise ValueError("worker goal cannot be empty")

        tools = payload.get("tools") or None
        if tools is not None and not isinstance(tools, list):  # pragma: no cover - defensive
            raise ValueError("tools must be a list when provided")

        return cls(
            role=role,
            goal=goal,
            backstory=str(payload.get("backstory", "")),
            tools=tools,
            verbose=bool(payload.get("verbose", False)),
        )


@dataclass(slots=True)
class TaskConfig:
    description: str
    agent_role: Optional[str] = None
    expected_output: str | None = None

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TaskConfig":
        description = str(payload.get("description", "")).strip()
        if not description:
            raise ValueError("task description cannot be empty")

        agent_role = payload.get("agent")
        if agent_role is not None:
            agent_role = str(agent_role).strip() or None

        expected_output = payload.get("expected_output")
        if expected_output is not None:
            expected_output = str(expected_output)

        return cls(description=description, agent_role=agent_role, expected_output=expected_output)


def _get_crewai_components():
    try:  # pragma: no cover - exercised in runtime environment
        from crewai import Agent, Task, Crew, Process
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "CrewAI is not installed. Add `crewai` to service dependencies before scheduling "
            "the `crewai-delegation` activity."
        ) from exc

    return Agent, Task, Crew, Process


def _select_process(process_type: str, process_cls: Any) -> Any:
    normalized = (process_type or "sequential").strip().lower()
    if normalized == "hierarchical":
        return getattr(process_cls, "hierarchical", getattr(process_cls, "HIERARCHICAL", process_cls))
    return getattr(process_cls, "sequential", getattr(process_cls, "SEQUENTIAL", process_cls))



@activity.defn(name="crewai-delegation")
async def run_crewai_delegation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a CrewAI delegation workflow under Temporal orchestration."""

    manager = payload.get("manager")
    workers = payload.get("workers")
    tasks = payload.get("tasks")
    tenant = payload.get("tenant", "default")
    metadata = payload.get("metadata")
    process_type = str(payload.get("process_type", "sequential"))

    logger = activity.logger
    if manager is None:
        raise ValueError("manager configuration is required")
    if workers is None:
        raise ValueError("worker configurations are required")
    if tasks is None:
        raise ValueError("task configurations are required")
    logger.info(
        "Starting CrewAI delegation",
        extra={
            "tenant": tenant,
            "worker_count": len(workers),
            "task_count": len(tasks),
            "process_type": process_type,
        },
    )

    if not tasks:
        raise ValueError("at least one task must be provided")

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

    process = _select_process(process_type, Process)

    try:
        crew = Crew(agents=agents, tasks=crew_tasks, process=process, verbose=False)
        result = crew.kickoff()
    except Exception as exc:  # pragma: no cover - CrewAI raised error
        logger.exception("CrewAI delegation failed")
        raise RuntimeError(f"crewai delegation failed: {exc}") from exc

    logger.info(
        "CrewAI delegation completed",
        extra={
            "tenant": tenant,
            "tasks_completed": len(crew_tasks),
            "workers": list(worker_agents.keys()),
        },
    )

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
