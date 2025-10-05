"""
⚠️ WE DO NOT MOCK - Real Temporal workflow definitions for multi-agent orchestration.
"""

from datetime import timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activities (to be implemented)
with workflow.unsafe.imports_passed_through():
    from .activities import (
        create_workspace,
        provision_git_repo,
        execute_capsule,
        bundle_artifacts,
        notify_completion,
        cleanup_workspace,
    )


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionMode(str, Enum):
    """Capsule execution mode."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    DAG = "dag"  # Directed Acyclic Graph with dependencies


@dataclass
class TaskDefinition:
    """Definition of a single task in the project."""
    task_id: str
    capsule_id: str
    persona_id: str
    description: str
    dependencies: List[str]  # Task IDs that must complete before this task
    timeout_seconds: int = 3600
    retry_attempts: int = 3
    metadata: Dict[str, Any] = None


@dataclass
class ProjectConfig:
    """Configuration for the entire project workflow."""
    project_id: str
    project_name: str
    tasks: List[TaskDefinition]
    execution_mode: ExecutionMode = ExecutionMode.DAG
    workspace_config: Dict[str, Any] = None
    git_repo_url: Optional[str] = None
    artifact_storage: str = "s3://somagent-artifacts"
    notify_webhooks: List[str] = None
    max_parallel_tasks: int = 5


@dataclass
class TaskResult:
    """Result of a single task execution."""
    task_id: str
    status: TaskStatus
    output: Dict[str, Any]
    artifacts: List[str]
    execution_time_seconds: float
    error_message: Optional[str] = None


@workflow.defn
class ProjectWorkflow:
    """
    Main workflow for orchestrating multi-agent project execution.
    
    This workflow:
    1. Creates a workspace (VSCode container, Git repo)
    2. Executes tasks based on dependency graph
    3. Handles parallel/sequential execution
    4. Bundles artifacts
    5. Notifies on completion
    6. Cleans up resources
    """

    def __init__(self) -> None:
        self.task_results: Dict[str, TaskResult] = {}
        self.workspace_id: Optional[str] = None
        self.current_status = "initializing"

    @workflow.run
    async def run(self, config: ProjectConfig) -> Dict[str, Any]:
        """Execute the project workflow."""
        
        workflow.logger.info(
            f"Starting project workflow: {config.project_name} "
            f"with {len(config.tasks)} tasks"
        )
        
        try:
            # Step 1: Setup workspace
            self.current_status = "setting_up_workspace"
            self.workspace_id = await workflow.execute_activity(
                create_workspace,
                args=[config.workspace_config],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=10),
                    maximum_attempts=3,
                ),
            )
            
            workflow.logger.info(f"Workspace created: {self.workspace_id}")
            
            # Step 2: Provision Git repository if needed
            if config.git_repo_url:
                self.current_status = "provisioning_git_repo"
                await workflow.execute_activity(
                    provision_git_repo,
                    args=[self.workspace_id, config.git_repo_url],
                    start_to_close_timeout=timedelta(minutes=5),
                )
            
            # Step 3: Execute tasks based on execution mode
            self.current_status = "executing_tasks"
            if config.execution_mode == ExecutionMode.SEQUENTIAL:
                await self._execute_sequential(config)
            elif config.execution_mode == ExecutionMode.PARALLEL:
                await self._execute_parallel(config)
            else:  # DAG mode
                await self._execute_dag(config)
            
            # Step 4: Bundle artifacts
            self.current_status = "bundling_artifacts"
            artifact_urls = await workflow.execute_activity(
                bundle_artifacts,
                args=[
                    self.workspace_id,
                    config.artifact_storage,
                    list(self.task_results.values())
                ],
                start_to_close_timeout=timedelta(minutes=15),
            )
            
            # Step 5: Notify completion
            self.current_status = "notifying"
            if config.notify_webhooks:
                await workflow.execute_activity(
                    notify_completion,
                    args=[config.notify_webhooks, {
                        "project_id": config.project_id,
                        "project_name": config.project_name,
                        "status": "completed",
                        "task_results": self.task_results,
                        "artifacts": artifact_urls,
                    }],
                    start_to_close_timeout=timedelta(seconds=30),
                )
            
            self.current_status = "completed"
            
            return {
                "project_id": config.project_id,
                "status": "completed",
                "workspace_id": self.workspace_id,
                "task_results": self.task_results,
                "artifacts": artifact_urls,
                "total_tasks": len(config.tasks),
                "successful_tasks": sum(
                    1 for r in self.task_results.values()
                    if r.status == TaskStatus.COMPLETED
                ),
                "failed_tasks": sum(
                    1 for r in self.task_results.values()
                    if r.status == TaskStatus.FAILED
                ),
            }
            
        except Exception as e:
            workflow.logger.error(f"Project workflow failed: {e}")
            self.current_status = "failed"
            
            # Attempt cleanup even on failure
            if self.workspace_id:
                try:
                    await workflow.execute_activity(
                        cleanup_workspace,
                        args=[self.workspace_id],
                        start_to_close_timeout=timedelta(minutes=5),
                    )
                except Exception as cleanup_error:
                    workflow.logger.error(f"Cleanup failed: {cleanup_error}")
            
            raise
    
    async def _execute_sequential(self, config: ProjectConfig) -> None:
        """Execute tasks sequentially in order."""
        for task in config.tasks:
            result = await self._execute_task(task)
            self.task_results[task.task_id] = result
            
            if result.status == TaskStatus.FAILED:
                workflow.logger.error(
                    f"Task {task.task_id} failed, stopping sequential execution"
                )
                break
    
    async def _execute_parallel(self, config: ProjectConfig) -> None:
        """Execute all tasks in parallel (no dependency checking)."""
        # Execute in batches to respect max_parallel_tasks
        tasks = config.tasks[:]
        
        while tasks:
            batch = tasks[:config.max_parallel_tasks]
            tasks = tasks[config.max_parallel_tasks:]
            
            # Execute batch in parallel
            results = await workflow.asyncio.gather(*[
                self._execute_task(task) for task in batch
            ])
            
            for task, result in zip(batch, results):
                self.task_results[task.task_id] = result
    
    async def _execute_dag(self, config: ProjectConfig) -> None:
        """Execute tasks based on dependency graph (DAG)."""
        completed = set()
        remaining = {task.task_id: task for task in config.tasks}
        
        while remaining:
            # Find tasks whose dependencies are satisfied
            ready_tasks = [
                task for task in remaining.values()
                if all(dep in completed for dep in task.dependencies)
            ]
            
            if not ready_tasks:
                # No tasks ready - check for circular dependencies
                if remaining:
                    raise ValueError(
                        f"Circular dependency detected. Remaining tasks: "
                        f"{list(remaining.keys())}"
                    )
                break
            
            # Execute ready tasks in parallel (up to max_parallel_tasks)
            batch = ready_tasks[:config.max_parallel_tasks]
            
            results = await workflow.asyncio.gather(*[
                self._execute_task(task) for task in batch
            ])
            
            for task, result in zip(batch, results):
                self.task_results[task.task_id] = result
                completed.add(task.task_id)
                del remaining[task.task_id]
                
                # Stop execution if critical task fails
                if result.status == TaskStatus.FAILED and not task.metadata.get("optional", False):
                    workflow.logger.error(
                        f"Critical task {task.task_id} failed, stopping execution"
                    )
                    return
    
    async def _execute_task(self, task: TaskDefinition) -> TaskResult:
        """Execute a single task (capsule)."""
        workflow.logger.info(f"Executing task: {task.task_id}")
        
        try:
            result = await workflow.execute_activity(
                execute_capsule,
                args=[{
                    "workspace_id": self.workspace_id,
                    "task_id": task.task_id,
                    "capsule_id": task.capsule_id,
                    "persona_id": task.persona_id,
                    "description": task.description,
                    "metadata": task.metadata,
                }],
                start_to_close_timeout=timedelta(seconds=task.timeout_seconds),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=2),
                    maximum_interval=timedelta(seconds=30),
                    maximum_attempts=task.retry_attempts,
                ),
            )
            
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                output=result.get("output", {}),
                artifacts=result.get("artifacts", []),
                execution_time_seconds=result.get("execution_time", 0),
            )
            
        except Exception as e:
            workflow.logger.error(f"Task {task.task_id} failed: {e}")
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                output={},
                artifacts=[],
                execution_time_seconds=0,
                error_message=str(e),
            )
    
    @workflow.query
    def get_status(self) -> Dict[str, Any]:
        """Query current workflow status."""
        return {
            "current_status": self.current_status,
            "workspace_id": self.workspace_id,
            "completed_tasks": len(self.task_results),
            "task_results": self.task_results,
        }
    
    @workflow.signal
    async def cancel_workflow(self) -> None:
        """Signal to cancel the workflow."""
        workflow.logger.info("Workflow cancellation requested")
        self.current_status = "cancelling"
        
        # Mark all pending tasks as cancelled
        for task_id in self.task_results:
            if self.task_results[task_id].status == TaskStatus.RUNNING:
                self.task_results[task_id].status = TaskStatus.CANCELLED
