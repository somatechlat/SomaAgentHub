"""Base Configuration Classes for SomaAgentHub

Provides the foundation for all configuration across the platform with strong
typing, validation, and environment variable resolution.
"""

from __future__ import annotations

import os
from enum import Enum
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from pathlib import Path

# NOTE: Pydantic v2 moved ``BaseSettings`` to the ``pydantic-settings`` package.
# The project historically imported ``BaseSettings`` directly from ``pydantic``.
# To maintain compatibility across versions, we attempt to import from
# ``pydantic`` first and fall back to ``pydantic_settings`` if unavailable.
try:
    from pydantic import BaseSettings, Field, validator, ConfigDict  # type: ignore
except ImportError:  # pragma: no cover
    from pydantic_settings import BaseSettings  # type: ignore
    from pydantic import Field, validator, ConfigDict  # type: ignore


class DeploymentMode(str, Enum):
    """Deployment modes for the platform."""
    DEV = "dev"
    PROD = "prod"
    PROD_HA = "prod_ha"


class ResourceProfile(str, Enum):
    """Resource profiles for different deployment sizes."""
    LOCAL_10GB = "local_10gb"
    CLOUD_SMALL = "cloud_small"
    CLOUD_MEDIUM = "cloud_medium"
    CLOUD_LARGE = "cloud_large"


@dataclass
class DatabaseConfig:
    """Database configuration with connection pooling and settings."""
    url: str
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 1800
    ssl_mode: Optional[str] = None


@dataclass
class RedisConfig:
    """Redis configuration for caching and session management."""
    url: str
    max_connections: int = 50
    decode_responses: bool = True
    ssl: bool = False
    health_check_interval: int = 30


@dataclass
class KafkaConfig:
    """Kafka configuration for event streaming."""
    bootstrap_servers: List[str]
    client_id: str
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: Optional[str] = None
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None
    ssl_context: Optional[Any] = None


@dataclass
class SecurityConfig:
    """Security configuration for authentication and authorization."""
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    mtls_enabled: bool = False
    cert_path: Optional[str] = None
    key_path: Optional[str] = None
    ca_cert_path: Optional[str] = None


@dataclass
class ObservabilityConfig:
    """Observability configuration for monitoring and tracing."""
    enable_tracing: bool = True
    enable_metrics: bool = True
    enable_logging: bool = True
    otlp_endpoint: Optional[str] = None
    log_level: str = "INFO"
    log_format: str = "json"
    metrics_port: int = 8000


@dataclass
class ServiceConfig:
    """Individual service configuration."""
    name: str
    version: str = "1.0.0"
    enabled: bool = True
    replicas: int = 1
    cpu_limit: str = "500m"
    memory_limit: str = "512Mi"
    cpu_request: str = "250m"
    memory_request: str = "256Mi"
    port: int = 8000
    environment: Dict[str, str] = field(default_factory=dict)
    health_check_path: str = "/health"
    readiness_check_path: str = "/ready"


