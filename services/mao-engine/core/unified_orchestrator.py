"""
Unified MAO Orchestrator Engine.

Central orchestration engine that combines all proven patterns:
- Saga pattern for distributed transactions
- Circuit breaker for resilience
- Workflow registry for consistency
- Activity registry for standardization
- Single entry point for all orchestration

TRUTH: Unified orchestrator eliminates fragmentation and provides enterprise-grade orchestration.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from temporalio import workflow
from temporalio.client import Client, WorkflowFailureError
from temporalio.worker import Worker
from temporalio.service import ConnectError

from services.common.config.base_settings import resolve_env

from .patterns.saga import Saga, SagaBuilder, CompensationPair
from .patterns.circuit_breaker import (
CircuitBreaker,
CircuitBreakerConfig,
get_circuit_breaker,
)
from .workflow_registry import (
WorkflowRegistry,
WorkflowType,
WorkflowDefinition,
WorkflowInstance,
WorkflowStatus,
workflow_registry,
)
from .activity_registry import (
ActivityRegistry,
ActivityType,
ActivityDefinition,
ActivityInstance,
ActivityStatus,
activity_registry,
)


class UnifiedMAOEngine:
"""
Unified MAO Orchestrator Engine.

TRUTH: This engine combines all proven patterns into a single, cohesive orchestration system:
- Saga: Distributed transactions with automatic compensation
- Circuit Breaker: Resilience against failures
- Workflow Registry: Consistent workflow management
- Activity Registry: Standardized activity execution
- Unified Configuration: Single source of truth

Architecture:

External Systems
    ↓ (Circuit Breaker)
MAO Engine (Unified Orchestrator)
    ↓ (Temporal)
Temporal Workers
    ↓ (Registry)
Workflow/Activity Definitions

Key Benefits:
- Single orchestrator eliminates fragmentation
- Consistent patterns across all workflows
- Automatic resilience and recovery
- Centralized monitoring and debugging
- Proven enterprise-grade patterns

Usage:
engine = UnifiedMAOEngine()

# Start the engine
await engine.start()

# Execute saga workflow
result = await engine.execute_saga(
    workflow_id="campaign-123",
    workflow_name="marketing_campaign",
    input_data={"campaign_id": "123", "budget": 10000}
)

# Monitor workflows
workflows = await engine.list_workflows()
"""

def __init__(self, temporal_client: Optional[Client] = None):
"""
Initialize unified MAO engine.

Args:
temporal_client: Optional Temporal client (creates default if None)
"""
self.temporal_client = temporal_client
self.workers: List[Worker] = []
self.is_running = False

# Initialize registries
self.workflow_registry = workflow_registry
self.activity_registry = activity_registry

# Configuration
self.temporal_namespace = resolve_env("TEMPORAL_NAMESPACE", "default")
self.temporal_host = resolve_env("TEMPORAL_HOST", "localhost")
self.temporal_port = int(resolve_env("TEMPORAL_PORT", "7233"))

async def start(self) -> None:
"""Start the MAO engine and all workers."""
if self.is_running:
return

# Create Temporal client if not provided
if not self.temporal_client:
try:
    self.temporal_client = await Client.connect(
        f"{self.temporal_host}:{self.temporal_port}",
        namespace=self.temporal_namespace,
    )
    print(f"Connected to Temporal at {self.temporal_host}:{self.temporal_port}")
except ConnectError as e:
    raise RuntimeError(f"Failed to connect to Temporal: {e}")

# Start workers for all registered workflows
await self._start_workers()

self.is_running = True
print("MAO Engine started successfully")

async def stop(self) -> None:
"""Stop the MAO engine and all workers."""
if not self.is_running:
return

# Stop all workers
for worker in self.workers:
await worker.shutdown()

self.workers.clear()
self.is_running = False
print("MAO Engine stopped")

async def _start_workers(self) -> None:
"""Start workers for all registered workflows."""
# Group workflows by task queue
task_queues: Dict[str, List[Type]] = {}

for name, definition in self.workflow_registry._workflow_definitions.items():
if definition.is_active:
    task_queue = self.workflow_registry.get_workflow_task_queue(name)
    if task_queue:
        task_queues.setdefault(task_queue, []).append(definition.workflow_class)

# Start one worker per task queue
for task_queue, workflow_classes in task_queues.items():
worker = Worker(
    self.temporal_client,
    task_queue=task_queue,
    workflows=workflow_classes,
    activities=self._get_all_activities(),
)
await worker.run()
self.workers.append(worker)
print(f"Started worker for task queue: {task_queue}")

def _get_all_activities(self) -> List[object]:
"""Get all registered activity functions."""
activities = []
for name, func in self.activity_registry._activity_functions.items():
activities.append(func)
return activities

async def execute_saga(
self,
workflow_id: str,
workflow_name: str,
input_data: Dict[str, Any],
timeout_seconds: Optional[int] = None,
) -> Dict[str, Any]:
"""
Execute a saga workflow.

Args:
workflow_id: Unique workflow identifier
workflow_name: Name of registered workflow
input_data: Input parameters for workflow
timeout_seconds: Optional timeout override

Returns:
Workflow execution result

