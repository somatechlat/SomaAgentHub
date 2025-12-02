"""
Unified Orchestrator - Central Brain of the MAO Engine.

Integrates all patterns (Saga, Circuit Breaker) and registries (Workflow, Activity)
into a single, cohesive orchestration engine. Provides the main entry point for
all workflow execution with automatic resilience and consistency guarantees.

TRUTH: This orchestrator is the single source of truth for all workflow execution.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
from typing import Any

from temporalio import workflow

from .patterns.saga import Saga
from .patterns.circuit_breaker import CircuitBreakerOpenError
from .registry.workflow_registry import get_workflow_registry, WorkflowRegistry
from .registry.activity_registry import get_activity_registry, ActivityRegistry


class UnifiedOrchestrator:
    """
    Unified orchestrator that integrates all patterns and registries.

    This is the central brain of the MAO engine, combining:
        - Saga pattern for distributed transactions
        - Circuit breaker pattern for fault tolerance
        - Workflow registry for discovery and versioning
        - Activity registry for service management
        - Automatic retry and compensation logic

        Features:
            - Automatic circuit breaker protection for all external calls
            - Saga pattern for ensuring data consistency
            - Workflow and activity discovery
            - Version management and deprecation
            - Comprehensive logging and monitoring
            - Graceful degradation on failures

            Usage:
                orchestrator = UnifiedOrchestrator()

# Execute workflow with automatic protection
                result = await orchestrator.execute_workflow(
                "marketing_campaign",
                {"campaign_id": "123", "budget": 5000.0},
                )

# Execute activity with circuit breaker protection
                result = await orchestrator.execute_activity(
                "create_github_repo",
                {"name": "campaign-repo", "private": True},
                )

