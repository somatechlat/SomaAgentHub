"""
Unified Configuration Module
Single source of truth for all service configuration
"""

from pydantic import Field, validator
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Dict, Any, Optional
import os
import yaml


class UnifiedSettings(BaseSettings):
    """Single source of truth for all service configuration"""
    
    # Environment and Deployment
    environment: str = Field(default="development", description="Current environment")
    deployment_mode: str = Field(default="local", description="Deployment strategy")
    
    # Service Registry Configuration
    service_registry: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Database Configuration
    redis_url: str = Field(default="redis://redis:6379", description="Redis connection URL")
    postgres_url: str = Field(default="postgresql://postgres:postgres@postgres:5432/soma", description="PostgreSQL connection URL")
    clickhouse_url: str = Field(default="http://clickhouse:8123", description="ClickHouse connection URL")
    
    # Service Ports (from Helm values)
    service_ports: Dict[str, int] = Field(default_factory=lambda: {
        "gateway_api": 8080,
        "orchestrator": 8081,
        "memory_gateway": 8082,
        "policy_engine": 8083,
        "llm_hub": 8084,
        "pricing_service": 8085,
        "agent_spawner": 8086,
        "object_store": 8087,
        "token_estimator": 8088,
        "vault": 8200,
        "temporal": 7233,
        "prometheus": 9090,
        "grafana": 3000
    })
    
    # Secrets Management
    vault_address: str = Field(default="http://vault:8200", description="Vault server address")
    vault_token: str = Field(default="", description="Vault authentication token")
    
    # Security
    jwt_secret: str = Field(default="your-secret-key", description="JWT signing secret")
    session_timeout_hours: int = Field(default=24, description="Session timeout in hours")
    
    # Monitoring
    prometheus_url: str = Field(default="http://prometheus:9090", description="Prometheus endpoint")
    grafana_url: str = Field(default="http://grafana:3000", description="Grafana endpoint")
    
    # LLM Hub Configuration
    llm_hub_url: str = Field(default="http://llm-hub:8084", description="LLM Hub service URL")
    default_model_provider: str = Field(default="openai", description="Default LLM provider")
    
    # Pricing Service Configuration
    pricing_service_url: str = Field(default="http://pricing-service:8085", description="Pricing service URL")
    gpubroker_url: str = Field(default="https://api.gpubroker.com", description="GPUBroker API URL")
    
    # Feature Flags
    require_payment: bool = Field(default=False, description="Require payment for builds")
    enable_tracing: bool = Field(default=True, description="Enable distributed tracing")
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    
    # Rate Limiting
    max_agents_per_user: int = Field(default=10, description="Maximum concurrent agents per user")
    max_builds_per_hour: int = Field(default=100, description="Maximum builds per hour per tenant")
    
    # File Storage
    object_store_bucket: str = Field(default="soma-artifacts", description="S3 bucket for artifacts")
    object_store_region: str = Field(default="us-east-1", description="S3 region")
    
    @validator('environment')
    def validate_environment(cls, v):
        allowed = {'development', 'staging', 'production'}
        if v not in allowed:
            raise ValueError(f'Environment must be one of {allowed}')
        return v
    
    @validator('deployment_mode')
    def validate_deployment_mode(cls, v):
        allowed = {'local', 'docker', 'kubernetes'}
        if v not in allowed:
            raise ValueError(f'Deployment mode must be one of {allowed}')
        return v
    
    class Config:
        env_prefix = "SOMASTACK_"
        case_sensitive = False
        env_nested_delimiter = "__"


@lru_cache()
def get_settings() -> UnifiedSettings:
    """Singleton pattern for settings - ensures single instance"""
    return UnifiedSettings()


def load_helm_values() -> Dict[str, Any]:
    """Load service configuration from helm values.yaml"""
    helm_values_path = "k8s/helm/soma-agent/values.yaml"
    try:
        with open(helm_values_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        # Fallback to defaults if helm values not found (local dev)
        return {}


def reload_settings() -> None:
    """Force reload of settings (useful for testing)"""
    get_settings.cache_clear()


# Global settings instance
settings = get_settings()