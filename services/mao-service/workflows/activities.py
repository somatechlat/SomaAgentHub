"""
⚠️ WE DO NOT MOCK - Real Temporal activity implementations.
"""

import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from temporalio import activity
import docker
import boto3
import requests
from git import Repo


@dataclass
class WorkspaceConfig:
    """Configuration for workspace creation."""
    vscode_image: str = "codercom/code-server:latest"
    cpu_limit: str = "2"
    memory_limit: str = "4g"
    volumes: Dict[str, str] = None
    environment: Dict[str, str] = None


@activity.defn
async def create_workspace(config: Dict[str, Any]) -> str:
    """
    Create a VSCode dev container workspace.
    
    Returns:
        workspace_id: Unique identifier for the created workspace
    """
    workspace_id = f"workspace-{uuid.uuid4().hex[:8]}"
    
    activity.logger.info(f"Creating workspace: {workspace_id}")
    
    try:
        # Initialize Docker client
        client = docker.from_env()
        
        # Prepare workspace configuration
        workspace_config = WorkspaceConfig(**(config or {}))
        
        # Create volume for workspace data
        volume = client.volumes.create(
            name=f"{workspace_id}-data",
            labels={
                "workspace_id": workspace_id,
                "created_by": "mao-service",
            }
        )
        
        activity.logger.info(f"Created volume: {volume.name}")
        
        # Launch VSCode container
        container = client.containers.run(
            image=workspace_config.vscode_image,
            name=workspace_id,
            detach=True,
            cpu_quota=int(float(workspace_config.cpu_limit) * 100000),
            mem_limit=workspace_config.memory_limit,
            volumes={
                volume.name: {"bind": "/home/coder/project", "mode": "rw"},
                **(workspace_config.volumes or {})
            },
            environment={
                "PASSWORD": "somagent",
                "WORKSPACE_ID": workspace_id,
                **(workspace_config.environment or {})
            },
            labels={
                "workspace_id": workspace_id,
                "service": "mao-workspace",
            },
            ports={"8080/tcp": None},  # Auto-assign port
            restart_policy={"Name": "unless-stopped"},
        )
        
        activity.logger.info(f"Container started: {container.id[:12]}")
        
        # Wait for container to be ready
        for _ in range(30):
            container.reload()
            if container.status == "running":
                break
            await asyncio.sleep(1)
        
        # Get assigned port
        container.reload()
        port_bindings = container.ports.get("8080/tcp", [])
        host_port = port_bindings[0]["HostPort"] if port_bindings else None
        
        activity.logger.info(
            f"Workspace ready: {workspace_id} on port {host_port}"
        )
        
        # Store workspace metadata
        await _store_workspace_metadata(workspace_id, {
            "container_id": container.id,
            "volume_name": volume.name,
            "host_port": host_port,
            "status": "running",
            "created_at": time.time(),
        })
        
        return workspace_id
        
    except Exception as e:
        activity.logger.error(f"Failed to create workspace: {e}")
        raise


@activity.defn
async def provision_git_repo(workspace_id: str, repo_url: str) -> Dict[str, Any]:
    """
    Clone Git repository into workspace.
    
    Args:
        workspace_id: ID of the workspace
        repo_url: Git repository URL to clone
        
    Returns:
        Repository metadata
    """
    activity.logger.info(f"Provisioning Git repo: {repo_url}")
    
    try:
        # Get workspace metadata
        metadata = await _get_workspace_metadata(workspace_id)
        container_id = metadata["container_id"]
        
        # Initialize Docker client
        client = docker.from_env()
        container = client.containers.get(container_id)
        
        # Execute git clone inside container
        exec_result = container.exec_run(
            cmd=f"git clone {repo_url} /home/coder/project/repo",
            user="coder",
            workdir="/home/coder/project",
        )
        
        if exec_result.exit_code != 0:
            raise RuntimeError(
                f"Git clone failed: {exec_result.output.decode()}"
            )
        
        activity.logger.info(f"Repository cloned successfully")
        
        # Get repository info
        exec_result = container.exec_run(
            cmd="git log -1 --format='%H|%an|%s'",
            user="coder",
            workdir="/home/coder/project/repo",
        )
        
        commit_info = exec_result.output.decode().strip().split("|")
        
        return {
            "repo_url": repo_url,
            "latest_commit": commit_info[0] if len(commit_info) > 0 else None,
            "author": commit_info[1] if len(commit_info) > 1 else None,
            "message": commit_info[2] if len(commit_info) > 2 else None,
        }
        
    except Exception as e:
        activity.logger.error(f"Failed to provision Git repo: {e}")
        raise


