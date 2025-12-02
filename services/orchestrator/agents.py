"""
Kubernetes-native agent management module for SomaAgentHub.

This module provides functions to create and launch agent instances using
the Kubernetes Python client for both one-off Jobs and long-running Deployments.
"""

from __future__ import annotations

import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from kubernetes import client, config
from kubernetes.client import V1Job, V1Deployment, V1Container, V1PodTemplateSpec
from kubernetes.client.rest import ApiException

from .app.database import get_async_session
from .app.models.agent_instance import AgentInstance, AgentStatus
from .app.repository.agent_instance import AgentInstanceRepository

logger = logging.getLogger(__name__)


class AgentManagementError(Exception):
    """Raised when agent management operations fail."""
    # No additional functionality required; the exception type itself is
    # sufficient for callers to catch specific agent‑management errors.


    async def create_agent_instance(
    agent_type: str,
    capsule_id: Optional[uuid.UUID],
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    k8s_namespace: str,
    metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentInstance:
    """Create a new agent instance in the database.
    
    Args:
        agent_type: Type of agent (code_generator, ui_customizer, etc.)
        capsule_id: Associated capsule ID if applicable
        tenant_id: Tenant identifier
        user_id: User who initiated the agent
        k8s_namespace: Kubernetes namespace for the agent
        metadata: Additional metadata dictionary

    Returns:
        AgentInstance: The created agent instance record

    Raises:
        AgentManagementError: If database creation fails
    """
    try:
        async with get_async_session() as session:
    repo = AgentInstanceRepository(session)
    
    agent_instance = AgentInstance(
        agent_type=agent_type,
        capsule_id=capsule_id,
        tenant_id=tenant_id,
        user_id=user_id,
        status=AgentStatus.PENDING,
        k8s_namespace=k8s_namespace,
        meta=metadata or {},
        created_at=datetime.utcnow(),
    )
    
    created_agent = await repo.create_agent_instance(agent_instance)
    logger.info(f"Created agent instance {created_agent.id} of type {agent_type}")
    return created_agent
    
    except Exception as e:
        logger.error(f"Failed to create agent instance: {e}")
        raise AgentManagementError(f"Database creation failed: {e}")


        async def launch_agent_instance(
    agent_instance_id: uuid.UUID,
    agent_type: str,
    k8s_namespace: str,
    is_long_running: bool = False,
    container_image: str = "somaagent01:latest",
    resource_requests: Optional[Dict[str, str]] = None,
    resource_limits: Optional[Dict[str, str]] = None,
    env_vars: Optional[Dict[str, str]] = None,
    ) -> str:
    """Launch an agent instance on Kubernetes.
    
    Args:
        agent_instance_id: UUID of the agent instance
        agent_type: Type of agent for configuration
        k8s_namespace: Kubernetes namespace to deploy in
        is_long_running: Whether to create a Deployment (True) or Job (False)
        container_image: Container image to use
        resource_requests: Resource requests (cpu, memory)
        resource_limits: Resource limits (cpu, memory)
        env_vars: Environment variables for the container

    Returns:
        str: Name of the created Kubernetes resource

    Raises:
        AgentManagementError: If Kubernetes deployment fails
    """
    try:
# Load Kubernetes configuration
        config.load_incluster_config()
    except config.ConfigException:
        try:
    config.load_kube_config()
    except Exception as e:
    raise AgentManagementError(f"Failed to load Kubernetes config: {e}")
    
    # Create API clients
    batch_v1 = client.BatchV1Api()
    apps_v1 = client.AppsV1Api()
    
    # Generate resource name
    resource_name = f"agent-{agent_instance_id.hex[:8]}"
    
    # Prepare container spec
    container = V1Container(
    name="agent",
    image=container_image,
    env=[client.V1EnvVar(name=k, value=v) for k, v in (env_vars or {}).items()],
    resources=client.V1ResourceRequirements(
    requests=resource_requests or {"cpu": "100m", "memory": "128Mi"},
    limits=resource_limits or {"cpu": "500m", "memory": "512Mi"},
    ),
    )
    
    try:
        if is_long_running:
    # Create Deployment for long-running agents
    deployment = V1Deployment(
        metadata=client.V1ObjectMeta(
            name=resource_name,
            namespace=k8s_namespace,
            labels={
                "app": "soma-agent",
                "agent-type": agent_type,
                "agent-id": str(agent_instance_id),
            },
        ),
        spec=client.V1DeploymentSpec(
            replicas=1,
            selector=client.V1LabelSelector(
                match_labels={
                    "app": "soma-agent",
                    "agent-id": str(agent_instance_id),
                },
            ),
            template=V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(
                    labels={
                        "app": "soma-agent",
                        "agent-type": agent_type,
                        "agent-id": str(agent_instance_id),
                    },
                ),
                spec=client.V1PodSpec(
                    containers=[container],
                    restart_policy="Always",
                ),
            ),
        ),
    )
    
    apps_v1.create_namespaced_deployment(namespace=k8s_namespace, body=deployment)
    logger.info(f"Created deployment {resource_name} for agent {agent_instance_id}")
    
    else:
    # Create Job for one-off agents
    job = V1Job(
        metadata=client.V1ObjectMeta(
            name=resource_name,
            namespace=k8s_namespace,
            labels={
                "app": "soma-agent",
                "agent-type": agent_type,
                "agent-id": str(agent_instance_id),
            },
        ),
        spec=client.V1JobSpec(
            template=V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(
                    labels={
                        "app": "soma-agent",
                        "agent-type": agent_type,
                        "agent-id": str(agent_instance_id),
                    },
                ),
                spec=client.V1PodSpec(
                    containers=[container],
                    restart_policy="Never",
                ),
            ),
            backoff_limit=1,
        ),
    )
    
    batch_v1.create_namespaced_job(namespace=k8s_namespace, body=job)
    logger.info(f"Created job {resource_name} for agent {agent_instance_id}")

