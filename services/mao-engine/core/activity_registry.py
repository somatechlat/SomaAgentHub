"""
Unified Activity Registry for MAO Engine.

Central registry for all activity types, implementations, and metadata.
Single source of truth for activity orchestration.

TRUTH: Centralized activity registry eliminates duplication and enables consistent activity management.
"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union

from temporalio import activity


class ActivityType(str, Enum):
"""Types of activities supported by MAO engine."""

DATA_PROCESSING = "data_processing"  # Data transformation and processing
API_CALL = "api_call"  # External API interactions
DATABASE_OPERATION = "database_operation"  # Database operations
FILE_OPERATION = "file_operation"  # File system operations
AI_SERVICE = "ai_service"  # AI/ML service calls
NOTIFICATION = "notification"  # Email, SMS, push notifications
VALIDATION = "validation"  # Data validation and verification
COMPENSATION = "compensation"  # Compensation/rollback activities
CUSTOM = "custom"  # Custom business logic


class ActivityStatus(str, Enum):
"""Activity execution status."""

PENDING = "pending"
RUNNING = "running"
COMPLETED = "completed"
FAILED = "failed"
CANCELLED = "cancelled"
TIMED_OUT = "timed_out"
RETRYING = "retrying"


@dataclass
class ActivityDefinition:
"""Definition of an activity type."""

name: str
description: str
activity_func: Callable
activity_type: ActivityType
version: str = "1.0.0"
tags: List[str] = field(default_factory=list)
parameters_schema: Optional[Dict[str, Any]] = None
output_schema: Optional[Dict[str, Any]] = None
timeout_seconds: Optional[int] = None
retry_policy: Optional[Dict[str, Any]] = None
circuit_breaker_config: Optional[Dict[str, Any]] = None
is_active: bool = True
created_at: Optional[str] = None
updated_at: Optional[str] = None


@dataclass
class ActivityInstance:
"""Instance of a running activity."""

activity_id: str
activity_type: str
activity_name: str
status: ActivityStatus
input_data: Dict[str, Any]
output_data: Optional[Dict[str, Any]] = None
error_message: Optional[str] = None
start_time: Optional[str] = None
end_time: Optional[str] = None
workflow_id: Optional[str] = None
retry_count: int = 0
metadata: Dict[str, Any] = field(default_factory=list)


class ActivityRegistry:
"""
Central registry for all activity definitions and instances.

TRUTH: Single registry prevents activity duplication and enables:
- Consistent activity discovery
- Centralized monitoring
- Unified versioning
- Dependency management
- Cross-activity compatibility

Usage:
registry = ActivityRegistry()

# Register activity
@registry.register_activity(
    name="send_email",
    activity_type=ActivityType.NOTIFICATION,
    timeout_seconds=30
)
async def send_email(to: str, subject: str, body: str) -> bool:
    # Send email logic
    return True

# Get activity definition
definition = registry.get_activity_definition("send_email")

# List activities by type
notification_activities = registry.list_activities(ActivityType.NOTIFICATION)
"""

def __init__(self):
"""Initialize activity registry."""
self._activity_definitions: Dict[str, ActivityDefinition] = {}
self._activity_instances: Dict[str, ActivityInstance] = {}
self._activity_functions: Dict[str, Callable] = {}

def register_activity(
self,
name: str,
activity_type: ActivityType,
description: str = "",
version: str = "1.0.0",
tags: Optional[List[str]] = None,
timeout_seconds: Optional[int] = None,
retry_policy: Optional[Dict[str, Any]] = None,
circuit_breaker_config: Optional[Dict[str, Any]] = None,
parameters_schema: Optional[Dict[str, Any]] = None,
output_schema: Optional[Dict[str, Any]] = None,
) -> Callable:
"""
Decorator to register an activity function.

Args:
name: Unique activity name
activity_type: Type of activity
description: Human-readable description
version: Semantic version
tags: Searchable tags
timeout_seconds: Default timeout
retry_policy: Temporal retry policy
circuit_breaker_config: Circuit breaker configuration
parameters_schema: JSON schema for input validation
output_schema: JSON schema for output validation

Returns:
Decorator function
"""
def decorator(activity_func: Callable) -> Callable:
# Validate activity function
if not inspect.isfunction(activity_func) and not inspect.ismethod(activity_func):
    raise ValueError(f"{name} must be a function")

# Check if function is async
if not inspect.iscoroutinefunction(activity_func):
    raise ValueError(f"Activity function {name} must be async")

# Create definition
definition = ActivityDefinition(
    name=name,
    description=description,
    activity_func=activity_func,
    activity_type=activity_type,
    version=version,
    tags=tags or [],
    parameters_schema=parameters_schema,
    output_schema=output_schema,
    timeout_seconds=timeout_seconds,
    retry_policy=retry_policy,
    circuit_breaker_config=circuit_breaker_config,
)

# Register
self._activity_definitions[name] = definition
self._activity_functions[name] = activity_func

return activity_func

return decorator

def get_activity_definition(self, name: str) -> Optional[ActivityDefinition]:
"""Get activity definition by name."""
return self._activity_definitions.get(name)

def get_activity_function(self, name: str) -> Optional[Callable]:
"""Get activity function by name."""
return self._activity_functions.get(name)

def list_activities(
self,
activity_type: Optional[ActivityType] = None,
tags: Optional[List[str]] = None,
is_active: Optional[bool] = None,
) -> List[ActivityDefinition]:
"""
List activity definitions with optional filtering.

