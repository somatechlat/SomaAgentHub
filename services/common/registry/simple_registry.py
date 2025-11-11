"""
Simple Service Registry
Fallback registry that doesn't parse YAML files
"""

from typing import Dict
from services.common.config.base_settings import resolve_env


class SimpleServiceRegistry:
    """Simple service registry with hardcoded defaults"""
    
    def __init__(self):
        self.services = {
            "gateway_api": {
                "url": "http://localhost:8080",
                "port": 8080,
                "health_path": "/health"
            },
            "orchestrator": {
                "url": "http://localhost:8081", 
                "port": 8081,
                "health_path": "/health"
            },
            "memory_gateway": {
                "url": "http://localhost:8082",
                "port": 8082, 
                "health_path": "/health"
            },
            "policy_engine": {
                "url": "http://localhost:8083",
                "port": 8083,
                "health_path": "/health"
            },
            "llm_hub": {
                "url": "http://localhost:8084",
                "port": 8084,
                "health_path": "/health"
            },
            "pricing_service": {
                "url": "http://localhost:8085",
                "port": 8085,
                "health_path": "/health"
            },
            "agent_spawner": {
                "url": "http://localhost:8086", 
                "port": 8086,
                "health_path": "/health"
            },
            "object_store": {
                "url": "http://localhost:8087",
                "port": 8087,
                "health_path": "/health"
            },
            "token_estimator": {
                "url": "http://localhost:8088",
                "port": 8088,
                "health_path": "/health"
            }
        }
    
    def get_service_url(self, service_name: str) -> str:
        """Get service URL"""
        if service_name in self.services:
            service = self.services[service_name]
            return f"{service['url']}"
        
        # Handle service name variations
        name_variations = [
            service_name.replace('_', '-'),
            service_name.replace('-', '_'),
            service_name.lower(),
            service_name.replace('_', '')
        ]
        
        for name in name_variations:
            if name in self.services:
                service = self.services[name]
                return f"{service['url']}"
        
        # Fallback to localhost
        return f"http://localhost:8080"
    
    def get_service_port(self, service_name: str) -> int:
        """Get service port"""
        if service_name in self.services:
            return self.services[service_name]["port"]
        
        # Handle service name variations
        name_variations = [
            service_name.replace('_', '-'),
            service_name.replace('-', '_'),
            service_name.lower(),
            service_name.replace('_', '')
        ]
        
        for name in name_variations:
            if name in self.services:
                return self.services[name]["port"]
        
        return 8080
    
    def get_all_services(self) -> Dict[str, Dict]:
        """Get all services"""
        return self.services.copy()


# Global simple registry
simple_registry = SimpleServiceRegistry()
