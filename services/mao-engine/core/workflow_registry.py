"""
Unified Workflow Registry for MAO Engine.

Central registry for all workflow types, definitions, and metadata.
Single source of truth for workflow orchestration.

TRUTH: Centralized registry eliminates workflow duplication and ensures consistency.
"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union

from temporalio import workflow
from temporalio.client import Client
from temporalio.worker import Worker

from services.common.config.base_settings import resolve_env


class WorkflowType(str, Enum):
"""Types of workflows supported by MAO engine."""

SAGA = "saga"  # Distributed transactions with compensation
SEQUENTIAL = "sequential"  # Step-by-step workflows
PARALLEL = "parallel"  # Concurrent execution workflows
CONDITIONAL = "conditional"  # Decision-based workflows
EVENT_DRIVEN = "event_driven"  # Event-triggered workflows
COMPOSITE = "composite"  # Nested workflows


class WorkflowStatus(str, Enum):
"""Workflow execution status."""

PENDING = "pending"
RUNNING = "running"
COMPLETED = "completed"
FAILED = "failed"
CANCELLED = "cancelled"
TIMED_OUT = "timed_out"
COMPENSATING = "compensating"


@dataclass
class WorkflowDefinition:
"""Definition of a workflow type."""

name: str
description: str
workflow_class: Type
workflow_type: WorkflowType
version: str = "1.0.0"
tags: List[str] = field(default_factory=list)
parameters_schema: Optional[Dict[str, Any]] = None
output_schema: Optional[Dict[str, Any]] = None
timeout_seconds: Optional[int] = None
retry_policy: Optional[Dict[str, Any]] = None
is_active: bool = True
created_at: Optional[str] = None
updated_at: Optional[str] = None


@dataclass
class WorkflowInstance:
"""Instance of a running workflow."""

workflow_id: str
workflow_type: str
workflow_name: str
status: WorkflowStatus
input_data: Dict[str, Any]
output_data: Optional[Dict[str, Any]] = None
error_message: Optional[str] = None
start_time: Optional[str] = None
end_time: Optional[str] = None
parent_workflow_id: Optional[str] = None
child_workflow_ids: List[str] = field(default_factory=list)
metadata: Dict[str, Any] = field(default_factory=list)


class WorkflowRegistry:
"""
Central registry for all workflow definitions and instances.

TRUTH: Single registry prevents workflow duplication and enables:
- Consistent workflow discovery
- Centralized monitoring
- Unified versioning
- Dependency management
- Cross-workflow compatibility

Usage:
registry = WorkflowRegistry()

# Register workflow
@registry.register_workflow(
    name="marketing_campaign",
    workflow_type=WorkflowType.SAGA,
    timeout_seconds=3600
)
class MarketingCampaignWorkflow:
    ...

# Get workflow definition
definition = registry.get_workflow_definition("marketing_campaign")

# List workflows by type
saga_workflows = registry.list_workflows(WorkflowType.SAGA)
"""

def __init__(self):
"""Initialize workflow registry."""
self._workflow_definitions: Dict[str, WorkflowDefinition] = {}
self._workflow_instances: Dict[str, WorkflowInstance] = {}
self._workflow_classes: Dict[str, Type] = {}
self._workflow_task_queues: Dict[str, str] = {}

def register_workflow(
self,
name: str,
workflow_type: WorkflowType,
description: str = "",
version: str = "1.0.0",
tags: Optional[List[str]] = None,
timeout_seconds: Optional[int] = None,
retry_policy: Optional[Dict[str, Any]] = None,
parameters_schema: Optional[Dict[str, Any]] = None,
output_schema: Optional[Dict[str, Any]] = None,
) -> Callable:
"""
Decorator to register a workflow class.

Args:
name: Unique workflow name
workflow_type: Type of workflow
description: Human-readable description
version: Semantic version
tags: Searchable tags
timeout_seconds: Default timeout
retry_policy: Temporal retry policy
parameters_schema: JSON schema for input validation
output_schema: JSON schema for output validation

Returns:
Decorator function
"""
def decorator(workflow_class: Type) -> Type:
# Validate workflow class
if not inspect.isclass(workflow_class):
raise ValueError(f"{name} must be a class")

# Check if workflow methods exist
if not hasattr(workflow_class, "run"):
raise ValueError(f"Workflow class {name} must have a 'run' method")

# Create definition
definition = WorkflowDefinition(
    name=name,
    description=description,
    workflow_class=workflow_class,
    workflow_type=workflow_type,
    version=version,
    tags=tags or [],
    parameters_schema=parameters_schema,
    output_schema=output_schema,
    timeout_seconds=timeout_seconds,
    retry_policy=retry_policy,
)

# Register
self._workflow_definitions[name] = definition
self._workflow_classes[name] = workflow_class

# Set task queue based on type
self._workflow_task_queues[name] = f"{workflow_type.value}-{name}"

return workflow_class

return decorator

def get_workflow_definition(self, name: str) -> Optional[WorkflowDefinition]:
"""Get workflow definition by name."""
return self._workflow_definitions.get(name)

def get_workflow_class(self, name: str) -> Optional[Type]:
"""Get workflow class by name."""
return self._workflow_classes.get(name)

def get_workflow_task_queue(self, name: str) -> Optional[str]:
"""Get task queue for workflow."""
return self._workflow_task_queues.get(name)

def list_workflows(
self,
workflow_type: Optional[WorkflowType] = None,
tags: Optional[List[str]] = None,
is_active: Optional[bool] = None,
) -> List[WorkflowDefinition]:
"""
List workflow definitions with optional filtering.