Args:
activity_type: Filter by activity type
tags: Filter by tags (must match all)
is_active: Filter by active status

Returns:
List of matching activity definitions
"""
definitions = list(self._activity_definitions.values())

# Apply filters
if activity_type:
definitions = [d for d in definitions if d.activity_type == activity_type]

if tags:
definitions = [
d for d in definitions
if all(tag in d.tags for tag in tags)
]

if is_active is not None:
definitions = [d for d in definitions if d.is_active == is_active]

return definitions

def create_activity_instance(
self,
activity_id: str,
activity_name: str,
input_data: Dict[str, Any],
workflow_id: Optional[str] = None,
) -> ActivityInstance:
"""
Create a new activity instance.

Args:
activity_id: Unique instance identifier
activity_name: Name of activity definition
input_data: Input parameters
workflow_id: Associated workflow ID

Returns:
New activity instance

Raises:
ValueError: If activity definition not found
"""
definition = self.get_activity_definition(activity_name)
if not definition:
raise ValueError(f"Activity definition not found: {activity_name}")

instance = ActivityInstance(
    activity_id=activity_id,
    activity_type=definition.activity_type.value,
    activity_name=activity_name,
    status=ActivityStatus.PENDING,
    input_data=input_data,
    workflow_id=workflow_id,
)

self._activity_instances[activity_id] = instance
return instance

def update_activity_instance(
self,
activity_id: str,
status: ActivityStatus,
output_data: Optional[Dict[str, Any]] = None,
error_message: Optional[str] = None,
end_time: Optional[str] = None,
retry_count: Optional[int] = None,
) -> Optional[ActivityInstance]:
"""
Update activity instance status and data.

Args:
activity_id: Instance identifier
status: New status
output_data: Output from execution
error_message: Error message if failed
end_time: End timestamp
retry_count: Update retry count

Returns:
Updated instance or None if not found
"""
instance = self._activity_instances.get(activity_id)
if not instance:
return None

instance.status = status
instance.output_data = output_data
instance.error_message = error_message
instance.end_time = end_time

if retry_count is not None:
    instance.retry_count = retry_count

return instance

def get_activity_instance(self, activity_id: str) -> Optional[ActivityInstance]:
"""Get activity instance by ID."""
return self._activity_instances.get(activity_id)

def get_activity_instances(
self,
activity_name: Optional[str] = None,
status: Optional[ActivityStatus] = None,
workflow_id: Optional[str] = None,
) -> List[ActivityInstance]:
"""
List activity instances with optional filtering.

Args:
activity_name: Filter by activity name
status: Filter by status
workflow_id: Filter by workflow ID

Returns:
List of matching activity instances
"""
instances = list(self._activity_instances.values())

if activity_name:
instances = [i for i in instances if i.activity_name == activity_name]

if status:
instances = [i for i in instances if i.status == status]

if workflow_id:
instances = [i for i in instances if i.workflow_id == workflow_id]

return instances

def validate_activity_input(self, activity_name: str, input_data: Dict[str, Any]) -> bool:
"""
Validate activity input against schema.

Args:
activity_name: Name of activity
input_data: Input to validate

Returns:
True if valid, False otherwise
"""
definition = self.get_activity_definition(activity_name)
if not definition or not definition.parameters_schema:
return True  # No schema to validate against

# TODO: Implement JSON schema validation
# For now, return True (schema validation will be implemented later)
return True

def get_activity_dependencies(self, activity_name: str) -> List[str]:
"""
Get list of activity dependencies.

Args:
activity_name: Name of activity

Returns:
List of activity names this activity depends on
"""
definition = self.get_activity_definition(activity_name)
if not definition:
return []

# Extract dependencies from activity function
activity_func = definition.activity_func

# TODO: Implement dependency analysis
# For now, return empty list (dependency analysis will be implemented later)
return []

def get_statistics(self) -> Dict[str, Any]:
"""
Get activity registry statistics.

Returns:
Dictionary with registry statistics
"""
total_activities = len(self._activity_definitions)
total_instances = len(self._activity_instances)

# Count by type
type_counts = {}
for definition in self._activity_definitions.values():
activity_type = definition.activity_type.value
type_counts[activity_type] = type_counts.get(activity_type, 0) + 1

# Count by status
status_counts = {}
for instance in self._activity_instances.values():
status = instance.status.value
status_counts[status] = status_counts.get(status, 0) + 1

return {
"total_activity_definitions": total_activities,
"total_activity_instances": total_instances,
"activity_types": type_counts,
"activity_statuses": status_counts,
}


# Global registry instance
activity_registry = ActivityRegistry()