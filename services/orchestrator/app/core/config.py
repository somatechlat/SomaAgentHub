"""Orchestrator service configuration.

This file uses environment variables with standardized prefix and provides
backward-compatibility via the shared resolver. No external unified modules
are required here to keep coupling low.
"""

import os
from services.common.config.base_settings import resolve_env, BaseServiceSettings

SERVICE_NAME = "orchestrator"

# Temporal configuration (DEV defaults, override via env)
TEMPORAL_TARGET_HOST = resolve_env("TEMPORAL_TARGET_HOST", "localhost:10009")
TEMPORAL_NAMESPACE = resolve_env("TEMPORAL_NAMESPACE", "default")
TEMPORAL_TASK_QUEUE = resolve_env("TEMPORAL_TASK_QUEUE", "somagent.session.workflows")
TEMPORAL_ENABLED = str(resolve_env("TEMPORAL_ENABLED", "false")).lower() == "true"

# Kafka configuration (DEV defaults)
KAFKA_BOOTSTRAP_SERVERS = resolve_env("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_CLIENT_ID = resolve_env("KAFKA_CLIENT_ID", "orchestrator-service")
KAFKA_TOPIC_PREFIX = resolve_env("KAFKA_TOPIC_PREFIX", "orchestration")
KAFKA_SECURITY_PROTOCOL = resolve_env("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")

# ---------------------------------------------------------------------------
# Settings aggregation
# ---------------------------------------------------------------------------


class Settings(BaseServiceSettings):
"""Concrete settings object for the Orchestrator service.

It extends the canonical ``BaseServiceSettings`` and maps the module level
constants to attributes expected throughout the codebase (e.g. ``settings.
temporal_target_host``). This replaces the previous pattern where callers
attempted to import a ``settings`` instance from this module but none was
defined, causing an ``ImportError`` during test collection.
"""

# Service identification
service_name: str = SERVICE_NAME

# Temporal configuration
temporal_target_host: str = TEMPORAL_TARGET_HOST
temporal_namespace: str = TEMPORAL_NAMESPACE
temporal_task_queue: str = TEMPORAL_TASK_QUEUE
temporal_enabled: bool = TEMPORAL_ENABLED

# Kafka configuration
kafka_bootstrap_servers: str = KAFKA_BOOTSTRAP_SERVERS
kafka_client_id: str = KAFKA_CLIENT_ID
kafka_topic_prefix: str = KAFKA_TOPIC_PREFIX
kafka_security_protocol: str = KAFKA_SECURITY_PROTOCOL

# Additional service URLs (canonical env vars)
policy_engine_url: str = resolve_env(
"POLICY_ENGINE_URL", "http://policy-engine:10020"
)
llm_hub_url: str = resolve_env("LLM_HUB_URL", "http://llm-hub:8000")
gateway_api_url: str = resolve_env("GATEWAY_API_URL", "http://gateway-api:10000")



# Database configuration (canonical prefix variables)
database_url: str = resolve_env(
"DATABASE_URL",
"postgresql+asyncpg://postgres:postgres@localhost:5432/orchestrator",
)
# Flags and pool settings – converted to appropriate types
database_echo: bool = str(resolve_env("DATABASE_ECHO", "false")).lower() == "true"
database_pool_size: int = int(resolve_env("DATABASE_POOL_SIZE", "5"))
database_max_overflow: int = int(resolve_env("DATABASE_MAX_OVERFLOW", "10"))
database_pool_timeout: int = int(resolve_env("DATABASE_POOL_TIMEOUT", "30"))
database_pool_recycle: int = int(resolve_env("DATABASE_POOL_RECYCLE", "1800"))


# Export a singleton instance for importers
settings = Settings()


def get_settings() -> Settings:
"""Return the singleton settings instance.

Many modules import ``get_settings`` for consistency with other services.
Providing this thin wrapper maintains the existing import contract.
"""
return settings
