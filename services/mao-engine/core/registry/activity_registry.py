"""
Activity Registry for Centralized Activity Management.

Central registry for all activities with circuit breaker integration,
metadata, and discovery. Provides single source of truth for all activity definitions.

TRUTH: Centralized activity registry prevents duplicate activities and ensures consistency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Callable

from temporalio import activity

from ..patterns.circuit_breaker import CircuitBreaker, CircuitBreakerConfig


class ActivityStatus(str, Enum):
"""Activity execution status."""

ACTIVE = "active"
DEPRECATED = "deprecated"
RETIRED = "retired"


@dataclass
class ActivityMetadata:
"""
Metadata for a registered activity.

Example:
ActivityMetadata(
name="create_github_repo",
version="1.0.0",
description="Create GitHub repository for campaign",
owner="platform-team",
category="github",
tags=["github", "repository", "creation"],
input_schema={"name": "str", "private": "bool", "description": "str"},
output_schema={"repo_id": "str", "repo_url": "str"},
timeout_seconds=30,
retry_policy={"max_attempts": 3, "backoff_coefficient": 2},
service_name="github-api",
circuit_breaker_config={"failure_threshold": 5, "timeout_seconds": 60},
dependencies=["github-client"],
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
timeout_seconds: int = 30
retry_policy: dict[str, Any] = field(default_factory=dict)
service_name: str
circuit_breaker_config: dict[str, Any] = field(default_factory=dict)
dependencies: list[str] = field(default_factory=list)
status: ActivityStatus = ActivityStatus.ACTIVE
created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
custom_fields: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActivityDefinition:
"""
Complete activity definition with function, metadata, and circuit breaker.

Example:
ActivityDefinition(
activity_func=create_github_repo_activity,
metadata=ActivityMetadata(...),
circuit_breaker=CircuitBreaker("github-api", config),
execution_stats={
"total_calls": 1000,
"success_rate": 0.98,
"avg_duration_seconds": 2.5,
}
)
"""

activity_func: Callable
metadata: ActivityMetadata
circuit_breaker: CircuitBreaker | None = None
execution_stats: dict[str, Any] = field(default_factory=dict)


class ActivityRegistry:
"""
Central registry for all activities.

Features:
- Single source of truth for all activity definitions
- Automatic circuit breaker integration
- Version management and deprecation
- Discovery and querying capabilities
- Execution statistics tracking
- Dependency management

Usage:
registry = ActivityRegistry()

# Register activity
registry.register(
create_github_repo_activity,
ActivityMetadata(
name="create_github_repo",
version="1.0.0",
description="Create GitHub repository for campaign",
owner="platform-team",
category="github",
service_name="github-api",
circuit_breaker_config={"failure_threshold": 5, "timeout_seconds": 60},
)
)

# Discover activities
github_activities = registry.find_by_category("github")
platform_activities = registry.find_by_owner("platform-team")

# Execute activity with circuit breaker protection
activity_def = registry.get("create_github_repo", "1.0.0")
result = await activity_def.circuit_breaker.call(
activity_def.activity_func,
**input_data
)
"""

def __init__(self):
"""Initialize empty activity registry."""
self._activities: dict[str, dict[str, ActivityDefinition]] = {}
# {name: {version: ActivityDefinition}}
self._aliases: dict[str, tuple[str, str]] = {}
# {alias: (name, version)}
self._circuit_breakers: dict[str, CircuitBreaker] = {}
# {service_name: CircuitBreaker}

def register(
self,
activity_func: Callable,
metadata: ActivityMetadata,
aliases: list[str] | None = None,
) -> None:
"""
Register an activity with metadata and circuit breaker.

Args:
activity_func: Temporal activity function
metadata: Activity metadata
aliases: Optional aliases for this activity

Raises:
ValueError: If activity name+version already exists
"""
name = metadata.name
version = metadata.version

# Check for duplicates
if name in self._activities and version in self._activities[name]:
raise ValueError(
f"Activity '{name}' version '{version}' already registered"
)

# Create or get circuit breaker for the service
circuit_breaker = self._get_or_create_circuit_breaker(
metadata.service_name,
metadata.circuit_breaker_config,
)

# Register activity
if name not in self._activities:
self._activities[name] = {}

self._activities[name][version] = ActivityDefinition(
activity_func=activity_func,
metadata=metadata,
circuit_breaker=circuit_breaker,
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

activity.logger.info(
f"[ActivityRegistry] Registered activity: {name}:{version}",
extra={
"name": name,
"version": version,
"aliases": aliases or [],
"category": metadata.category,
"service": metadata.service_name,
},
)

def get(self, name: str, version: str | None = None) -> ActivityDefinition:
"""
Get activity definition by name and version.

Args:
name: Activity name
version: Specific version (if None, gets latest active)

Returns:
ActivityDefinition

Raises:
KeyError: If activity not found
"""
if name not in self._activities:
raise KeyError(f"Activity '{name}' not found")

if version is None:
# Get latest active version
versions = self._activities[name]
active_versions = [
(v, defn) for v, defn in versions.items()
if defn.metadata.status == ActivityStatus.ACTIVE
]

if not active_versions:
raise KeyError(f"No active versions found for activity '{name}'")

# Sort by version (semantic versioning)
active_versions.sort(key=lambda x: x[0], reverse=True)
return active_versions[0][1]

if version not in self._activities[name]:
raise KeyError(f"Version '{version}' not found for activity '{name}'")

return self._activities[name][version]

def resolve_alias(self, alias: str) -> ActivityDefinition:
"""
Resolve activity alias to definition.

Args:
alias: Activity alias

Returns:
ActivityDefinition

Raises:
KeyError: If alias not found
"""
if alias not in self._aliases:
raise KeyError(f"Alias '{alias}' not found")

name, version = self._aliases[alias]
return self.get(name, version)

def find_by_category(self, category: str) -> list[ActivityDefinition]:
"""
Find all activities in a category.

Args:
category: Category to search

Returns:
List of matching activity definitions
"""
results = []
for versions in self._activities.values():
for defn in versions.values():
if defn.metadata.category == category:
results.append(defn)

return results

def find_by_owner(self, owner: str) -> list[ActivityDefinition]:
"""
Find all activities owned by a team/person.

Args:
owner: Owner to search

Returns:
List of matching activity definitions
"""
results = []
for versions in self._activities.values():
for defn in versions.values():
if defn.metadata.owner == owner:
results.append(defn)

return results

def find_by_service(self, service_name: str) -> list[ActivityDefinition]:
"""
Find all activities for a specific service.

Args:
service_name: Service name to search

Returns:
List of matching activity definitions
"""
results = []
for versions in self._activities.values():
for defn in versions.values():
if defn.metadata.service_name == service_name:
results.append(defn)

return results

def find_by_tag(self, tag: str) -> list[ActivityDefinition]:
"""
Find all activities with a specific tag.

Args:
tag: Tag to search

Returns:
List of matching activity definitions
"""
results = []
for versions in self._activities.values():
for defn in versions.values():
if tag in defn.metadata.tags:
results.append(defn)

return results

def search(self, query: str) -> list[ActivityDefinition]:
"""
Search activities by name, description, or tags.

Args:
query: Search query

Returns:
List of matching activity definitions
"""
query_lower = query.lower()
results = []

for versions in self._activities.values():
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

def list_all(self, status: ActivityStatus | None = None) -> list[ActivityDefinition]:
"""
List all activities, optionally filtered by status.

Args:
status: Filter by status (if None, returns all)

Returns:
List of activity definitions
"""
results = []
for versions in self._activities.values():
for defn in versions.values():
if status is None or defn.metadata.status == status:
results.append(defn)

return results

def get_versions(self, name: str) -> list[str]:
"""
Get all versions of an activity.

Args:
name: Activity name

Returns:
List of version strings
"""
if name not in self._activities:
return []

return list(self._activities[name].keys())

def update_metadata(
self,
name: str,
version: str,
**updates,
) -> None:
"""
Update activity metadata.

Args:
name: Activity name
version: Activity version
**updates: Metadata fields to update

Raises:
KeyError: If activity not found
"""
activity_def = self.get(name, version)
metadata = activity_def.metadata

# Update metadata fields
for key, value in updates.items():
if hasattr(metadata, key):
setattr(metadata, key, value)

metadata.updated_at = datetime.now(UTC)

activity.logger.info(
f"[ActivityRegistry] Updated metadata for {name}:{version}",
extra={"updates": list(updates.keys())},
)

def deprecate(self, name: str, version: str) -> None:
"""
Mark activity as deprecated.

Args:
name: Activity name
version: Activity version
"""
self.update_metadata(name, version, status=ActivityStatus.DEPRECATED)

activity.logger.warning(
f"[ActivityRegistry] Deprecated activity: {name}:{version}",
)

def retire(self, name: str, version: str) -> None:
"""
Mark activity as retired (cannot be executed).

Args:
name: Activity name
version: Activity version
"""
self.update_metadata(name, version, status=ActivityStatus.RETIRED)

activity.logger.warning(
f"[ActivityRegistry] Retired activity: {name}:{version}",
)

def get_circuit_breaker(self, service_name: str) -> CircuitBreaker | None:
"""
Get circuit breaker for a service.

Args:
service_name: Service name

Returns:
CircuitBreaker instance or None if not found
"""
return self._circuit_breakers.get(service_name)

def get_all_circuit_breakers(self) -> dict[str, CircuitBreaker]:
"""
Get all circuit breakers (for monitoring endpoint).

Returns:
Dictionary of {service_name: CircuitBreaker}
"""
return self._circuit_breakers.copy()

def get_statistics(self) -> dict[str, Any]:
"""
Get registry statistics.

Returns:
Dictionary with registry metrics
"""
total_activities = sum(len(versions) for versions in self._activities.values())
active_activities = sum(
1
for versions in self._activities.values()
for defn in versions.values()
if defn.metadata.status == ActivityStatus.ACTIVE
)

category_counts = {}
owner_counts = {}
service_counts = {}

for versions in self._activities.values():
for defn in versions.values():
# Count categories
category = defn.metadata.category
category_counts[category] = category_counts.get(category, 0) + 1

# Count owners
owner = defn.metadata.owner
owner_counts[owner] = owner_counts.get(owner, 0) + 1

# Count services
service = defn.metadata.service_name
service_counts[service] = service_counts.get(service, 0) + 1

return {
"total_activities": total_activities,
"active_activities": active_activities,
"deprecated_activities": total_activities - active_activities,
"categories": category_counts,
"owners": owner_counts,
"services": service_counts,
"circuit_breakers": len(self._circuit_breakers),
"aliases": len(self._aliases),
}

def _get_or_create_circuit_breaker(
self,
service_name: str,
config_dict: dict[str, Any],
) -> CircuitBreaker:
"""
Get or create circuit breaker for a service.

Args:
service_name: Service name
config_dict: Circuit breaker configuration dictionary

Returns:
CircuitBreaker instance
"""
if service_name not in self._circuit_breakers:
# Convert dict to CircuitBreakerConfig
config = CircuitBreakerConfig(**config_dict)
self._circuit_breakers[service_name] = CircuitBreaker(service_name, config)

activity.logger.info(
f"[ActivityRegistry] Created circuit breaker for service: {service_name}",
)

return self._circuit_breakers[service_name]


# Global activity registry instance
_activity_registry = ActivityRegistry()


def get_activity_registry() -> ActivityRegistry:
"""Get the global activity registry instance."""
return _activity_registry


def register_activity(
metadata: ActivityMetadata,
aliases: list[str] | None = None,
):
"""
Decorator to register activities with the global registry.

Usage:
@register_activity(
ActivityMetadata(
name="create_github_repo",
version="1.0.0",
description="Create GitHub repository for campaign",
owner="platform-team",
category="github",
service_name="github-api",
circuit_breaker_config={"failure_threshold": 5, "timeout_seconds": 60},
)
)
@activity.defn
async def create_github_repo_activity(name: str, private: bool) -> dict:
# Activity implementation
pass
"""
def decorator(activity_func: Callable) -> Callable:
get_activity_registry().register(activity_func, metadata, aliases)
return activity_func

return decorator