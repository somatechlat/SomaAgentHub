"""
Deployment Strategy Pattern
Unified deployment configuration for all environments
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
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


class DevDeployment(DeploymentStrategy):
    """DEV mode deployment - local development with production-like setup"""
    
    def __init__(self):
        self.settings = get_settings()
        self.vault_manager = get_vault_manager()
    
    def get_database_url(self, service: str) -> str:
        """DEV database URL - localhost"""
        return f"postgresql://postgres:postgres@localhost:5432/soma"
    
    def get_redis_url(self) -> str:
        """DEV Redis URL - localhost"""
        return "redis://localhost:6379"
    
    def get_service_url(self, service: str) -> str:
        """DEV service URL - localhost"""
        port = self.settings.service_ports.get(service, 8080)
        return f"http://localhost:{port}"
    
    def get_port(self, service: str) -> int:
        """Get DEV port"""
        return self.settings.service_ports.get(service, 8080)
    
    def get_secrets(self, service: str) -> Dict[str, Any]:
        """DEV secrets - simple defaults"""
        return {
            "jwt_secret": "dev-jwt-secret-change-in-prod",
            "stripe_key": "dev-stripe-key",
            "redis_password": None
        }
    
    def get_environment_variables(self, service: str) -> Dict[str, str]:
        """DEV environment variables"""
        return {
            "SOMASTACK_ENVIRONMENT": "development",
            "SOMASTACK_DEPLOYMENT_MODE": "DEV",
            "SOMASTACK_SERVICE_NAME": service,
            "SOMASTACK_DATABASE_URL": self.get_database_url(service),
            "SOMASTACK_REDIS_URL": self.get_redis_url(),
            "SOMASTACK_LOG_LEVEL": "DEBUG",
            "SOMASTACK_ENABLE_METRICS": "false",
            "SOMASTACK_ENABLE_TRACING": "false"
        }


class ProdDeployment(DeploymentStrategy):
    """PROD mode deployment - production ready"""
    
    def __init__(self):
        self.settings = get_settings()
        self.vault_manager = get_vault_manager()
    
    def get_database_url(self, service: str) -> str:
        """PROD database URL from environment"""
        return os.getenv("SOMASTACK_DATABASE_URL", "postgresql://prod-db:5432/soma")
    
    def get_redis_url(self) -> str:
        """PROD Redis URL from environment"""
        return os.getenv("SOMASTACK_REDIS_URL", "redis://prod-redis:6379")
    
    def get_service_url(self, service: str) -> str:
        """PROD service URL via service discovery"""
        return f"http://{service}.soma.svc.cluster.local:8080"
    
    def get_port(self, service: str) -> int:
        """PROD port"""
        return 8080
    
    def get_secrets(self, service: str) -> Dict[str, Any]:
        """PROD secrets from environment/Vault"""
        return {
            "jwt_secret": os.getenv("SOMASTACK_JWT_SECRET", "prod-jwt-secret"),
            "stripe_key": os.getenv("SOMASTACK_STRIPE_KEY"),
            "redis_password": os.getenv("SOMASTACK_REDIS_PASSWORD")
        }
    
    def get_environment_variables(self, service: str) -> Dict[str, str]:
        """PROD environment variables"""
        return {
            "SOMASTACK_ENVIRONMENT": "production",
            "SOMASTACK_DEPLOYMENT_MODE": "PROD",
            "SOMASTACK_SERVICE_NAME": service,
            "SOMASTACK_LOG_LEVEL": "INFO",
            "SOMASTACK_ENABLE_METRICS": "true",
            "SOMASTACK_ENABLE_TRACING": "true"
        }


class DeploymentFactory:
    """Factory for creating deployment strategies - only DEV/PROD"""
    
    _strategies = {
        "DEV": DevDeployment,
        "PROD": ProdDeployment
    }
    
    @staticmethod
    def create_strategy(mode: str = None) -> DeploymentStrategy:
        """Create deployment strategy - DEV or PROD only"""
        if mode is None:
            mode = get_settings().deployment_mode
        
        # Simplify to only DEV and PROD
        if mode == "DEV":
            return DevDeployment()
        elif mode == "PROD":
            return ProdDeployment()
        else:
            raise ValueError("Deployment mode must be DEV or PROD")
    
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