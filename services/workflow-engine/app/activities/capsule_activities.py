"""
Capsule Activities - Activity implementations for capsule workflows
"""

import logging
import os
import json
import asyncio
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class CapsuleActivities:
    """Capsule activity implementations"""
    
    def __init__(self):
        self.capsule_registry = {}
        self.capsule_templates = {}
    
    async def validate_capsule_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate capsule configuration"""
        
        logger.info(f"Validating capsule config: {config}")
        
        capsule_name = config.get("capsule_name")
        capsule_config = config.get("config", {})
        
        # Validate required fields
        if not capsule_name:
            raise ValueError("Capsule name is required")
        
        # Validate capsule type
        capsule_type = capsule_config.get("type", "general")
        valid_types = ["general", "specialized", "custom"]
        
        if capsule_type not in valid_types:
            raise ValueError(f"Invalid capsule type: {capsule_type}")
        
        # Validate resources
        resources = capsule_config.get("resources", {})
        required_resources = ["cpu", "memory", "storage"]
        
        for resource in required_resources:
            if resource not in resources:
                raise ValueError(f"Missing required resource: {resource}")
        
        # Validate dependencies
        dependencies = capsule_config.get("dependencies", [])
        for dep in dependencies:
            if not isinstance(dep, dict) or "name" not in dep:
                raise ValueError(f"Invalid dependency format: {dep}")
        
        validated_config = {
            "capsule_name": capsule_name,
            "type": capsule_type,
            "resources": resources,
            "dependencies": dependencies,
            "validated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Capsule config validated successfully: {validated_config}")
        return validated_config
    
    async def create_capsule_infrastructure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create capsule infrastructure"""
        
        logger.info(f"Creating capsule infrastructure: {config}")
        
        capsule_name = config.get("capsule_name")
        validated_config = config.get("config", {})
        
        # Create capsule directory structure
        capsule_base_path = f"/var/lib/soma/capsules/{capsule_name}"
        
        try:
            # Create base directory
            os.makedirs(capsule_base_path, exist_ok=True)
            
            # Create subdirectories
            subdirs = ["config", "data", "logs", "temp", "agents"]
            for subdir in subdirs:
                os.makedirs(os.path.join(capsule_base_path, subdir), exist_ok=True)
            
            # Create capsule configuration file
            config_file = os.path.join(capsule_base_path, "config", "capsule.json")
            with open(config_file, "w") as f:
                json.dump(validated_config, f, indent=2)
            
            # Create capsule metadata
            metadata = {
                "capsule_name": capsule_name,
                "created_at": datetime.utcnow().isoformat(),
                "status": "created",
                "base_path": capsule_base_path,
                "config": validated_config
            }
            
            # Store in registry
            self.capsule_registry[capsule_name] = metadata
            
            logger.info(f"Capsule infrastructure created successfully: {metadata}")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to create capsule infrastructure: {e}")
            raise
    
    async def initialize_capsule_services(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize capsule services"""
        
        logger.info(f"Initializing capsule services: {config}")
        
        capsule_name = config.get("capsule_name")
        infrastructure = config.get("infrastructure", {})
        
        # Initialize core services
        services = {
            "agent_service": {
                "status": "initialized",
                "port": 8001,
                "endpoints": ["/agents", "/agents/{agent_id}", "/agents/{agent_id}/execute"]
            },
            "data_service": {
                "status": "initialized",
                "port": 8002,
                "endpoints": ["/data", "/data/{dataset_id}", "/data/query"]
            },
            "workflow_service": {
                "status": "initialized",
                "port": 8003,
                "endpoints": ["/workflows", "/workflows/{workflow_id}", "/workflows/{workflow_id}/execute"]
            },
            "monitoring_service": {
                "status": "initialized",
                "port": 8004,
                "endpoints": ["/metrics", "/health", "/logs"]
            }
        }
        
        # Update capsule registry
        if capsule_name in self.capsule_registry:
            self.capsule_registry[capsule_name]["services"] = services
            self.capsule_registry[capsule_name]["status"] = "services_initialized"
        
        result = {
            "capsule_name": capsule_name,
            "services": services,
            "initialized_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Capsule services initialized successfully: {result}")
        return result
    
    async def configure_capsule(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure capsule"""
        
        logger.info(f"Configuring capsule: {config}")
        
        capsule_name = config.get("capsule_name")
        services = config.get("services", {})
        capsule_config = config.get("config", {})
        
        # Apply configuration to services
        configured_services = {}
        
        for service_name, service_info in services.items():
            # Load service-specific configuration
            service_config = capsule_config.get("services", {}).get(service_name, {})
            
            # Apply configuration
            configured_service = {
                **service_info,
                "config": service_config,
                "status": "configured"
            }
            
            configured_services[service_name] = configured_service
        
        # Update capsule registry
        if capsule_name in self.capsule_registry:
            self.capsule_registry[capsule_name]["services"] = configured_services
            self.capsule_registry[capsule_name]["status"] = "configured"
        
        result = {
            "capsule_name": capsule_name,
            "configured_services": configured_services,
            "configured_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Capsule configured successfully: {result}")
        return result
    
    async def deploy_capsule(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy capsule"""
        
        logger.info(f"Deploying capsule: {config}")
        
        capsule_name = config.get("capsule_name")
        configuration = config.get("configuration", {})
        
        # Start services
        deployed_services = {}
        
        for service_name, service_info in configuration.get("configured_services", {}).items():
            # Simulate service deployment
            deployed_service = {
                **service_info,
                "status": "deployed",
                "deployment_id": f"deploy_{service_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "endpoint": f"http://localhost:{service_info['port']}"
            }
            
            deployed_services[service_name] = deployed_service
        
        # Update capsule registry
        if capsule_name in self.capsule_registry:
            self.capsule_registry[capsule_name]["services"] = deployed_services
            self.capsule_registry[capsule_name]["status"] = "deployed"
            self.capsule_registry[capsule_name]["deployed_at"] = datetime.utcnow().isoformat()
        
        result = {
            "capsule_name": capsule_name,
            "deployed_services": deployed_services,
            "deployment_status": "success",
            "deployed_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Capsule deployed successfully: {result}")
        return result