class BaseConfig(BaseSettings):
    """Base configuration class for all SomaAgentHub services.
    
    This class provides a unified configuration system that replaces the
    multiple overlapping configuration patterns found throughout the codebase.
    
    Environment variables should use the prefix SOMA_AGENT_HUB_ for consistency.
    """
    
    # Basic configuration
    environment: str = Field(default="development", env="SOMA_AGENT_HUB_ENVIRONMENT")
    deployment_mode: DeploymentMode = Field(default=DeploymentMode.DEV, env="SOMA_AGENT_HUB_DEPLOYMENT_MODE")
    resource_profile: ResourceProfile = Field(default=ResourceProfile.LOCAL_10GB, env="SOMA_AGENT_HUB_RESOURCE_PROFILE")
    
    # Debug and logging
    debug: bool = Field(default=False, env="SOMA_AGENT_HUB_DEBUG")
    log_level: str = Field(default="INFO", env="SOMA_AGENT_HUB_LOG_LEVEL")
    
    # Service identification
    service_name: str = Field(default="unknown", env="SOMA_AGENT_HUB_SERVICE_NAME")
    service_version: str = Field(default="1.0.0", env="SOMA_AGENT_HUB_SERVICE_VERSION")
    
    # Network configuration
    host: str = Field(default="0.0.0.0", env="SOMA_AGENT_HUB_HOST")
    port: int = Field(default=8000, env="SOMA_AGENT_HUB_PORT")
    
    # Database configuration
    database_url: Optional[str] = Field(default=None, env="SOMA_AGENT_HUB_DATABASE_URL")
    database_echo: bool = Field(default=False, env="SOMA_AGENT_HUB_DATABASE_ECHO")
    database_pool_size: int = Field(default=5, env="SOMA_AGENT_HUB_DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, env="SOMA_AGENT_HUB_DATABASE_MAX_OVERFLOW")
    database_pool_timeout: int = Field(default=30, env="SOMA_AGENT_HUB_DATABASE_POOL_TIMEOUT")
    database_pool_recycle: int = Field(default=1800, env="SOMA_AGENT_HUB_DATABASE_POOL_RECYCLE")
    
    # Redis configuration
    redis_url: Optional[str] = Field(default=None, env="SOMA_AGENT_HUB_REDIS_URL")
    redis_max_connections: int = Field(default=50, env="SOMA_AGENT_HUB_REDIS_MAX_CONNECTIONS")
    
    # Kafka configuration
    kafka_bootstrap_servers: str = Field(default="localhost:9092", env="SOMA_AGENT_HUB_KAFKA_BOOTSTRAP_SERVERS")
    kafka_client_id: Optional[str] = Field(default=None, env="SOMA_AGENT_HUB_KAFKA_CLIENT_ID")
    kafka_security_protocol: str = Field(default="PLAINTEXT", env="SOMA_AGENT_HUB_KAFKA_SECURITY_PROTOCOL")
    
    # Security configuration
    jwt_secret: Optional[str] = Field(default=None, env="SOMA_AGENT_HUB_JWT_SECRET")
    mtls_enabled: bool = Field(default=False, env="SOMA_AGENT_HUB_MTLS_ENABLED")
    
    # Observability configuration
    enable_tracing: bool = Field(default=True, env="SOMA_AGENT_HUB_ENABLE_TRACING")
    enable_metrics: bool = Field(default=True, env="SOMA_AGENT_HUB_ENABLE_METRICS")
    otlp_endpoint: Optional[str] = Field(default=None, env="SOMA_AGENT_HUB_OTLP_ENDPOINT")
    
    # External service URLs
    temporal_host: Optional[str] = Field(default=None, env="SOMA_AGENT_HUB_TEMPORAL_HOST")
    temporal_namespace: str = Field(default="default", env="SOMA_AGENT_HUB_TEMPORAL_NAMESPACE")
    vault_url: Optional[str] = Field(default=None, env="SOMA_AGENT_HUB_VAULT_URL")
    opa_url: Optional[str] = Field(default=None, env="SOMA_AGENT_HUB_OPA_URL")
    
    # Feature flags
    enable_health_checks: bool = Field(default=True, env="SOMA_AGENT_HUB_ENABLE_HEALTH_CHECKS")
    enable_metrics_endpoint: bool = Field(default=True, env="SOMA_AGENT_HUB_ENABLE_METRICS_ENDPOINT")
    
    # Pydantic v2 uses ``model_config`` (a ``ConfigDict``) for configuration.
    # This replaces the legacy ``Config`` inner class. It sets the environment
    # variable prefix, disables case‑sensitivity, points to a ``.env`` file, and
    # allows extra fields so that unknown environment variables do not raise
    # validation errors.
    model_config = ConfigDict(
        env_prefix="SOMA_AGENT_HUB_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    @validator("service_name", pre=True)
    def default_service_name(cls, v):
        """Set default service name from module path if not provided."""
        if v is None or v == "unknown":
            # Try to infer from calling module
            import inspect
            frame = inspect.currentframe()
            if frame and frame.f_back:
                module = inspect.getmodule(frame.f_back)
                if module:
                    # Extract service name from module path
                    path_parts = module.__name__.split(".")
                    if "services" in path_parts:
                        services_idx = path_parts.index("services")
                        if len(path_parts) > services_idx + 1:
                            return path_parts[services_idx + 1]
        return v or "unknown"

    @validator("kafka_client_id", pre=True)
    def default_kafka_client_id(cls, v, values):
        """Set default Kafka client ID from service name."""
        if v is None and "service_name" in values:
            return values["service_name"]
        return v

    @property
    def is_dev(self) -> bool:
        """Check if running in development mode."""
        return self.deployment_mode == DeploymentMode.DEV

    @property
    def is_prod(self) -> bool:
        """Check if running in production mode."""
        return self.deployment_mode in (DeploymentMode.PROD, DeploymentMode.PROD_HA)

    @property
    def is_prod_ha(self) -> bool:
        """Check if running in production HA mode."""
        return self.deployment_mode == DeploymentMode.PROD_HA

    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration with defaults."""
        url = self.database_url or os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/soma")
        return DatabaseConfig(
            url=url,
            echo=self.database_echo,
            pool_size=self.database_pool_size,
            max_overflow=self.database_max_overflow,
            pool_timeout=self.database_pool_timeout,
            pool_recycle=self.database_pool_recycle,
        )

    def get_redis_config(self) -> RedisConfig:
        """Get Redis configuration with defaults."""
        url = self.redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        return RedisConfig(
            url=url,
            max_connections=self.redis_max_connections,
            decode_responses=True,
            ssl=self.kafka_security_protocol in ("SSL", "SASL_SSL"),
        )

    def get_kafka_config(self) -> KafkaConfig:
        """Get Kafka configuration with defaults."""
        servers = [s.strip() for s in self.kafka_bootstrap_servers.split(",") if s.strip()]
        return KafkaConfig(
            bootstrap_servers=servers,
            client_id=self.kafka_client_id or self.service_name,
            security_protocol=self.kafka_security_protocol,
        )

    def get_security_config(self) -> SecurityConfig:
        """Get security configuration with defaults."""
        jwt_secret = self.jwt_secret or os.getenv("JWT_SECRET", "dev-secret-not-for-production")
        return SecurityConfig(
            jwt_secret=jwt_secret,
            mtls_enabled=self.mtls_enabled,
        )

    def get_observability_config(self) -> ObservabilityConfig:
        """Get observability configuration."""
        return ObservabilityConfig(
            enable_tracing=self.enable_tracing,
            enable_metrics=self.enable_metrics,
            enable_logging=True,
            otlp_endpoint=self.otlp_endpoint,
            log_level=self.log_level,
            metrics_port=self.port + 1,  # Metrics on port + 1
        )

    def get_service_config(self) -> ServiceConfig:
        """Get this service's configuration."""
        return ServiceConfig(
            name=self.service_name,
            version=self.service_version,
            port=self.port,
            environment=self.dict(),
        )

    @classmethod
    def load_from_file(cls, config_path: Path) -> BaseConfig:
        """Load configuration from YAML file."""
        import yaml
        
        if not config_path.exists():
            return cls()
            
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
            
        return cls(**config_data)

    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to YAML file."""
        import yaml
        
        config_data = self.dict()
        with open(config_path, 'w') as f:
            yaml.safe_dump(config_data, f, default_flow_style=False)


# Global configuration instance
_config_instance: Optional[BaseConfig] = None


def get_config() -> BaseConfig:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = BaseConfig()
    return _config_instance


def set_config(config: BaseConfig) -> None:
    """Set the global configuration instance."""
    global _config_instance
    _config_instance = config


# Backwards compatibility
settings = get_config()
get_settings = get_config