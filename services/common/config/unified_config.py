"""
Unified Configuration System for SomaAgentHub
Supports DEV/PROD modes with resource optimization
"""

from __future__ import annotations

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel, Field

class DeploymentMode(str, Enum):
    DEV = "dev"
    PROD = "prod"
    PROD_HA = "prod_ha"

class ResourceProfile(str, Enum):
    LOCAL_10GB = "local_10gb"
    CLOUD_SMALL = "cloud_small"
    CLOUD_MEDIUM = "cloud_medium"
    CLOUD_LARGE = "cloud_large"

@dataclass
class ServiceConfig:
    replicas: int = 1
    cpu_limit: str = "500m"
    memory_limit: str = "512Mi"
    enabled: bool = True
    environment: Dict[str, str] = field(default_factory=dict)

@dataclass
class DatabaseConfig:
    single_instance: bool = True
    ha_replicas: int = 1
    backup_enabled: bool = True
    memory_limit: str = "1Gi"
    cpu_limit: str = "500m"

@dataclass
class MonitoringConfig:
    enabled: bool = True
    retention_days: int = 30
    metrics_enabled: bool = True
    logs_enabled: bool = True
    traces_enabled: bool = True
    alerting_enabled: bool = True

@dataclass
class EnvironmentConfig:
    deployment_mode: DeploymentMode
    resource_profile: ResourceProfile
    memory_limit_gb: int = 10
    cpu_limit: int = 4
    max_concurrent_builds: int = 3
    max_agents_per_build: int = 5
    debug_mode: bool = False
    services: Dict[str, ServiceConfig] = field(default_factory=dict)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    features: Dict[str, bool] = field(default_factory=dict)

class UnifiedConfigManager:
    def __init__(self, config_path: str = "config/unified.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.env_config = self._create_env_config()
    
    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return self._create_default_config()
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _create_default_config(self) -> Dict[str, Any]:
        return {
            "deployment_mode": "dev",
            "resource_profile": "local_10gb",
            "memory_limit_gb": 10,
            "cpu_limit": 4,
            "max_concurrent_builds": 3,
            "max_agents_per_build": 5,
            "debug_mode": False,
            "database": {"single_instance": True, "ha_replicas": 1, "backup_enabled": True},
            "monitoring": {"enabled": True, "retention_days": 30},
            "features": {
                "multi_tenant": True, "agent_spawning": True, "workflow_engine": True,
                "pricing_engine": True, "marketplace": True, "artifact_management": True
            },
            "services": {
                "gateway-api": {"replicas": 1, "cpu_limit": "200m", "memory_limit": "256Mi"},
                "workflow-engine": {"replicas": 1, "cpu_limit": "500m", "memory_limit": "512Mi"},
                "ai-services": {"replicas": 1, "cpu_limit": "1000m", "memory_limit": "1Gi"},
                "capsule-manager": {"replicas": 1, "cpu_limit": "300m", "memory_limit": "384Mi"},
                "data-services": {"replicas": 1, "cpu_limit": "300m", "memory_limit": "512Mi"},
                "governance-services": {"replicas": 1, "cpu_limit": "200m", "memory_limit": "256Mi"},
                "utility-services": {"replicas": 1, "cpu_limit": "200m", "memory_limit": "256Mi"},
                "database-cluster": {"replicas": 1, "cpu_limit": "500m", "memory_limit": "1Gi"},
                "cache-cluster": {"replicas": 1, "cpu_limit": "200m", "memory_limit": "256Mi"},
                "monitoring-stack": {"replicas": 1, "cpu_limit": "500m", "memory_limit": "1Gi"}
            },
            "environments": {
                "dev": {"resource_profile": "local_10gb", "memory_limit_gb": 10, "cpu_limit": 4},
                "prod": {"resource_profile": "cloud_medium", "memory_limit_gb": 0, "cpu_limit": 0},
                "prod_ha": {"resource_profile": "cloud_large", "memory_limit_gb": 0, "cpu_limit": 0}
            }
        }
    
    def _create_env_config(self) -> EnvironmentConfig:
        deployment_mode = DeploymentMode(os.getenv("DEPLOYMENT_MODE", "dev"))
        env_config = self.config["environments"].get(deployment_mode.value, {})
        
        services = {}
        for service_name, service_config in self.config["services"].items():
            env_service_config = env_config.get("services", {}).get(service_name, {})
            services[service_name] = ServiceConfig(
                replicas=env_service_config.get("replicas", service_config["replicas"]),
                cpu_limit=env_service_config.get("cpu_limit", service_config["cpu_limit"]),
                memory_limit=env_service_config.get("memory_limit", service_config["memory_limit"]),
                enabled=service_config.get("enabled", True)
            )
        
        return EnvironmentConfig(
            deployment_mode=deployment_mode,
            resource_profile=ResourceProfile(env_config.get("resource_profile", "local_10gb")),
            memory_limit_gb=env_config.get("memory_limit_gb", 10),
            cpu_limit=env_config.get("cpu_limit", 4),
            services=services,
            database=DatabaseConfig(**env_config.get("database", {})),
            monitoring=MonitoringConfig(**self.config.get("monitoring", {})),
            features=self.config.get("features", {})
        )

config_manager = UnifiedConfigManager()