# Update agent instance with Kubernetes resource name
    await update_agent_k8s_info(
    agent_instance_id, 
    k8s_job_name=None if is_long_running else resource_name,
    k8s_deployment_name=resource_name if is_long_running else None
    )

    return resource_name

    except ApiException as e:
        logger.error(f"Kubernetes API error: {e}")
        raise AgentManagementError(f"Failed to create Kubernetes resource: {e}")
    except Exception as e:
        logger.error(f"Unexpected error launching agent: {e}")
        raise AgentManagementError(f"Failed to launch agent: {e}")


        async def update_agent_k8s_info(
    agent_instance_id: uuid.UUID,
    k8s_job_name: Optional[str] = None,
    k8s_deployment_name: Optional[str] = None,
    status: Optional[AgentStatus] = None,
    ) -> None:
    """Update agent instance with Kubernetes information.
    
    Args:
        agent_instance_id: UUID of the agent instance
        k8s_job_name: Kubernetes job name if applicable
        k8s_deployment_name: Kubernetes deployment name if applicable
        status: New status if provided
    """
    try:
        async with get_async_session() as session:
    repo = AgentInstanceRepository(session)
    
    update_data = {}
    if k8s_job_name:
        update_data["k8s_job_name"] = k8s_job_name
    if k8s_deployment_name:
        update_data["k8s_deployment_name"] = k8s_deployment_name
    if status:
        update_data["status"] = status
    
    await repo.update_agent_instance(agent_instance_id, update_data)
    logger.info(f"Updated agent {agent_instance_id} with K8s info: {update_data}")
    
    except Exception as e:
        logger.error(f"Failed to update agent K8s info: {e}")
        raise AgentManagementError(f"Database update failed: {e}")


        async def update_agent_status(
    agent_instance_id: uuid.UUID,
    status: AgentStatus,
    error_message: Optional[str] = None,
    ) -> None:
    """Update agent instance status.
    
    Args:
        agent_instance_id: UUID of the agent instance
        status: New agent status
        error_message: Error message if status is FAILED
    """
    try:
        async with get_async_session() as session:
    repo = AgentInstanceRepository(session)
    
    update_data = {
        "status": status,
        "updated_at": datetime.utcnow(),
    }
    
    if status == AgentStatus.RUNNING:
        update_data["started_at"] = datetime.utcnow()
    elif status in [AgentStatus.SUCCEEDED, AgentStatus.FAILED, AgentStatus.TERMINATED]:
        update_data["completed_at"] = datetime.utcnow()
        
    if error_message:
        update_data["error_message"] = error_message
    
    await repo.update_agent_instance(agent_instance_id, update_data)
    logger.info(f"Updated agent {agent_instance_id} status to {status}")
    
    except Exception as e:
        logger.error(f"Failed to update agent status: {e}")
        raise AgentManagementError(f"Database update failed: {e}")