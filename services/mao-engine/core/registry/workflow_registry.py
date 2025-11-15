"""
Workflow Registry for Centralized Workflow Management.

Central registry for all workflows with metadata, versioning, and discovery.
Provides single source of truth for all workflow definitions.

TRUTH: Centralized workflow registry prevents duplicate workflows and ensures consistency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Callable

from temporalio import workflow


class WorkflowStatus(str, Enum):
"""Workflow execution status."""

ACTIVE = "active"
DEPRECATED = "deprecated"
RETIRED = "retired"


@dataclass
class WorkflowMetadata:
"""
Metadata for a registered workflow.

Example:
WorkflowMetadata(
name="marketing_campaign",
version="1.0.0",
description="End-to-end marketing campaign workflow",
owner="marketing-team",
category="business_process",
tags=["campaign", "marketing", "automation"],
input_schema={"campaign_id": "str", "budget": "float"},
output_schema={"success": "bool", "campaign_url": "str"},
timeout_minutes=120,
retry_policy={"max_attempts": 3, "backoff_coefficient": 2},
dependencies=["github", "slack", "notion"],
created_at=datetime.now(UTC),
updated_at=datetime.now(UTC),
)
"""

name: str
version: str
description: str
owner: str
category: str
tags: list[str] = field(default_factory=list)
input_schema: dict[str, Any] = field(default_factory=dict)
output_schema: dict[str, Any] = field(default_factory=dict)
timeout_minutes: int = 60
retry_policy: dict[str, Any] = field(default_factory=dict)
dependencies: list[str] = field(default_factory=list)
status: WorkflowStatus = WorkflowStatus.ACTIVE
created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
custom_fields: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
"""
Complete workflow definition with function and metadata.

Example:
WorkflowDefinition(
workflow_func=marketing_campaign_workflow,
metadata=WorkflowMetadata(...),
execution_stats={
"total_executions": 150,
"success_rate": 0.95,
"avg_duration_seconds": 300,
}
)
"""

workflow_func: Callable
metadata: WorkflowMetadata
execution_stats: dict[str, Any] = field(default_factory=dict)


class WorkflowRegistry:
"""
Central registry for all workflows.

Features:
- Single source of truth for all workflow definitions
- Version management and deprecation
- Discovery and querying capabilities
- Execution statistics tracking
- Dependency management

Usage:
registry = WorkflowRegistry()

# Register workflow
registry.register(
marketing_campaign_workflow,
WorkflowMetadata(
name="marketing_campaign",
version="1.0.0",
description="End-to-end marketing campaign workflow",
owner="marketing-team",
category="business_process",
)
)

# Discover workflows
campaign_workflows = registry.find_by_category("business_process")
marketing_workflows = registry.find_by_owner("marketing-team")

# Execute workflow
workflow_def = registry.get("marketing_campaign", "1.0.0")
result = await workflow_def.workflow_func(**input_data)
"""

def __init__(self):
"""Initialize empty workflow registry."""
self._workflows: dict[str, dict[str, WorkflowDefinition]] = {}
# {name: {version: WorkflowDefinition}}
self._aliases: dict[str, tuple[str, str]] = {}
# {alias: (name, version)}

def register(
self,
workflow_func: Callable,
metadata: WorkflowMetadata,
aliases: list[str] | None = None,
) -> None:
"""
Register a workflow with metadata.

Args:
workflow_func: Temporal workflow function
metadata: Workflow metadata
aliases: Optional aliases for this workflow

Raises:
ValueError: If workflow name+version already exists
"""
name = metadata.name
version = metadata.version

# Check for duplicates
if name in self._workflows and version in self._workflows[name]:
raise ValueError(
f"Workflow '{name}' version '{version}' already registered"
)

# Register workflow
if name not in self._workflows:
self._workflows[name] = {}

self._workflows[name][version] = WorkflowDefinition(
workflow_func=workflow_func,
metadata=metadata,
)

# Register aliases
if aliases:
for alias in aliases:
if alias in self._aliases:
raise ValueError(
f"Alias '{alias}' already assigned to "
f"{self._aliases[alias][0]}:{self._aliases[alias][1]}"
)
self._aliases[alias] = (name, version)

workflow.logger.info(
f"[WorkflowRegistry] Registered workflow: {name}:{version}",
extra={
"name": name,
"version": version,
"aliases": aliases or [],
"category": metadata.category,
},
)

def get(self, name: str, version: str | None = None) -> WorkflowDefinition:
"""
Get workflow definition by name and version.

Args:
name: Workflow name
version: Specific version (if None, gets latest active)

Returns:
WorkflowDefinition

Raises:
KeyError: If workflow not found
"""
if name not in self._workflows:
raise KeyError(f"Workflow '{name}' not found")

if version is None:
# Get latest active version
versions = self._workflows[name]
active_versions = [
(v, defn) for v, defn in versions.items()
if defn.metadata.status == WorkflowStatus.ACTIVE
]

if not active_versions:
raise KeyError(f"No active versions found for workflow '{name}'")

# Sort by version (semantic versioning)
active_versions.sort(key=lambda x: x[0], reverse=True)
return active_versions[0][1]

if version not in self._workflows[name]:
raise KeyError(f"Version '{version}' not found for workflow '{name}'")

return self._workflows[name][version]

def resolve_alias(self, alias: str) -> WorkflowDefinition:
"""
Resolve workflow alias to definition.

Args:
alias: Workflow alias

