"""Configuration primitives for the orchestrator service using unified settings.

This module centralises environment-driven configuration using the unified
configuration system.
"""

import os
from functools import lru_cache
from services.common.config.unified_settings import get_settings
from services.common.registry.service_registry import get_service_registry
from services.common.secrets.vault_manager import get_vault_manager
from services.common.deployment.deployment_strategy import get_deployment_config

# Get unified settings
settings = get_settings()
registry = get_service_registry()
vault = get_vault_manager()
deployment_config = get_deployment_config("orchestrator")

# Service-specific configuration
SERVICE_NAME = "orchestrator"
SERVICE_PORT = settings.service_ports.get("orchestrator", 8081)

# Database configuration
DATABASE_URL = deployment_config.database_url
REDIS_URL = deployment_config.redis_url

# Temporal configuration (using SOMASTACK_ prefixed env vars)
TEMPORAL_TARGET_HOST = os.getenv("SOMASTACK_TEMPORAL_TARGET_HOST", "localhost:10009")
TEMPORAL_NAMESPACE = os.getenv("SOMASTACK_TEMPORAL_NAMESPACE", "default")
TEMPORAL_TASK_QUEUE = os.getenv("SOMASTACK_TEMPORAL_TASK_QUEUE", "somagent.session.workflows")
TEMPORAL_ENABLED = os.getenv("SOMASTACK_TEMPORAL_ENABLED", "false").lower() == "true"

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("SOMASTACK_KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_CLIENT_ID = os.getenv("SOMASTACK_KAFKA_CLIENT_ID", "orchestrator-service")
KAFKA_TOPIC_PREFIX = os.getenv("SOMASTACK_KAFKA_TOPIC_PREFIX", "orchestration")
KAFKA_SECURITY_PROTOCOL = os.getenv("SOMASTACK_KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")

# Service dependencies (using registry for discovery)
def get_service_url(service_name: str, default_path: str = "") -> str:
    """Get service URL with fallback to defaults"""
    try:
        return registry.get_service_url(service_name)
    except:
        port = settings.service_ports.get(service_name, 8080)
        return f"http://localhost:{port}{default_path}"

POLICY_ENGINE_URL = get_service_url("policy-engine", "/v1/evaluate")
IDENTITY_SERVICE_URL = get_service_url("identity-service", "/v1/tokens/issue")
NOTIFICATION_SERVICE_URL = get_service_url("notification-service", "/v1/notifications")
LLM_HUB_URL = get_service_url("llm-hub")
PRICING_SERVICE_URL = get_service_url("pricing-service")
CONSTITUTION_SERVICE_URL = get_service_url("constitution-service", "/v1")
CAPSULE_REPO_URL = get_service_url("capsule-repo", "/v1/capsules")

# Environment-specific configuration
ENVIRONMENT = settings.environment
DEPLOYMENT_MODE = settings.deployment_mode

# Service discovery
SERVICE_REGISTRY = registry

# Secrets management
SECRETS = vault.get_service_secrets(SERVICE_NAME)

# Configuration class for unified access
class UnifiedSettings:
    """Unified configuration settings"""
    
    def __init__(self):
        self.service_name = SERVICE_NAME
        self.temporal_target_host = TEMPORAL_TARGET_HOST
        self.temporal_namespace = TEMPORAL_NAMESPACE
        self.temporal_task_queue = TEMPORAL_TASK_QUEUE
        self.temporal_enabled = TEMPORAL_ENABLED
        self.database_url = DATABASE_URL
        self.redis_url = REDIS_URL
        self.policy_engine_url = POLICY_ENGINE_URL
        self.identity_service_url = IDENTITY_SERVICE_URL
        self.notification_service_url = NOTIFICATION_SERVICE_URL
        self.llm_hub_url = LLM_HUB_URL
        self.pricing_service_url = PRICING_SERVICE_URL
        self.constitution_service_url = CONSTITUTION_SERVICE_URL
        self.capsule_repo_url = CAPSULE_REPO_URL

@lru_cache
def get_settings() -> UnifiedSettings:
    """Singleton-style accessor used across the service."""
    return UnifiedSettings()

settings = get_settings()
