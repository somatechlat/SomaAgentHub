"""
Deployment Strategy Pattern
Unified deployment configuration for all environments
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os
import yaml
from dataclasses import dataclass

from ..config.unified_settings import get_settings
from ..secrets.vault_manager import get_vault_manager


@dataclass
class DeploymentConfig:
    """Deployment configuration data structure"""
    environment: str
    deployment_mode: str
    database_url: str
    redis_url: str
    service_urls: Dict[str, str]
    secrets: Dict[str, Any]
    ports: Dict[str, int]
    volumes: Dict[str, str]
    network_config: Dict[str, Any]


class DeploymentStrategy(ABC):
    """Abstract deployment strategy"""
    
    @abstractmethod
    def get_database_url(self, service: str) -> str:
        """Get database URL for service"""
        pass
    
    @abstractmethod
    def get_redis_url(self) -> str:
        """Get Redis URL"""
        pass
    
    @abstractmethod
    def get_service_url(self, service: str) -> str:
        """Get service URL"""
        pass
    
    @abstractmethod
    def get_port(self, service: str) -> int:
        """Get service port"""
        pass
    
    @abstractmethod
    def get_secrets(self, service: str) -> Dict[str, Any]:
        """Get service-specific secrets"""
        pass
    
    @abstractmethod
    def get_environment_variables(self, service: str) -> Dict[str, str]:
        """Get environment variables for service"""
        pass


class LocalDeployment(DeploymentStrategy):
    """Local development deployment strategy"""
    
    def __init__(self):
        self.settings = get_settings()
        self.vault_manager = get_vault_manager()
    
    def get_database_url(self, service: str) -> str:
        """Local database URL"""
        return f"postgresql://postgres:postgres@localhost:5432/{service}_dev"
    
    def get_redis_url(self) -> str:
        """Local Redis URL"""
        return "redis://localhost:6379"
    
    def get_service_url(self, service: str) -> str:
        """Local service URL"""
        port = self.settings.service_ports.get(service, 8080)
        return f"http://localhost:{port}"
    
    def get_port(self, service: str) -> int:
        """Get local port"""
        return self.settings.service_ports.get(service, 8080)
    
    def get_secrets(self, service: str) -> Dict[str, Any]:
        """Get development secrets"""
        return self.vault_manager.get_service_secrets(service)
    
    def get_environment_variables(self, service: str) -> Dict[str, str]:
        """Get environment variables for local development"""
        return {
            "ENVIRONMENT": "development",
            "DEPLOYMENT_MODE": "local",
            "DATABASE_URL": self.get_database_url(service),
            "REDIS_URL": self.get_redis_url(),
            "SERVICE_NAME": service,
            "LOG_LEVEL": "DEBUG",
            "PROMETHEUS_ENABLED": "false",
            "TRACING_ENABLED": "false"
        }


class DockerDeployment(DeploymentStrategy):
    """Docker deployment strategy"""
    
    def __init__(self):
        self.settings = get_settings()
        self.vault_manager = get_vault_manager()
    
    def get_database_url(self, service: str) -> str:
        """Docker database URL"""
        return "postgresql://postgres:postgres@postgres:5432/soma"
    
    def get_redis_url(self) -> str:
        """Docker Redis URL"""
        return "redis://redis:6379"
    
    def get_service_url(self, service: str) -> str:
        """Docker service URL"""
        port = self.settings.service_ports.get(service, 8080)
        return f"http://{service}:{port}"
    
    def get_port(self, service: str) -> int:
        """Get Docker port"""
        return self.settings.service_ports.get(service, 8080)
    
    def get_secrets(self, service: str) -> Dict[str, Any]:
        """Get Docker secrets"""
        return self.vault_manager.get_service_secrets(service)
    
    def get_environment_variables(self, service: str) -> Dict[str, str]:
        """Get environment variables for Docker"""
        return {
            "ENVIRONMENT": "development",
            "DEPLOYMENT_MODE": "docker",
            "DATABASE_URL": self.get_database_url(service),
            "REDIS_URL": self.get_redis_url(),
            "SERVICE_NAME": service,
            "LOG_LEVEL": "INFO",
            "PROMETHEUS_ENABLED": "true",
            "TRACING_ENABLED": "true"
        }


class KubernetesDeployment(DeploymentStrategy):
    """Kubernetes production deployment strategy"""
    
    def __init__(self):
        self.settings = get_settings()
        self.vault_manager = get_vault_manager()
    
    def get_database_url(self, service: str) -> str:
        """Kubernetes database URL from Vault"""
        try:
            db_creds = self.vault_manager.get_database_credentials(service)
            return f"postgresql://{db_creds['username']}:{db_creds['password']}@postgres-cluster:5432/soma"
        except:
            # Fallback to environment
            return os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/soma")
    
    def get_redis_url(self) -> str:
        """Kubernetes Redis URL"""
        return "redis://redis-master:6379"
    
    def get_service_url(self, service: str) -> str:
        """Kubernetes service URL"""
        return f"http://{service}.soma.svc.cluster.local:8080"
    
    def get_port(self, service: str) -> int:
        """Get Kubernetes port"""
        return 8080  # Standard port in K8s
    
    def get_secrets(self, service: str) -> Dict[str, Any]:
        """Get Kubernetes secrets from Vault"""
        return self.vault_manager.get_service_secrets(service)
    
    def get_environment_variables(self, service: str) -> Dict[str, str]:
        """Get environment variables for Kubernetes"""
        return {
            "ENVIRONMENT": "production",
            "DEPLOYMENT_MODE": "kubernetes",
            "DATABASE_URL": self.get_database_url(service),
            "REDIS_URL": self.get_redis_url(),
            "SERVICE_NAME": service,
            "LOG_LEVEL": "INFO",
            "PROMETHEUS_ENABLED": "true",
            "TRACING_ENABLED": "true",
            "VAULT_ADDR": self.settings.vault_address,
            "VAULT_TOKEN": self.settings.vault_token
        }


class DeploymentFactory:
    """Factory for creating deployment strategies"""
    
    _strategies = {
        "local": LocalDeployment,
        "docker": DockerDeployment,
        "kubernetes": KubernetesDeployment
    }
    
    @classmethod
    def create_strategy(cls, mode: str = None) -> DeploymentStrategy:
        """Create deployment strategy based on mode"""
        if mode is None:
            mode = get_settings().deployment_mode
        
        if mode not in cls._strategies:
            raise ValueError(f"Unknown deployment mode: {mode}. Must be one of {list(cls._strategies.keys())}")
        
        return cls._strategies[mode]()
    
    @classmethod
    def get_available_modes(cls) -> List[str]:
        """Get available deployment modes"""
        return list(cls._strategies.keys())
    
    @classmethod
    def validate_mode(cls, mode: str) -> bool:
        """Validate deployment mode"""
        return mode in cls._strategies


class DeploymentConfigGenerator:
    """Generate deployment configurations for different environments"""
    
    @staticmethod
    def generate_compose_override(service: str, strategy: DeploymentStrategy) -> Dict[str, Any]:
        """Generate Docker Compose override for service"""
        env_vars = strategy.get_environment_variables(service)
        
        return {
            "version": "3.8",
            "services": {
                service: {
                    "environment": env_vars,
                    "ports": [f"{strategy.get_port(service)}:{strategy.get_port(service)}"]
                }
            }
        }
    
    @staticmethod
    def generate_k8s_config(service: str, strategy: DeploymentStrategy) -> Dict[str, Any]:
        """Generate Kubernetes ConfigMap for service"""
        env_vars = strategy.get_environment_variables(service)
        
        return {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": f"{service}-config",
                "namespace": "soma"
            },
            "data": env_vars
        }
    
    @staticmethod
    def generate_env_file(service: str, strategy: DeploymentStrategy) -> str:
        """Generate .env file for service"""
        env_vars = strategy.get_environment_variables(service)
        
        env_content = []
        for key, value in env_vars.items():
            env_content.append(f"{key}={value}")
        
        return "\n".join(env_content)


def get_deployment_config(service: str, mode: str = None) -> DeploymentConfig:
    """Get complete deployment configuration for service"""
    strategy = DeploymentFactory.create_strategy(mode)
    
    return DeploymentConfig(
        environment=get_settings().environment,
        deployment_mode=get_settings().deployment_mode,
        database_url=strategy.get_database_url(service),
        redis_url=strategy.get_redis_url(),
        service_urls={name: strategy.get_service_url(name) for name in get_settings().service_ports.keys()},
        secrets=strategy.get_secrets(service),
        ports=get_settings().service_ports,
        volumes={},
        network_config=strategy.get_environment_variables(service)
    )


# Global deployment strategy
deployment_strategy = DeploymentFactory.create_strategy()