Args:
workflow_type: Filter by workflow type
tags: Filter by tags (must match all)
is_active: Filter by active status

Returns:
List of matching workflow definitions
"""
definitions = list(self._workflow_definitions.values())

# Apply filters
if workflow_type:
definitions = [d for d in definitions if d.workflow_type == workflow_type]

if tags:
definitions = [
d for d in definitions
if all(tag in d.tags for tag in tags)
]

if is_active is not None:
definitions = [d for d in definitions if d.is_active == is_active]

return definitions

def create_workflow_instance(
self,
workflow_id: str,
workflow_name: str,
input_data: Dict[str, Any],
parent_workflow_id: Optional[str] = None,
) -> WorkflowInstance:
"""
Create a new workflow instance.

Args:
workflow_id: Unique instance identifier
workflow_name: Name of workflow definition
input_data: Input parameters
parent_workflow_id: Parent workflow ID (for nested workflows)

Returns:
New workflow instance

Raises:
ValueError: If workflow definition not found
"""
definition = self.get_workflow_definition(workflow_name)
if not definition:
raise ValueError(f"Workflow definition not found: {workflow_name}")

instance = WorkflowInstance(
    workflow_id=workflow_id,
    workflow_type=definition.workflow_type.value,
    workflow_name=workflow_name,
    status=WorkflowStatus.PENDING,
    input_data=input_data,
    parent_workflow_id=parent_workflow_id,
)

self._workflow_instances[workflow_id] = instance
return instance

def update_workflow_instance(
self,
workflow_id: str,
status: WorkflowStatus,
output_data: Optional[Dict[str, Any]] = None,
error_message: Optional[str] = None,
end_time: Optional[str] = None,
) -> Optional[WorkflowInstance]:
"""
Update workflow instance status and data.

Args:
workflow_id: Instance identifier
status: New status
output_data: Output from execution
error_message: Error message if failed
end_time: End timestamp

Returns:
Updated instance or None if not found
"""
instance = self._workflow_instances.get(workflow_id)
if not instance:
return None

instance.status = status
instance.output_data = output_data
instance.error_message = error_message
instance.end_time = end_time

return instance

def get_workflow_instance(self, workflow_id: str) -> Optional[WorkflowInstance]:
"""Get workflow instance by ID."""
return self._workflow_instances.get(workflow_id)

def get_workflow_instances(
self,
workflow_name: Optional[str] = None,
status: Optional[WorkflowStatus] = None,
parent_workflow_id: Optional[str] = None,
) -> List[WorkflowInstance]:
"""
List workflow instances with optional filtering.

Args:
workflow_name: Filter by workflow name
status: Filter by status
parent_workflow_id: Filter by parent workflow

Returns:
List of matching workflow instances
"""
instances = list(self._workflow_instances.values())

if workflow_name:
instances = [i for i in instances if i.workflow_name == workflow_name]

if status:
instances = [i for i in instances if i.status == status]

if parent_workflow_id:
instances = [i for i in instances if i.parent_workflow_id == parent_workflow_id]

return instances

def validate_workflow_input(self, workflow_name: str, input_data: Dict[str, Any]) -> bool:
"""
Validate workflow input against schema.

Args:
workflow_name: Name of workflow
input_data: Input to validate

Returns:
True if valid, False otherwise
"""
definition = self.get_workflow_definition(workflow_name)
if not definition or not definition.parameters_schema:
return True  # No schema to validate against

        raise NotImplementedError("JSON schema validation not yet implemented")

def get_workflow_dependencies(self, workflow_name: str) -> List[str]:
"""
Get list of workflow dependencies.

Args:
workflow_name: Name of workflow

Returns:
List of workflow names this workflow depends on
"""
definition = self.get_workflow_definition(workflow_name)
if not definition:
return []

# Extract dependencies from workflow class
workflow_class = definition.workflow_class

        raise NotImplementedError("Dependency analysis not yet implemented")

def get_statistics(self) -> Dict[str, Any]:
"""
Get workflow registry statistics.

Returns:
Dictionary with registry statistics
"""
total_workflows = len(self._workflow_definitions)
total_instances = len(self._workflow_instances)

# Count by type
type_counts = {}
for definition in self._workflow_definitions.values():
workflow_type = definition.workflow_type.value
type_counts[workflow_type] = type_counts.get(workflow_type, 0) + 1

# Count by status
status_counts = {}
for instance in self._workflow_instances.values():
status = instance.status.value
status_counts[status] = status_counts.get(status, 0) + 1

return {
"total_workflow_definitions": total_workflows,
"total_workflow_instances": total_instances,
"workflow_types": type_counts,
"workflow_statuses": status_counts,
}


# Global registry instance
workflow_registry = WorkflowRegistry()