# Execute saga with automatic compensation
                saga = orchestrator.create_saga("campaign_setup")
                try:
                    repo = await saga.execute(create_github_repo, {"name": "repo"})
                    channel = await saga.execute(create_slack_channel, {"name": "channel"})
                    except Exception:
                        await saga.compensate()
                        raise

                        Real-World Benefits:
                            - Single entry point for all orchestration
                            - Automatic resilience and consistency
                            - Comprehensive monitoring and debugging
                            - Simplified development with proven patterns
                            """

    def __init__(
    self,
    workflow_registry: WorkflowRegistry | None = None,
    activity_registry: ActivityRegistry | None = None,
    ):
    """
    Initialize unified orchestrator.

    Args:
        workflow_registry: Custom workflow registry (uses global if None)
        activity_registry: Custom activity registry (uses global if None)
        """
        self.workflow_registry = workflow_registry or get_workflow_registry()
        self.activity_registry = activity_registry or get_activity_registry()

        workflow.logger.info(
        "[UnifiedOrchestrator] Initialized",
        extra={
        "workflows_count": len(self.workflow_registry._workflows),
        "activities_count": len(self.activity_registry._activities),
        "circuit_breakers_count": len(self.activity_registry._circuit_breakers),
        },
        )

    async def execute_workflow(
                                    self,
                                    workflow_name: str,
                                    input_data: dict[str, Any],
                                    workflow_version: str | None = None,
                                    workflow_id: str | None = None,
                                    task_queue: str = "mao-engine-task-queue",
                                    execution_timeout: timedelta = timedelta(hours=1),
                                    ) -> Any:
                                        """
                                        Execute a workflow with automatic protection and monitoring.

                                        Args:
                                            workflow_name: Name of the workflow to execute
                                            input_data: Input data for the workflow
                                            workflow_version: Specific version (if None, uses latest active)
                                            workflow_id: Custom workflow ID (if None, auto-generated)
                                            task_queue: Temporal task queue
                                            execution_timeout: Maximum execution time

                                            Returns:
                                                Workflow execution result

                                                Raises:
                                                    KeyError: If workflow not found
                                                    Exception: If workflow execution fails
                                                    """
# Get workflow definition
                                                    workflow_def = self.workflow_registry.get(workflow_name, workflow_version)

                                                    workflow.logger.info(
                                                    f"[UnifiedOrchestrator] Executing workflow: {workflow_name}",
                                                    extra={
                                                    "workflow_name": workflow_name,
                                                    "workflow_version": workflow_def.metadata.version,
                                                    "workflow_id": workflow_id,
                                                    "task_queue": task_queue,
                                                    "input_keys": list(input_data.keys()),
                                                    },
                                                    )

# Execute workflow with Temporal
                                                    result = await workflow.execute_child_workflow(
                                                    workflow_def.workflow_func,
                                                    input_data,
                                                    id=workflow_id,
                                                    task_queue=task_queue,
                                                    execution_timeout=execution_timeout,
                                                    retry_policy=workflow_def.metadata.retry_policy,
                                                    )

                                                    workflow.logger.info(
                                                    f"[UnifiedOrchestrator] Workflow completed: {workflow_name}",
                                                    extra={
                                                    "workflow_name": workflow_name,
                                                    "result_type": type(result).__name__,
                                                    },
                                                    )

                                                    return result

    async def execute_activity(
                                                    self,
                                                    activity_name: str,
                                                    input_data: dict[str, Any],
                                                    activity_version: str | None = None,
                                                    timeout: timedelta = timedelta(seconds=30),
                                                    retry_policy: dict[str, Any] | None = None,
                                                    ) -> Any:
                                                        """
                                                        Execute an activity with circuit breaker protection.

                                                        Args:
                                                            activity_name: Name of the activity to execute
                                                            input_data: Input data for the activity
                                                            activity_version: Specific version (if None, uses latest active)
                                                            timeout: Activity execution timeout
                                                            retry_policy: Custom retry policy

                                                            Returns:
                                                                Activity execution result

                                                                Raises:
                                                                    KeyError: If activity not found
                                                                    CircuitBreakerOpenError: If circuit breaker is open
                                                                    Exception: If activity execution fails
                                                                    """
# Get activity definition
                                                                    activity_def = self.activity_registry.get(activity_name, activity_version)

                                                                    workflow.logger.info(
                                                                    f"[UnifiedOrchestrator] Executing activity: {activity_name}",
                                                                    extra={
                                                                    "activity_name": activity_name,
                                                                    "activity_version": activity_def.metadata.version,
                                                                    "service": activity_def.metadata.service_name,
                                                                    "input_keys": list(input_data.keys()),
                                                                    },
                                                                    )

# Check if circuit breaker is available
                                                                    if activity_def.circuit_breaker:
                                                                        try:
# Execute with circuit breaker protection
                                                                            result = await activity_def.circuit_breaker.call(
                                                                            activity_def.activity_func,
                                                                            **input_data,
                                                                            )

                                                                            workflow.logger.info(
                                                                            f"[UnifiedOrchestrator] Activity completed (with CB): {activity_name}",
                                                                            extra={
                                                                            "activity_name": activity_name,
                                                                            "circuit_breaker_state": activity_def.circuit_breaker.state.value,
                                                                            },
                                                                            )

                                                                            return result

                                                                            except CircuitBreakerOpenError as e:
                                                                                workflow.logger.error(
                                                                                f"[UnifiedOrchestrator] Circuit breaker open for {activity_name}",
                                                                                extra={
                                                                                "activity_name": activity_name,
                                                                                "service": activity_def.metadata.service_name,
                                                                                "opened_at": e.opened_at.isoformat(),
                                                                                },
                                                                                )
                                                                                raise

                                                                                else:
# Execute without circuit breaker (fallback)
                                                                                    result = await workflow.execute_activity(
                                                                                    activity_def.activity_func,
                                                                                    input_data,
                                                                                    start_to_close_timeout=timeout,
                                                                                    retry_policy=retry_policy or activity_def.metadata.retry_policy,
                                                                                    )

                                                                                    workflow.logger.info(
                                                                                    f"[UnifiedOrchestrator] Activity completed (no CB): {activity_name}",
                                                                                    )

                                                                                    return result

    def create_saga(self, saga_id: str) -> Saga:
        """
        Create a new saga instance for distributed transactions.

        Args:
    saga_id: Unique identifier for this saga

    Returns:
        Saga instance configured with the orchestrator's activity registry
        """
        workflow.logger.info(f"[UnifiedOrchestrator] Creating saga: {saga_id}")

        return Saga(saga_id)

    async def execute_saga_workflow(
                                                                                                self,
                                                                                                workflow_name: str,
                                                                                                input_data: dict[str, Any],
                                                                                                workflow_version: str | None = None,
                                                                                                ) -> Any:
                                                                                                    """
                                                                                                    Execute a workflow with automatic saga pattern integration.

                                                                                                    This is a convenience method that automatically wraps workflow execution
                                                                                                    in a saga pattern for distributed transaction support.

                                                                                                    Args:
                                                                                                        workflow_name: Name of the workflow to execute
                                                                                                        input_data: Input data for the workflow
                                                                                                        workflow_version: Specific version (if None, uses latest active)

                                                                                                        Returns:
                                                                                                            Workflow execution result

                                                                                                            Raises:
                                                                                                                KeyError: If workflow not found
                                                                                                                Exception: If workflow execution fails (with automatic compensation)
                                                                                                                """
                                                                                                                saga_id = f"{workflow_name}_{workflow.id()}"
                                                                                                                saga = self.create_saga(saga_id)

                                                                                                                try:
                                                                                                                    workflow.logger.info(
                                                                                                                    f"[UnifiedOrchestrator] Executing saga workflow: {workflow_name}",
                                                                                                                    extra={"saga_id": saga_id, "workflow_name": workflow_name},
                                                                                                                    )

# Execute workflow with saga tracking
                                                                                                                    result = await self.execute_workflow(
                                                                                                                    workflow_name,
                                                                                                                    input_data,
                                                                                                                    workflow_version,
                                                                                                                    workflow_id=saga_id,
                                                                                                                    )

                                                                                                                    workflow.logger.info(
                                                                                                                    f"[UnifiedOrchestrator] Saga workflow completed: {workflow_name}",
                                                                                                                    extra={"saga_id": saga_id},
                                                                                                                    )

                                                                                                                    return result

                                                                                                                    except Exception as e:
                                                                                                                        workflow.logger.error(
                                                                                                                        f"[UnifiedOrchestrator] Saga workflow failed: {workflow_name}",
                                                                                                                        extra={"saga_id": saga_id, "error": str(e)},
                                                                                                                        )

# Automatic compensation
                                                                                                                        await saga.compensate(f"workflow_failure: {e}")

                                                                                                                        raise

    def get_workflow_info(self, workflow_name: str, version: str | None = None) -> dict[str, Any]:
        """
        Get information about a registered workflow.

        Args:
    workflow_name: Name of the workflow
    version: Specific version (if None, uses latest active)

    Returns:
        Dictionary with workflow information
        """
        workflow_def = self.workflow_registry.get(workflow_name, version)
        metadata = workflow_def.metadata

        return {
        "name": metadata.name,
        "version": metadata.version,
        "description": metadata.description,
        "owner": metadata.owner,
        "category": metadata.category,
        "tags": metadata.tags,
        "input_schema": metadata.input_schema,
        "output_schema": metadata.output_schema,
        "timeout_minutes": metadata.timeout_minutes,
        "status": metadata.status.value,
        "created_at": metadata.created_at.isoformat(),
        "updated_at": metadata.updated_at.isoformat(),
        "execution_stats": workflow_def.execution_stats,
        }

    def get_activity_info(self, activity_name: str, version: str | None = None) -> dict[str, Any]:
        """
        Get information about a registered activity.

        Args:
    activity_name: Name of the activity
    version: Specific version (if None, uses latest active)

    Returns:
        Dictionary with activity information
        """
        activity_def = self.activity_registry.get(activity_name, version)
        metadata = activity_def.metadata

        circuit_breaker_info = None
        if activity_def.circuit_breaker:
            circuit_breaker_info = activity_def.circuit_breaker.get_status()

            return {
            "name": metadata.name,
            "version": metadata.version,
            "description": metadata.description,
            "owner": metadata.owner,
            "category": metadata.category,
            "tags": metadata.tags,
            "service_name": metadata.service_name,
            "input_schema": metadata.input_schema,
            "output_schema": metadata.output_schema,
            "timeout_seconds": metadata.timeout_seconds,
            "status": metadata.status.value,
            "circuit_breaker": circuit_breaker_info,
            "created_at": metadata.created_at.isoformat(),
            "updated_at": metadata.updated_at.isoformat(),
            "execution_stats": activity_def.execution_stats,
            }

    def get_orchestrator_status(self) -> dict[str, Any]:
                                                                                                                                                        """
                                                                                                                                                        Get comprehensive orchestrator status and metrics.

                                                                                                                                                        Returns:
                                                                                                                                                            Dictionary with orchestrator metrics and status
                                                                                                                                                            """
                                                                                                                                                            workflow_stats = self.workflow_registry.get_statistics()
                                                                                                                                                            activity_stats = self.activity_registry.get_statistics()

# Get circuit breaker statuses
                                                                                                                                                            circuit_breakers = {}
                                                                                                                                                            for service_name, breaker in self.activity_registry.get_all_circuit_breakers().items():
                                                                                                                                                                circuit_breakers[service_name] = breaker.get_status()

                                                                                                                                                                return {
                                                                                                                                                                "workflows": workflow_stats,
                                                                                                                                                                "activities": activity_stats,
                                                                                                                                                                "circuit_breakers": circuit_breakers,
                                                                                                                                                                "orchestrator_info": {
                                                                                                                                                                "version": "1.0.0",
                                                                                                                                                                "started_at": workflow.now().isoformat(),
                                                                                                                                                                "total_registrations": (
                                                                                                                                                                workflow_stats["total_workflows"] + activity_stats["total_activities"]
                                                                                                                                                                ),
                                                                                                                                                                },
                                                                                                                                                                }

    def discover_workflows(
                                                                                                                                                                self,
                                                                                                                                                                query: str | None = None,
                                                                                                                                                                category: str | None = None,
                                                                                                                                                                owner: str | None = None,
                                                                                                                                                                status: str | None = None,
                                                                                                                                                                ) -> list[dict[str, Any]]:
                                                                                                                                                                    """
                                                                                                                                                                    Discover workflows with filtering capabilities.

                                                                                                                                                                    Args:
                                                                                                                                                                        query: Search query for name/description/tags
                                                                                                                                                                        category: Filter by category
                                                                                                                                                                        owner: Filter by owner
                                                                                                                                                                        status: Filter by status

                                                                                                                                                                        Returns:
                                                                                                                                                                            List of workflow information dictionaries
                                                                                                                                                                            """
                                                                                                                                                                            if query:
                                                                                                                                                                                workflows = self.workflow_registry.search(query)
                                                                                                                                                                                elif category:
                                                                                                                                                                                    workflows = self.workflow_registry.find_by_category(category)
                                                                                                                                                                                    elif owner:
                                                                                                                                                                                        workflows = self.workflow_registry.find_by_owner(owner)
                                                                                                                                                                                        else:
                                                                                                                                                                                            workflows = self.workflow_registry.list_all()

# Filter by status if specified
                                                                                                                                                                                            if status:
                                                                                                                                                                                                from .registry.workflow_registry import WorkflowStatus
                                                                                                                                                                                                status_enum = WorkflowStatus(status)
                                                                                                                                                                                                workflows = [w for w in workflows if w.metadata.status == status_enum]

                                                                                                                                                                                                return [self.get_workflow_info(w.metadata.name, w.metadata.version) for w in workflows]

    def discover_activities(
                                                                                                                                                                                                self,
                                                                                                                                                                                                query: str | None = None,
                                                                                                                                                                                                category: str | None = None,
                                                                                                                                                                                                owner: str | None = None,
                                                                                                                                                                                                service: str | None = None,
                                                                                                                                                                                                status: str | None = None,
                                                                                                                                                                                                ) -> list[dict[str, Any]]:
                                                                                                                                                                                                    """
                                                                                                                                                                                                    Discover activities with filtering capabilities.

                                                                                                                                                                                                    Args:
                                                                                                                                                                                                        query: Search query for name/description/tags
                                                                                                                                                                                                        category: Filter by category
                                                                                                                                                                                                        owner: Filter by owner
                                                                                                                                                                                                        service: Filter by service name
                                                                                                                                                                                                        status: Filter by status

                                                                                                                                                                                                        Returns:
                                                                                                                                                                                                            List of activity information dictionaries
                                                                                                                                                                                                            """
                                                                                                                                                                                                            if query:
                                                                                                                                                                                                                activities = self.activity_registry.search(query)
                                                                                                                                                                                                                elif category:
                                                                                                                                                                                                                    activities = self.activity_registry.find_by_category(category)
                                                                                                                                                                                                                    elif owner:
                                                                                                                                                                                                                        activities = self.activity_registry.find_by_owner(owner)
                                                                                                                                                                                                                        elif service:
                                                                                                                                                                                                                            activities = self.activity_registry.find_by_service(service)
                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                activities = self.activity_registry.list_all()

# Filter by status if specified
                                                                                                                                                                                                                                if status:
                                                                                                                                                                                                                                    from .registry.activity_registry import ActivityStatus
                                                                                                                                                                                                                                    status_enum = ActivityStatus(status)
                                                                                                                                                                                                                                    activities = [a for a in activities if a.metadata.status == status_enum]

                                                                                                                                                                                                                                    return [self.get_activity_info(a.metadata.name, a.metadata.version) for a in activities]

    def health_check(self) -> dict[str, Any]:
                                                                                                                                                                                                                                        """
                                                                                                                                                                                                                                        Perform health check of the orchestrator and all components.

                                                                                                                                                                                                                                        Returns:
                                                                                                                                                                                                                                            Dictionary with health status information
                                                                                                                                                                                                                                            """
                                                                                                                                                                                                                                            workflow_count = len(self.workflow_registry._workflows)
                                                                                                                                                                                                                                            activity_count = len(self.activity_registry._activities)
                                                                                                                                                                                                                                            circuit_breaker_count = len(self.activity_registry._circuit_breakers)

# Check circuit breaker health
                                                                                                                                                                                                                                            unhealthy_circuit_breakers = []
                                                                                                                                                                                                                                            for service_name, breaker in self.activity_registry.get_all_circuit_breakers().items():
                                                                                                                                                                                                                                                if breaker.state.value == "open":
                                                                                                                                                                                                                                                    unhealthy_circuit_breakers.append(service_name)

                                                                                                                                                                                                                                                    return {
                                                                                                                                                                                                                                                    "status": "healthy" if not unhealthy_circuit_breakers else "degraded",
                                                                                                                                                                                                                                                    "components": {
                                                                                                                                                                                                                                                    "workflow_registry": {"status": "healthy", "workflows": workflow_count},
                                                                                                                                                                                                                                                    "activity_registry": {"status": "healthy", "activities": activity_count},
                                                                                                                                                                                                                                                    "circuit_breakers": {
                                                                                                                                                                                                                                                    "status": "healthy" if not unhealthy_circuit_breakers else "degraded",
                                                                                                                                                                                                                                                    "total": circuit_breaker_count,
                                                                                                                                                                                                                                                    "unhealthy": unhealthy_circuit_breakers,
                                                                                                                                                                                                                                                    },
                                                                                                                                                                                                                                                    },
                                                                                                                                                                                                                                                    "timestamp": workflow.now().isoformat(),
                                                                                                                                                                                                                                                    }


# Global unified orchestrator instance
                                                                                                                                                                                                                                                    _unified_orchestrator = UnifiedOrchestrator()


    def get_unified_orchestrator() -> UnifiedOrchestrator:
        """Get the global unified orchestrator instance."""
        return _unified_orchestrator