Raises:
ValueError: If workflow not found or input invalid
WorkflowFailureError: If workflow fails
"""
# Get workflow definition
definition = self.workflow_registry.get_workflow_definition(workflow_name)
if not definition:
    raise ValueError(f"Workflow not found: {workflow_name}")

# Validate input
if not self.workflow_registry.validate_workflow_input(workflow_name, input_data):
    raise ValueError(f"Invalid input for workflow: {workflow_name}")

# Create workflow instance
instance = self.workflow_registry.create_workflow_instance(
    workflow_id=workflow_id,
    workflow_name=workflow_name,
    input_data=input_data,
)

# Update status to running
self.workflow_registry.update_workflow_instance(
    workflow_id, WorkflowStatus.RUNNING
)

try:
    # Get task queue
    task_queue = self.workflow_registry.get_workflow_task_queue(workflow_name)
    if not task_queue:
        raise ValueError(f"No task queue for workflow: {workflow_name}")

    # Execute workflow
    handle = await self.temporal_client.start_workflow(
        workflow_name,
        input_data,
        id=workflow_id,
        task_queue=task_queue,
        execution_timeout=timeout_seconds or definition.timeout_seconds,
        retry_policy=definition.retry_policy,
    )

    # Wait for result
    result = await handle.result()

    # Update instance with success
    self.workflow_registry.update_workflow_instance(
        workflow_id,
        WorkflowStatus.COMPLETED,
        output_data=result,
        end_time=datetime.utcnow().isoformat(),
    )

    return result

except Exception as e:
    # Update instance with failure
    self.workflow_registry.update_workflow_instance(
        workflow_id,
        WorkflowStatus.FAILED,
        error_message=str(e),
        end_time=datetime.utcnow().isoformat(),
    )
    raise

async def execute_activity(
self,
activity_id: str,
activity_name: str,
input_data: Dict[str, Any],
workflow_id: Optional[str] = None,
timeout_seconds: Optional[int] = None,
) -> Dict[str, Any]:
"""
Execute an activity with circuit breaker protection.

Args:
activity_id: Unique activity identifier
activity_name: Name of registered activity
input_data: Input parameters for activity
workflow_id: Associated workflow ID
timeout_seconds: Optional timeout override

Returns:
Activity execution result

Raises:
ValueError: If activity not found or input invalid
Exception: If activity fails
"""
# Get activity definition
definition = self.activity_registry.get_activity_definition(activity_name)
if not definition:
    raise ValueError(f"Activity not found: {activity_name}")

# Validate input
if not self.activity_registry.validate_activity_input(activity_name, input_data):
    raise ValueError(f"Invalid input for activity: {activity_name}")

# Create activity instance
instance = self.activity_registry.create_activity_instance(
    activity_id=activity_id,
    activity_name=activity_name,
    input_data=input_data,
    workflow_id=workflow_id,
)

# Get activity function
activity_func = self.activity_registry.get_activity_function(activity_name)
if not activity_func:
    raise ValueError(f"Activity function not found: {activity_name}")

# Get or create circuit breaker for this activity
circuit_breaker_name = f"activity-{activity_name}"
circuit_breaker = get_circuit_breaker(circuit_breaker_name)

# Update status to running
self.activity_registry.update_activity_instance(
    activity_id, ActivityStatus.RUNNING
)

try:
    # Execute activity with circuit breaker protection
    result = await circuit_breaker.call(
        activity_func,
        **input_data,
    )

    # Update instance with success
    self.activity_registry.update_activity_instance(
        activity_id,
        ActivityStatus.COMPLETED,
        output_data=result,
        end_time=datetime.utcnow().isoformat(),
    )

    return result

except Exception as e:
    # Update instance with failure
    self.activity_registry.update_activity_instance(
        activity_id,
        ActivityStatus.FAILED,
        error_message=str(e),
        end_time=datetime.utcnow().isoformat(),
    )
    raise

def create_saga_builder(self) -> SagaBuilder:
"""
Create a new saga builder.

Returns:
SagaBuilder instance for constructing sagas
"""
return SagaBuilder()

def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowInstance]:
"""
Get status of a workflow.

Args:
workflow_id: Workflow identifier

Returns:
Workflow instance or None if not found
"""
return self.workflow_registry.get_workflow_instance(workflow_id)

def get_activity_status(self, activity_id: str) -> Optional[ActivityInstance]:
"""
Get status of an activity.

Args:
activity_id: Activity identifier

Returns:
Activity instance or None if not found
"""
return self.activity_registry.get_activity_instance(activity_id)

def list_workflows(
self,
workflow_name: Optional[str] = None,
status: Optional[WorkflowStatus] = None,
) -> List[WorkflowInstance]:
"""
List workflow instances.

Args:
workflow_name: Filter by workflow name
status: Filter by status

Returns:
List of workflow instances
"""
return self.workflow_registry.get_workflow_instances(
    workflow_name=workflow_name,
    status=status,
)

def list_activities(
self,
activity_name: Optional[str] = None,
status: Optional[ActivityStatus] = None,
workflow_id: Optional[str] = None,
) -> List[ActivityInstance]:
"""
List activity instances.

Args:
activity_name: Filter by activity name
status: Filter by status
workflow_id: Filter by workflow ID

Returns:
List of activity instances
"""
return self.activity_registry.get_activity_instances(
    activity_name=activity_name,
    status=status,
    workflow_id=workflow_id,
)

def get_circuit_breaker_status(self, service_name: str) -> Dict[str, Any]:
"""
Get status of a circuit breaker.

Args:
service_name: Service/endpoint name

Returns:
Circuit breaker status dictionary
"""
circuit_breaker = get_circuit_breaker(service_name)
return circuit_breaker.get_status()

def get_engine_statistics(self) -> Dict[str, Any]:
"""
Get engine statistics.

Returns:
Dictionary with engine statistics
"""
return {
"workflow_registry": self.workflow_registry.get_statistics(),
"activity_registry": self.activity_registry.get_statistics(),
"temporal_client_connected": self.temporal_client is not None,
"workers_running": len(self.workers),
"is_running": self.is_running,
}


# Global engine instance
mao_engine = UnifiedMAOEngine()