Returns:
WorkflowDefinition

Raises:
KeyError: If alias not found
"""
if alias not in self._aliases:
raise KeyError(f"Alias '{alias}' not found")

name, version = self._aliases[alias]
return self.get(name, version)

def find_by_category(self, category: str) -> list[WorkflowDefinition]:
"""
Find all workflows in a category.

Args:
category: Category to search

Returns:
List of matching workflow definitions
"""
results = []
for versions in self._workflows.values():
for defn in versions.values():
if defn.metadata.category == category:
results.append(defn)

return results

def find_by_owner(self, owner: str) -> list[WorkflowDefinition]:
"""
Find all workflows owned by a team/person.

Args:
owner: Owner to search

Returns:
List of matching workflow definitions
"""
results = []
for versions in self._workflows.values():
for defn in versions.values():
if defn.metadata.owner == owner:
results.append(defn)

return results

def find_by_tag(self, tag: str) -> list[WorkflowDefinition]:
"""
Find all workflows with a specific tag.

Args:
tag: Tag to search

Returns:
List of matching workflow definitions
"""
results = []
for versions in self._workflows.values():
for defn in versions.values():
if tag in defn.metadata.tags:
results.append(defn)

return results

def search(self, query: str) -> list[WorkflowDefinition]:
"""
Search workflows by name, description, or tags.

Args:
query: Search query

Returns:
List of matching workflow definitions
"""
query_lower = query.lower()
results = []

for versions in self._workflows.values():
for defn in versions.values():
metadata = defn.metadata

# Search in name, description, tags
if (
query_lower in metadata.name.lower()
or query_lower in metadata.description.lower()
or any(query_lower in tag.lower() for tag in metadata.tags)
):
results.append(defn)

return results

def list_all(self, status: WorkflowStatus | None = None) -> list[WorkflowDefinition]:
"""
List all workflows, optionally filtered by status.

Args:
status: Filter by status (if None, returns all)

Returns:
List of workflow definitions
"""
results = []
for versions in self._workflows.values():
for defn in versions.values():
if status is None or defn.metadata.status == status:
results.append(defn)

return results

def get_versions(self, name: str) -> list[str]:
"""
Get all versions of a workflow.

Args:
name: Workflow name

Returns:
List of version strings
"""
if name not in self._workflows:
return []

return list(self._workflows[name].keys())

def update_metadata(
self,
name: str,
version: str,
**updates,
) -> None:
"""
Update workflow metadata.

Args:
name: Workflow name
version: Workflow version
**updates: Metadata fields to update

Raises:
KeyError: If workflow not found
"""
workflow_def = self.get(name, version)
metadata = workflow_def.metadata

# Update metadata fields
for key, value in updates.items():
if hasattr(metadata, key):
setattr(metadata, key, value)

metadata.updated_at = datetime.now(UTC)

workflow.logger.info(
f"[WorkflowRegistry] Updated metadata for {name}:{version}",
extra={"updates": list(updates.keys())},
)

def deprecate(self, name: str, version: str) -> None:
"""
Mark workflow as deprecated.

Args:
name: Workflow name
version: Workflow version
"""
self.update_metadata(name, version, status=WorkflowStatus.DEPRECATED)

workflow.logger.warning(
f"[WorkflowRegistry] Deprecated workflow: {name}:{version}",
)

def retire(self, name: str, version: str) -> None:
"""
Mark workflow as retired (cannot be executed).

Args:
name: Workflow name
version: Workflow version
"""
self.update_metadata(name, version, status=WorkflowStatus.RETIRED)

workflow.logger.warning(
f"[WorkflowRegistry] Retired workflow: {name}:{version}",
)

def get_statistics(self) -> dict[str, Any]:
"""
Get registry statistics.

Returns:
Dictionary with registry metrics
"""
total_workflows = sum(len(versions) for versions in self._workflows.values())
active_workflows = sum(
1
for versions in self._workflows.values()
for defn in versions.values()
if defn.metadata.status == WorkflowStatus.ACTIVE
)

category_counts = {}
owner_counts = {}

for versions in self._workflows.values():
for defn in versions.values():
# Count categories
category = defn.metadata.category
category_counts[category] = category_counts.get(category, 0) + 1

# Count owners
owner = defn.metadata.owner
owner_counts[owner] = owner_counts.get(owner, 0) + 1

return {
"total_workflows": total_workflows,
"active_workflows": active_workflows,
"deprecated_workflows": total_workflows - active_workflows,
"categories": category_counts,
"owners": owner_counts,
"aliases": len(self._aliases),
}


# Global workflow registry instance
_workflow_registry = WorkflowRegistry()


def get_workflow_registry() -> WorkflowRegistry:
"""Get the global workflow registry instance."""
return _workflow_registry


def register_workflow(
metadata: WorkflowMetadata,
aliases: list[str] | None = None,
):
"""
Decorator to register workflows with the global registry.

Usage:
@register_workflow(
WorkflowMetadata(
name="marketing_campaign",
version="1.0.0",
description="End-to-end marketing campaign workflow",
owner="marketing-team",
category="business_process",
)
)
@workflow.defn
class MarketingCampaignWorkflow:
@workflow.run
async def run(self, input_data: dict) -> dict:
# Workflow implementation
pass
"""
def decorator(workflow_func: Callable) -> Callable:
get_workflow_registry().register(workflow_func, metadata, aliases)
return workflow_func

return decorator