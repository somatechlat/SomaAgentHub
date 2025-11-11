"""
Service Registry Pattern
Centralized service discovery with health monitoring
"""

import httpx
import asyncio
from typing import Dict, Optional, List
from pydantic import BaseModel
import yaml
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ServiceEndpoint(BaseModel):
    """Service endpoint configuration"""
    name: str
    url: str
    port: int
    health_path: str = "/health"
    version: str = "1.0.0"
    region: str = "us-east-1"
    protocol: str = "http"
    tags: List[str] = []
    last_heartbeat: Optional[datetime] = None
    healthy: bool = True


class ServiceRegistry:
    """Centralized service discovery with health monitoring"""
    
    def __init__(self):
        self.services: Dict[str, ServiceEndpoint] = {}
        self._load_from_helm_values()
        self._load_from_compose()
        
    def _load_from_helm_values(self) -> None:
        """Load service configuration from helm values.yaml"""
        try:
            with open("k8s/helm/soma-agent/values.yaml", 'r') as f:
                values = yaml.safe_load(f)
                services = values.get('services', {})
                
                for service_name, config in services.items():
                    port = config.get('port', 8080)
                    # Handle template variables gracefully
                    if isinstance(port, str) and '$' in str(port):
                        port = 8080  # Default fallback
                    elif port is None:
                        port = 8080
                    
                    self.services[service_name] = ServiceEndpoint(
                        name=service_name,
                        url=f"http://{service_name}",
                        port=int(port),
                        health_path=config.get('health_path', '/health'),
                        version=config.get('version', '1.0.0')
                    )
        except FileNotFoundError:
            logger.warning("Helm values.yaml not found, using defaults")
            
    def _load_from_compose(self) -> None:
        """Load service configuration from docker-compose.yml as fallback"""
        try:
            with open("docker-compose.yml", 'r') as f:
                compose = yaml.safe_load(f)
                services = compose.get('services', {})
                
                for service_name, config in services.items():
                    if service_name not in self.services:
                        ports = config.get('ports', [])
                        port = 8080
                        if ports:
                            # Extract container port from host:container mapping
                            port_mapping = str(ports[0])
                            if ':' in port_mapping:
                                try:
                                    port = int(port_mapping.split(':')[1])
                                except (ValueError, IndexError):
                                    # Handle cases like "8080:8080" or just "8080"
                                    port = int(port_mapping.split(':')[0])
                            else:
                                try:
                                    port = int(port_mapping)
                                except ValueError:
                                    port = 8080
                        
                        self.services[service_name] = ServiceEndpoint(
                            name=service_name,
                            url=f"http://{service_name}",
                            port=port,
                            health_path='/health'
                        )
        except FileNotFoundError:
            logger.warning("docker-compose.yml not found")
    
    async def get_service_url(self, service_name: str, healthy_only: bool = True) -> str:
        """Get service URL with health checking"""
        if service_name not in self.services:
            raise ValueError(f"Service {service_name} not found in registry")
        
        service = self.services[service_name]
        
        if healthy_only and not await self.health_check(service_name):
            # Try to get backup service or raise
            raise ConnectionError(f"Service {service_name} is unhealthy")
        
        return f"{service.url}:{service.port}"
    
    async def health_check(self, service_name: str) -> bool:
        """Perform health check on a service"""
        if service_name not in self.services:
            return False
            
        service = self.services[service_name]
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                url = f"{service.url}:{service.port}{service.health_path}"
                response = await client.get(url)
                is_healthy = response.status_code == 200
                
                # Update health status
                service.healthy = is_healthy
                service.last_heartbeat = datetime.utcnow()
                
                return is_healthy
                
        except Exception as e:
            logger.warning(f"Health check failed for {service_name}: {e}")
            service.healthy = False
            return False
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Perform health check on all services"""
        results = {}
        
        # Create tasks for parallel health checks
        tasks = [
            self.health_check(service_name)
            for service_name in self.services.keys()
        ]
        
        service_names = list(self.services.keys())
        health_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for service_name, result in zip(service_names, health_results):
            if isinstance(result, Exception):
                results[service_name] = False
                logger.error(f"Health check error for {service_name}: {result}")
            else:
                results[service_name] = result
        
        return results
    
    def register_service(self, service: ServiceEndpoint) -> None:
        """Register a new service"""
        self.services[service.name] = service
        logger.info(f"Registered service: {service.name}")
    
    def deregister_service(self, service_name: str) -> None:
        """Deregister a service"""
        if service_name in self.services:
            del self.services[service_name]
            logger.info(f"Deregistered service: {service_name}")
    
    def get_all_services(self) -> List[ServiceEndpoint]:
        """Get all registered services"""
        return list(self.services.values())
    
    def get_healthy_services(self) -> List[ServiceEndpoint]:
        """Get only healthy services"""
        return [service for service in self.services.values() if service.healthy]
    
    async def discover_services(self) -> Dict[str, str]:
        """Discover all available services and their URLs"""
        discovered = {}
        
        for service_name in self.services.keys():
            try:
                url = await self.get_service_url(service_name)
                discovered[service_name] = url
            except Exception as e:
                logger.warning(f"Failed to discover {service_name}: {e}")
                discovered[service_name] = None
        
        return discovered


# Global registry instance
_registry = None

def get_service_registry() -> ServiceRegistry:
    """Get global service registry instance"""
    global _registry
    if _registry is None:
        _registry = ServiceRegistry()
    return _registry


async def initialize_registry() -> ServiceRegistry:
    """Initialize and perform initial health checks"""
    registry = get_service_registry()
    await registry.health_check_all()
    return registry