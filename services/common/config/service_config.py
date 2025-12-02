"""Service-Specific Configuration Extensions

Provides service-specific configuration classes that extend the base configuration
with service-specific settings and validation.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .base_config import BaseConfig, ServiceConfig


@dataclass
class GatewayServiceConfig(ServiceConfig):
    """Configuration specific to the Gateway service."""
    orchestrator_url: str = "http://orchestrator:10001"
    identity_service_url: str = "http://identity-service:10002"
    pricing_service_url: str = "http://pricing-service:10026"
    settings_service_url: str = "http://settings-service:10008"
    enable_moderation: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    cors_origins: List[str] = None
    
    def __post_init__(self):
        if self.cors_origins is None:
    self.cors_origins = ["*"]


    @dataclass
    class OrchestratorServiceConfig(ServiceConfig):
    """Configuration specific to the Orchestrator service."""
    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "somagent.session.workflows"
    temporal_enabled: bool = True
    max_concurrent_workflows: int = 100
    workflow_timeout_seconds: int = 300
    agent_timeout_seconds: int = 600
    enable_agent_spawning: bool = True
    enable_workflow_persistence: bool = True


    @dataclass
    class BuilderServiceConfig(ServiceConfig):
    """Configuration specific to the Builder service."""
    template_storage_path: str = "/templates"
    artifact_storage_path: str = "/artifacts"
    max_build_concurrency: int = 5
    build_timeout_seconds: int = 1800
    enable_static_templates: bool = True
    enable_dynamic_generation: bool = True
    supported_frameworks: List[str] = None
    
    def __post_init__(self):
        if self.supported_frameworks is None:
    self.supported_frameworks = ["fastapi", "react", "helm"]


    @dataclass
    class CapsuleRegistryConfig(ServiceConfig):
    """Configuration specific to the Capsule Registry service."""
    storage_backend: str = "postgres"  # postgres, redis, filesystem
    storage_path: str = "/capsules"
    max_capsule_size_mb: int = 100
    enable_versioning: bool = True
    enable_signing: bool = True
    supported_capsule_types: List[str] = None
    
    def __post_init__(self):
        if self.supported_capsule_types is None:
    self.supported_capsule_types = ["static", "workflow", "external_service", "analytic"]


    @dataclass
    class AgentManagerConfig(ServiceConfig):
    """Configuration specific to the Agent Manager service."""
    max_concurrent_agents: int = 50
    agent_default_cpu: str = "500m"
    agent_default_memory: str = "512Mi"
    agent_default_timeout_seconds: int = 300
    enable_auto_scaling: bool = True
    enable_health_monitoring: bool = True
    cleanup_interval_seconds: int = 300
    supported_agent_types: List[str] = None
    
    def __post_init__(self):
        if self.supported_agent_types is None:
    self.supported_agent_types = ["llm", "code_generator", "ui_customizer", "data_analyzer"]


    @dataclass
    class IdentityServiceConfig(ServiceConfig):
    """Configuration specific to the Identity service."""
    jwt_issuer_url: str = "http://identity-service:10002"
    jwt_audience: str = "soma-client"
    jwt_expiration_minutes: int = 60
    enable_oidc: bool = True
    enable_oauth2: bool = True
    session_timeout_minutes: int = 120
    max_concurrent_sessions: int = 1000


    @dataclass
    class AnalyticsServiceConfig(ServiceConfig):
    """Configuration specific to the Analytics service."""
    storage_backend: str = "clickhouse"  # clickhouse, postgres, redis
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_database: str = "soma_analytics"
    enable_real_time_analytics: bool = True
    enable_batch_processing: bool = True
    retention_days: int = 30


# Service configuration factory
    _service_configs: Dict[str, type] = {
    "gateway-service": GatewayServiceConfig,
    "orchestrator-service": OrchestratorServiceConfig,
    "builder-service": BuilderServiceConfig,
    "capsule-registry": CapsuleRegistryConfig,
    "agent-manager": AgentManagerConfig,
    "identity-service": IdentityServiceConfig,
    "analytics-service": AnalyticsServiceConfig,
    }


    def register_service_config(service_name: str, config_class: type) -> None:
    """Register a new service configuration class."""
    _service_configs[service_name] = config_class


    def get_service_config_class(service_name: str) -> Optional[type]:
    """Get the configuration class for a specific service."""
    return _service_configs.get(service_name)


    def get_service_config(service_name: str, base_config: BaseConfig) -> ServiceConfig:
    """Get service-specific configuration based on base configuration."""
    config_class = _service_configs.get(service_name, ServiceConfig)
    
    # Extract service-specific settings from base config
    service_settings = {
    "name": service_name,
    "version": base_config.service_version,
    "port": base_config.port,
    "environment": base_config.dict(),
    }
    
    # Add service-specific overrides from environment
    import os
    service_prefix = f"SOMA_AGENT_HUB_{service_name.upper().replace('-', '_')}_"
    
    for key, value in os.environ.items():
        if key.startswith(service_prefix):
    setting_name = key[len(service_prefix):].lower()
    service_settings[setting_name] = value
    
    return config_class(**service_settings)


    def create_gateway_config(base_config: BaseConfig) -> GatewayServiceConfig:
    """Create gateway service configuration."""
    return get_service_config("gateway-service", base_config)


    def create_orchestrator_config(base_config: BaseConfig) -> OrchestratorServiceConfig:
    """Create orchestrator service configuration."""
    return get_service_config("orchestrator-service", base_config)


    def create_builder_config(base_config: BaseConfig) -> BuilderServiceConfig:
    """Create builder service configuration."""
    return get_service_config("builder-service", base_config)


    def create_capsule_registry_config(base_config: BaseConfig) -> CapsuleRegistryConfig:
    """Create capsule registry configuration."""
    return get_service_config("capsule-registry", base_config)


    def create_agent_manager_config(base_config: BaseConfig) -> AgentManagerConfig:
    """Create agent manager configuration."""
    return get_service_config("agent-manager", base_config)