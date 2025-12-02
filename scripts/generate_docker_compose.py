"""
Docker Compose Generator for SomaAgentHub
Generates optimized docker-compose files for different deployment modes
"""

import os
from typing import Any

import yaml

from services.common.config.unified_config import DeploymentMode, config_manager


class DockerComposeGenerator:
    def __init__(self):
        self.config_manager = config_manager

    def generate_compose(self, deployment_mode: DeploymentMode) -> dict[str, Any]:
        os.environ["DEPLOYMENT_MODE"] = deployment_mode.value

        compose_config = {
            "version": "3.8",
            "services": {},
            "networks": {"somagenthub-network": {"driver": "bridge"}},
            "volumes": {
                "postgres_data": {},
                "redis_data": {},
                "temporal_data": {},
                "minio_data": {},
                "qdrant_data": {},
                "prometheus_data": {},
                "jaeger_data": {},
                "loki_data": {},
            },
        }

        compose_config["services"].update(self._generate_database_services())
        compose_config["services"].update(self._generate_application_services())
        compose_config["services"].update(self._generate_monitoring_services())

        return compose_config

    def _generate_database_services(self) -> dict[str, Any]:
        db_config = self.config_manager.get_database_config()
        services = {}

        services["database-cluster"] = {
            "image": "postgres:15",
            "container_name": "somagenthub_database",
            "environment": {
                "POSTGRES_USER": "somaagent",
                "POSTGRES_PASSWORD": "somaagent",
                "POSTGRES_DB": "somaagent",
                "POSTGRES_INITDB_ARGS": "--auth-host=scram-sha-256",
            },
            "ports": ["5432:5432"],
            "volumes": ["postgres_data:/var/lib/postgresql/data"],
            "networks": ["somagenthub-network"],
            "deploy": {
                "resources": {
                    "limits": {
                        "memory": db_config.memory_limit,
                        "cpus": db_config.cpu_limit,
                    }
                }
            },
            "healthcheck": {
                "test": ["CMD-SHELL", "pg_isready -U somaagent -d somaagent"],
                "interval": "10s",
                "timeout": "5s",
                "retries": 5,
            },
        }

        services["cache-cluster"] = {
            "image": "redis:7-alpine",
            "container_name": "somagenthub_cache",
            "command": ["redis-server", "--appendonly", "yes", "--maxmemory", "256mb"],
            "ports": ["6379:6379"],
            "volumes": ["redis_data:/data"],
            "networks": ["somagenthub-network"],
            "deploy": {"resources": {"limits": {"memory": "256Mi", "cpus": "0.5"}}},
            "healthcheck": {
                "test": ["CMD", "redis-cli", "ping"],
                "interval": "10s",
                "timeout": "5s",
                "retries": 5,
            },
        }

        return services

    def _generate_application_services(self) -> dict[str, Any]:
        services = {}

        for service_name in self.config_manager.get_enabled_services():
            service_config = self.config_manager.get_service_config(service_name)

            services[service_name] = {
                "build": {
                    "context": f"./services/{service_name}",
                    "dockerfile": "Dockerfile",
                },
                "container_name": f"somagenthub_{service_name}",
                "environment": service_config.environment,
                "ports": [f"{self._get_service_port(service_name)}:8000"],
                "networks": ["somagenthub-network"],
                "deploy": {
                    "replicas": service_config.replicas,
                    "resources": {
                        "limits": {
                            "memory": service_config.memory_limit,
                            "cpus": service_config.cpu_limit,
                        }
                    },
                },
                "depends_on": {
                    "database-cluster": {"condition": "service_healthy"},
                    "cache-cluster": {"condition": "service_healthy"},
                },
            }

        return services

    def _generate_monitoring_services(self) -> dict[str, Any]:
        monitoring_config = self.config_manager.get_monitoring_config()
        services = {}

        if monitoring_config.enabled:
            services["monitoring-stack"] = {
                "image": "prom/prometheus:latest",
                "container_name": "somagenthub_monitoring",
                "ports": ["9090:9090"],
                "volumes": ["./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml"],
                "networks": ["somagenthub-network"],
                "deploy": {"resources": {"limits": {"memory": "512Mi", "cpus": "500m"}}},
            }

        return services

    def _get_service_port(self, service_name: str) -> int:
        port_map = {
            "gateway-api": 10000,
            "workflow-engine": 10001,
            "ai-services": 10022,
            "capsule-manager": 10002,
            "data-services": 10003,
            "governance-services": 10004,
            "utility-services": 10005,
        }
        return port_map.get(service_name, 8000)

    def save_compose_file(self, deployment_mode: DeploymentMode, output_path: str):
        compose_config = self.generate_compose(deployment_mode)
        with open(output_path, "w") as f:
            yaml.dump(compose_config, f, default_flow_style=False)
