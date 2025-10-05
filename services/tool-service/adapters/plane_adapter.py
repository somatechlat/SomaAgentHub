"""
⚠️ WE DO NOT MOCK - Real Plane.so API adapter.

Plane.so is a project management platform. This adapter provides:
- Project creation and management
- Issue tracking
- Sprint planning
- Team collaboration
"""

import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PlaneAdapter:
    """
    Adapter for Plane.so project management platform.
    
    API Documentation: https://docs.plane.so/api-reference
    """
    
    def __init__(self, api_token: str, workspace_slug: str, base_url: str = "https://api.plane.so"):
        self.api_token = api_token
        self.workspace_slug = workspace_slug
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated API request."""
        url = f"{self.base_url}/api/v1/{endpoint}"
        
        response = requests.request(
            method=method,
            url=url,
            headers=self.headers,
            timeout=30,
            **kwargs
        )
        
        response.raise_for_status()
        return response.json() if response.content else {}
    
    # Project Management
    
    def create_project(
        self,
        name: str,
        identifier: str,
        description: str = "",
        network: int = 2  # 2 = private, 0 = public
    ) -> Dict[str, Any]:
        """
        Create a new project in Plane.
        
        Args:
            name: Project name
            identifier: Short project identifier (e.g., 'SOMA')
            description: Project description
            network: Privacy level (0=public, 2=private)
            
        Returns:
            Created project data
        """
        logger.info(f"Creating Plane project: {name}")
        
        data = {
            "name": name,
            "identifier": identifier,
            "description": description,
            "network": network,
        }
        
        return self._request(
            "POST",
            f"workspaces/{self.workspace_slug}/projects/",
            json=data
        )
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get project details."""
        return self._request(
            "GET",
            f"workspaces/{self.workspace_slug}/projects/{project_id}/"
        )
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects in workspace."""
        return self._request(
            "GET",
            f"workspaces/{self.workspace_slug}/projects/"
        )
    
    # Issue Management
    
    def create_issue(
        self,
        project_id: str,
        name: str,
        description: str = "",
        priority: str = "medium",
        state: Optional[str] = None,
        assignees: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new issue.
        
        Args:
            project_id: Project ID
            name: Issue title
            description: Issue description
            priority: Priority (low, medium, high, urgent)
            state: State ID (optional)
            assignees: List of user IDs
            labels: List of label IDs
            
        Returns:
            Created issue data
        """
        logger.info(f"Creating issue: {name}")
        
        data = {
            "name": name,
            "description": description,
            "priority": priority,
        }
        
        if state:
            data["state"] = state
        if assignees:
            data["assignees"] = assignees
        if labels:
            data["labels"] = labels
        
        return self._request(
            "POST",
            f"workspaces/{self.workspace_slug}/projects/{project_id}/issues/",
            json=data
        )
    
    def update_issue(
        self,
        project_id: str,
        issue_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Update an existing issue."""
        return self._request(
            "PATCH",
            f"workspaces/{self.workspace_slug}/projects/{project_id}/issues/{issue_id}/",
            json=kwargs
        )
    
    def get_issue(self, project_id: str, issue_id: str) -> Dict[str, Any]:
        """Get issue details."""
        return self._request(
            "GET",
            f"workspaces/{self.workspace_slug}/projects/{project_id}/issues/{issue_id}/"
        )
    
    def list_issues(
        self,
        project_id: str,
        state: Optional[str] = None,
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List issues with filters.
        
        Args:
            project_id: Project ID
            state: Filter by state
            priority: Filter by priority
            assignee: Filter by assignee
            
        Returns:
            List of issues
        """
        params = {}
        if state:
            params["state"] = state
        if priority:
            params["priority"] = priority
        if assignee:
            params["assignee"] = assignee
        
        return self._request(
            "GET",
            f"workspaces/{self.workspace_slug}/projects/{project_id}/issues/",
            params=params
        )
    
    # Cycle/Sprint Management
    
    def create_cycle(
        self,
        project_id: str,
        name: str,
        start_date: str,
        end_date: str,
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Create a sprint cycle.
        
        Args:
            project_id: Project ID
            name: Cycle name (e.g., "Sprint 1")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            description: Cycle description
            
        Returns:
            Created cycle data
        """
        logger.info(f"Creating cycle: {name}")
        
        data = {
            "name": name,
            "start_date": start_date,
            "end_date": end_date,
            "description": description,
        }
        
        return self._request(
            "POST",
            f"workspaces/{self.workspace_slug}/projects/{project_id}/cycles/",
            json=data
        )
    
    def add_issue_to_cycle(
        self,
        project_id: str,
        cycle_id: str,
        issue_id: str
    ) -> Dict[str, Any]:
        """Add an issue to a cycle."""
        return self._request(
            "POST",
            f"workspaces/{self.workspace_slug}/projects/{project_id}/cycles/{cycle_id}/cycle-issues/",
            json={"issue": issue_id}
        )
    
    # Module Management
    
    def create_module(
        self,
        project_id: str,
        name: str,
        description: str = "",
        start_date: Optional[str] = None,
        target_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a module (feature grouping).
        
        Args:
            project_id: Project ID
            name: Module name
            description: Module description
            start_date: Start date (YYYY-MM-DD)
            target_date: Target completion date (YYYY-MM-DD)
            
        Returns:
            Created module data
        """
        logger.info(f"Creating module: {name}")
        
        data = {
            "name": name,
            "description": description,
        }
        
        if start_date:
            data["start_date"] = start_date
        if target_date:
            data["target_date"] = target_date
        
        return self._request(
            "POST",
            f"workspaces/{self.workspace_slug}/projects/{project_id}/modules/",
            json=data
        )
    
    # State Management
    
    def list_states(self, project_id: str) -> List[Dict[str, Any]]:
        """List all workflow states."""
        return self._request(
            "GET",
            f"workspaces/{self.workspace_slug}/projects/{project_id}/states/"
        )
    
    def create_state(
        self,
        project_id: str,
        name: str,
        group: str = "backlog",  # backlog, unstarted, started, completed, cancelled
        color: str = "#3f76ff"
    ) -> Dict[str, Any]:
        """Create a custom workflow state."""
        data = {
            "name": name,
            "group": group,
            "color": color,
        }
        
        return self._request(
            "POST",
            f"workspaces/{self.workspace_slug}/projects/{project_id}/states/",
            json=data
        )
    
    # Label Management
    
    def create_label(
        self,
        project_id: str,
        name: str,
        color: str = "#3f76ff"
    ) -> Dict[str, Any]:
        """Create an issue label."""
        data = {
            "name": name,
            "color": color,
        }
        
        return self._request(
            "POST",
            f"workspaces/{self.workspace_slug}/projects/{project_id}/issue-labels/",
            json=data
        )
    
    def list_labels(self, project_id: str) -> List[Dict[str, Any]]:
        """List all labels."""
        return self._request(
            "GET",
            f"workspaces/{self.workspace_slug}/projects/{project_id}/issue-labels/"
        )
    
    # Team Management
    
    def list_workspace_members(self) -> List[Dict[str, Any]]:
        """List workspace members."""
        return self._request(
            "GET",
            f"workspaces/{self.workspace_slug}/members/"
        )
    
    def invite_member(self, email: str, role: int = 10) -> Dict[str, Any]:
        """
        Invite member to workspace.
        
        Args:
            email: Member email
            role: Role level (5=guest, 10=member, 15=admin, 20=owner)
            
        Returns:
            Invitation data
        """
        data = {
            "email": email,
            "role": role,
        }
        
        return self._request(
            "POST",
            f"workspaces/{self.workspace_slug}/invitations/",
            json=data
        )
    
    # Analytics
    
    def get_project_analytics(self, project_id: str) -> Dict[str, Any]:
        """Get project analytics and metrics."""
        return self._request(
            "GET",
            f"workspaces/{self.workspace_slug}/projects/{project_id}/analytics/"
        )
    
    # Utility Methods
    
    def bulk_create_issues(
        self,
        project_id: str,
        issues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Bulk create multiple issues.
        
        Args:
            project_id: Project ID
            issues: List of issue data dictionaries
            
        Returns:
            List of created issues
        """
        logger.info(f"Bulk creating {len(issues)} issues")
        
        created_issues = []
        for issue_data in issues:
            try:
                created = self.create_issue(project_id, **issue_data)
                created_issues.append(created)
            except Exception as e:
                logger.error(f"Failed to create issue {issue_data.get('name')}: {e}")
        
        return created_issues
    
    def setup_project_from_template(
        self,
        name: str,
        identifier: str,
        template: str = "agile"
    ) -> Dict[str, Any]:
        """
        Setup project from template with default states and labels.
        
        Args:
            name: Project name
            identifier: Project identifier
            template: Template type (agile, kanban, scrum)
            
        Returns:
            Project setup data
        """
        logger.info(f"Setting up project from {template} template")
        
        # Create project
        project = self.create_project(name, identifier)
        project_id = project["id"]
        
        # Create default labels based on template
        if template == "agile":
            labels = [
                {"name": "bug", "color": "#ef4444"},
                {"name": "feature", "color": "#3b82f6"},
                {"name": "enhancement", "color": "#8b5cf6"},
                {"name": "documentation", "color": "#10b981"},
                {"name": "technical-debt", "color": "#f59e0b"},
            ]
            
            for label_data in labels:
                try:
                    self.create_label(project_id, **label_data)
                except Exception as e:
                    logger.warning(f"Failed to create label: {e}")
        
        return {
            "project": project,
            "project_id": project_id,
            "template": template,
        }