@activity.defn
async def execute_capsule(task_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a Task Capsule within the workspace.
    
    Args:
        task_config: Configuration for the task including capsule_id, persona_id
        
    Returns:
        Execution result with output and artifacts
    """
    task_id = task_config["task_id"]
    capsule_id = task_config["capsule_id"]
    workspace_id = task_config["workspace_id"]
    
    activity.logger.info(f"Executing capsule {capsule_id} for task {task_id}")
    
    start_time = time.time()
    
    try:
        # Get workspace metadata
        metadata = await _get_workspace_metadata(workspace_id)
        
        # Call capsule execution API
        response = requests.post(
            f"{os.getenv('TASK_CAPSULE_REPO_URL', 'http://task-capsule-repo:8000')}/v1/capsules/execute",
            json={
                "capsule_id": capsule_id,
                "persona_id": task_config.get("persona_id"),
                "workspace_id": workspace_id,
                "description": task_config.get("description"),
                "metadata": task_config.get("metadata", {}),
            },
            timeout=task_config.get("timeout_seconds", 3600),
        )
        
        response.raise_for_status()
        result = response.json()
        
        execution_time = time.time() - start_time
        
        activity.logger.info(
            f"Capsule execution completed in {execution_time:.2f}s"
        )
        
        return {
            "output": result.get("output", {}),
            "artifacts": result.get("artifacts", []),
            "execution_time": execution_time,
            "logs": result.get("logs", []),
        }
        
    except Exception as e:
        activity.logger.error(f"Capsule execution failed: {e}")
        raise


@activity.defn
async def bundle_artifacts(
    workspace_id: str,
    storage_url: str,
    task_results: List[Dict[str, Any]]
) -> List[str]:
    """
    Bundle and upload artifacts to storage.
    
    Args:
        workspace_id: ID of the workspace
        storage_url: S3 or storage URL (e.g., s3://bucket/path)
        task_results: Results from all tasks
        
    Returns:
        List of artifact URLs
    """
    activity.logger.info(f"Bundling artifacts for workspace {workspace_id}")
    
    try:
        # Extract all artifact paths
        all_artifacts = []
        for result in task_results:
            all_artifacts.extend(result.get("artifacts", []))
        
        if not all_artifacts:
            activity.logger.info("No artifacts to bundle")
            return []
        
        # Initialize S3 client
        s3_client = boto3.client("s3")
        
        # Parse storage URL
        if storage_url.startswith("s3://"):
            bucket_path = storage_url[5:].split("/", 1)
            bucket = bucket_path[0]
            prefix = bucket_path[1] if len(bucket_path) > 1 else ""
        else:
            raise ValueError(f"Unsupported storage URL: {storage_url}")
        
        # Get workspace metadata
        metadata = await _get_workspace_metadata(workspace_id)
        container_id = metadata["container_id"]
        
        # Initialize Docker client
        client = docker.from_env()
        container = client.containers.get(container_id)
        
        uploaded_urls = []
        
        # Upload each artifact
        for artifact_path in all_artifacts:
            # Get artifact from container
            bits, stat = container.get_archive(artifact_path)
            
            # Construct S3 key
            artifact_name = artifact_path.split("/")[-1]
            s3_key = f"{prefix}/{workspace_id}/{artifact_name}"
            
            # Upload to S3
            s3_client.upload_fileobj(
                bits,
                bucket,
                s3_key,
                ExtraArgs={"ServerSideEncryption": "AES256"}
            )
            
            url = f"s3://{bucket}/{s3_key}"
            uploaded_urls.append(url)
            
            activity.logger.info(f"Uploaded artifact: {url}")
        
        return uploaded_urls
        
    except Exception as e:
        activity.logger.error(f"Failed to bundle artifacts: {e}")
        raise


@activity.defn
async def notify_completion(
    webhook_urls: List[str],
    payload: Dict[str, Any]
) -> None:
    """
    Notify webhooks about workflow completion.
    
    Args:
        webhook_urls: List of webhook URLs to notify
        payload: Notification payload
    """
    activity.logger.info(f"Notifying {len(webhook_urls)} webhooks")
    
    for url in webhook_urls:
        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            response.raise_for_status()
            activity.logger.info(f"Notified webhook: {url}")
        except Exception as e:
            activity.logger.error(f"Failed to notify {url}: {e}")
            # Continue with other webhooks even if one fails


@activity.defn
async def cleanup_workspace(workspace_id: str) -> None:
    """
    Cleanup workspace resources.
    
    Args:
        workspace_id: ID of the workspace to cleanup
    """
    activity.logger.info(f"Cleaning up workspace: {workspace_id}")
    
    try:
        # Get workspace metadata
        metadata = await _get_workspace_metadata(workspace_id)
        
        # Initialize Docker client
        client = docker.from_env()
        
        # Stop and remove container
        try:
            container = client.containers.get(metadata["container_id"])
            container.stop(timeout=30)
            container.remove()
            activity.logger.info(f"Container removed: {metadata['container_id']}")
        except docker.errors.NotFound:
            activity.logger.warning("Container already removed")
        
        # Remove volume
        try:
            volume = client.volumes.get(metadata["volume_name"])
            volume.remove()
            activity.logger.info(f"Volume removed: {metadata['volume_name']}")
        except docker.errors.NotFound:
            activity.logger.warning("Volume already removed")
        
        # Clean up metadata
        await _delete_workspace_metadata(workspace_id)
        
        activity.logger.info(f"Workspace cleanup completed: {workspace_id}")
        
    except Exception as e:
        activity.logger.error(f"Failed to cleanup workspace: {e}")
        raise


# Helper functions for workspace metadata storage (using Redis)

async def _store_workspace_metadata(
    workspace_id: str,
    metadata: Dict[str, Any]
) -> None:
    """Store workspace metadata in Redis."""
    import redis.asyncio as redis
    import os
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    client = redis.from_url(redis_url)
    try:
        await client.hset(
            f"workspace:{workspace_id}",
            mapping={k: str(v) for k, v in metadata.items()}
        )
        await client.expire(f"workspace:{workspace_id}", 86400 * 7)  # 7 days
    finally:
        await client.close()


async def _get_workspace_metadata(workspace_id: str) -> Dict[str, Any]:
    """Retrieve workspace metadata from Redis."""
    import redis.asyncio as redis
    import os
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    client = redis.from_url(redis_url)
    try:
        data = await client.hgetall(f"workspace:{workspace_id}")
        if not data:
            raise ValueError(f"Workspace not found: {workspace_id}")
        return {k.decode(): v.decode() for k, v in data.items()}
    finally:
        await client.close()


async def _delete_workspace_metadata(workspace_id: str) -> None:
    """Delete workspace metadata from Redis."""
    import redis.asyncio as redis
    import os
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    client = redis.from_url(redis_url)
    try:
        await client.delete(f"workspace:{workspace_id}")
    finally:
        await client.close()
