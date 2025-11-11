"""Orchestrator service configuration.

This file uses environment variables with standardized prefix and provides
backward-compatibility via the shared resolver. No external unified modules
are required here to keep coupling low.
"""

import os
from services.common.config.base_settings import resolve_env

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
