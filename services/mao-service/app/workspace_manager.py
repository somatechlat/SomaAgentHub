"""
⚠️ WE DO NOT MOCK - Real workspace manager for VSCode dev containers.
"""

import docker
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class WorkspaceInfo:
    """Information about a workspace."""
    workspace_id: str
    container_id: str
    volume_name: str
    host_port: str
    vscode_url: str
    status: str
    created_at: float


class WorkspaceManager:
    """
    Manages VSCode dev container workspaces.
    
    Features:
    - Create isolated VSCode environments
    - Provision with Git repos
    - Manage lifecycle (start, stop, cleanup)
    - Resource limits enforcement
    """
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.workspaces: Dict[str, WorkspaceInfo] = {}
    
    async def create_workspace(
        self,
        workspace_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> WorkspaceInfo:
        """
        Create a new VSCode workspace.
        
        Args:
            workspace_id: Unique identifier for workspace
            config: Optional configuration (image, resources, env vars)
            
        Returns:
            WorkspaceInfo with connection details
        """
        config = config or {}
        
        # Default configuration
        image = config.get("vscode_image", "codercom/code-server:latest")
        cpu_limit = config.get("cpu_limit", "2")
        memory_limit = config.get("memory_limit", "4g")
        
        logger.info(f"Creating workspace: {workspace_id}")
        
        try:
            # Create volume
            volume = self.docker_client.volumes.create(
                name=f"{workspace_id}-data",
                labels={
                    "workspace_id": workspace_id,
                    "managed_by": "mao-workspace-manager",
                }
            )
            
            # Launch container
            container = self.docker_client.containers.run(
                image=image,
                name=workspace_id,
                detach=True,
                cpu_quota=int(float(cpu_limit) * 100000),
                mem_limit=memory_limit,
                volumes={
                    volume.name: {"bind": "/home/coder/project", "mode": "rw"}
                },
                environment={
                    "PASSWORD": "somagent",
                    "WORKSPACE_ID": workspace_id,
                    **config.get("environment", {})
                },
                labels={
                    "workspace_id": workspace_id,
                    "service": "mao-workspace",
                },
                ports={"8080/tcp": None},  # Auto-assign port
                restart_policy={"Name": "unless-stopped"},
            )
            
            # Wait for container to be ready
            for _ in range(30):
                container.reload()
                if container.status == "running":
                    break
                await asyncio.sleep(1)
            
            # Get port binding
            container.reload()
            port_bindings = container.ports.get("8080/tcp", [])
            host_port = port_bindings[0]["HostPort"] if port_bindings else "unknown"
            
            # Create workspace info
            import time
            workspace_info = WorkspaceInfo(
                workspace_id=workspace_id,
                container_id=container.id,
                volume_name=volume.name,
                host_port=host_port,
                vscode_url=f"http://localhost:{host_port}",
                status="running",
                created_at=time.time(),
            )
            
            self.workspaces[workspace_id] = workspace_info
            
            logger.info(
                f"Workspace created: {workspace_id} at {workspace_info.vscode_url}"
            )
            
            return workspace_info
            
        except Exception as e:
            logger.error(f"Failed to create workspace: {e}")
            raise
    
    async def provision_git_repo(
        self,
        workspace_id: str,
        repo_url: str,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Clone Git repository into workspace.
        
        Args:
            workspace_id: Workspace identifier
            repo_url: Git repository URL
            branch: Branch to checkout (default: main)
            
        Returns:
            Repository metadata (latest commit, author, etc.)
        """
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")
        
        logger.info(f"Provisioning Git repo in {workspace_id}: {repo_url}")
        
        try:
            container = self.docker_client.containers.get(workspace.container_id)
            
            # Clone repository
            exec_result = container.exec_run(
                cmd=f"git clone -b {branch} {repo_url} /home/coder/project/repo",
                user="coder",
                workdir="/home/coder/project",
            )
            
            if exec_result.exit_code != 0:
                raise RuntimeError(
                    f"Git clone failed: {exec_result.output.decode()}"
                )
            
            # Get commit info
            exec_result = container.exec_run(
                cmd="git log -1 --format='%H|%an|%ae|%s'",
                user="coder",
                workdir="/home/coder/project/repo",
            )
            
            commit_info = exec_result.output.decode().strip().split("|")
            
            logger.info(f"Repository provisioned: {repo_url}")
            
            return {
                "repo_url": repo_url,
                "branch": branch,
                "commit_hash": commit_info[0] if len(commit_info) > 0 else None,
                "author_name": commit_info[1] if len(commit_info) > 1 else None,
                "author_email": commit_info[2] if len(commit_info) > 2 else None,
                "commit_message": commit_info[3] if len(commit_info) > 3 else None,
            }
            
        except Exception as e:
            logger.error(f"Failed to provision Git repo: {e}")
            raise
    
    async def execute_command(
        self,
        workspace_id: str,
        command: str,
        workdir: str = "/home/coder/project"
    ) -> Dict[str, Any]:
        """
        Execute a command in the workspace container.
        
        Args:
            workspace_id: Workspace identifier
            command: Command to execute
            workdir: Working directory
            
        Returns:
            Command output and exit code
        """
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")
        
        try:
            container = self.docker_client.containers.get(workspace.container_id)
            
            exec_result = container.exec_run(
                cmd=command,
                user="coder",
                workdir=workdir,
            )
            
            return {
                "exit_code": exec_result.exit_code,
                "output": exec_result.output.decode(),
                "success": exec_result.exit_code == 0,
            }
            
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            raise
    
    async def stop_workspace(self, workspace_id: str) -> None:
        """Stop a workspace container."""
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")
        
        try:
            container = self.docker_client.containers.get(workspace.container_id)
            container.stop(timeout=30)
            workspace.status = "stopped"
            logger.info(f"Workspace stopped: {workspace_id}")
        except Exception as e:
            logger.error(f"Failed to stop workspace: {e}")
            raise
    
    async def cleanup_workspace(self, workspace_id: str) -> None:
        """
        Cleanup workspace resources.
        
        Removes container and volume.
        """
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")
        
        logger.info(f"Cleaning up workspace: {workspace_id}")
        
        try:
            # Remove container
            try:
                container = self.docker_client.containers.get(workspace.container_id)
                container.stop(timeout=10)
                container.remove()
            except docker.errors.NotFound:
                logger.warning("Container already removed")
            
            # Remove volume
            try:
                volume = self.docker_client.volumes.get(workspace.volume_name)
                volume.remove()
            except docker.errors.NotFound:
                logger.warning("Volume already removed")
            
            # Remove from tracking
            del self.workspaces[workspace_id]
            
            logger.info(f"Workspace cleaned up: {workspace_id}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup workspace: {e}")
            raise
    
    def get_workspace(self, workspace_id: str) -> Optional[WorkspaceInfo]:
        """Get workspace information."""
        return self.workspaces.get(workspace_id)
    
    def list_workspaces(self) -> Dict[str, WorkspaceInfo]:
        """List all managed workspaces."""
        return self.workspaces.copy()
