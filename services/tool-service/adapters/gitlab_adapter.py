"""
⚠️ WE DO NOT MOCK - Real GitLab API integration.

GitLab Adapter for Repository and CI/CD Management
Comprehensive GitLab integration using REST API v4.
"""

import requests
from typing import Dict, Any, List, Optional
import base64
import logging

logger = logging.getLogger(__name__)


class GitLabAdapter:
    """
    GitLab adapter for repository, CI/CD, and project management.
    
    API documentation: https://docs.gitlab.com/ee/api/api_resources.html
    """
    
    def __init__(self, url: str = "https://gitlab.com", token: str = None):
        """
        Initialize GitLab adapter.
        
        Args:
            url: GitLab instance URL (default: gitlab.com)
            token: Personal access token or OAuth token
        """
        self.base_url = f"{url}/api/v4"
        self.headers = {"PRIVATE-TOKEN": token} if token else {}
        logger.info(f"GitLab adapter initialized for {url}")
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make API request."""
        url = f"{self.base_url}/{endpoint}"
        response = requests.request(method, url, headers=self.headers, timeout=30, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else {}
    
    # ============================================================================
    # PROJECTS
    # ============================================================================
    
    def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        visibility: str = "private",
        initialize_with_readme: bool = True,
        namespace_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new project."""
        data = {
            "name": name,
            "visibility": visibility,
            "initialize_with_readme": initialize_with_readme
        }
        if description:
            data["description"] = description
        if namespace_id:
            data["namespace_id"] = namespace_id
        
        project = self._request("POST", "projects", json=data)
        logger.info(f"Created project: {project['path_with_namespace']}")
        return project
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get project by ID or path."""
        # URL-encode project path
        encoded_id = requests.utils.quote(project_id, safe='')
        return self._request("GET", f"projects/{encoded_id}")
    
    def list_projects(self, owned: bool = True, limit: int = 20) -> List[Dict[str, Any]]:
        """List projects."""
        params = {"per_page": limit}
        if owned:
            params["owned"] = "true"
        return self._request("GET", "projects", params=params)
    
    def delete_project(self, project_id: str):
        """Delete a project."""
        encoded_id = requests.utils.quote(project_id, safe='')
        self._request("DELETE", f"projects/{encoded_id}")
        logger.info(f"Deleted project: {project_id}")
    
    # ============================================================================
    # REPOSITORY FILES
    # ============================================================================
    
    def create_file(
        self,
        project_id: str,
        file_path: str,
        content: str,
        commit_message: str,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """Create a new file in repository."""
        encoded_id = requests.utils.quote(project_id, safe='')
        encoded_path = requests.utils.quote(file_path, safe='')
        
        data = {
            "branch": branch,
            "content": content,
            "commit_message": commit_message
        }
        
        return self._request("POST", f"projects/{encoded_id}/repository/files/{encoded_path}", json=data)
    
    def get_file(self, project_id: str, file_path: str, ref: str = "main") -> Dict[str, Any]:
        """Get file content from repository."""
        encoded_id = requests.utils.quote(project_id, safe='')
        encoded_path = requests.utils.quote(file_path, safe='')
        
        file_data = self._request("GET", f"projects/{encoded_id}/repository/files/{encoded_path}", params={"ref": ref})
        
        # Decode base64 content
        if "content" in file_data:
            file_data["content_decoded"] = base64.b64decode(file_data["content"]).decode('utf-8')
        
        return file_data
    
    def update_file(
        self,
        project_id: str,
        file_path: str,
        content: str,
        commit_message: str,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """Update existing file."""
        encoded_id = requests.utils.quote(project_id, safe='')
        encoded_path = requests.utils.quote(file_path, safe='')
        
        data = {
            "branch": branch,
            "content": content,
            "commit_message": commit_message
        }
        
        return self._request("PUT", f"projects/{encoded_id}/repository/files/{encoded_path}", json=data)
    
    # ============================================================================
    # BRANCHES
    # ============================================================================
    
    def create_branch(self, project_id: str, branch_name: str, ref: str = "main") -> Dict[str, Any]:
        """Create a new branch."""
        encoded_id = requests.utils.quote(project_id, safe='')
        data = {"branch": branch_name, "ref": ref}
        return self._request("POST", f"projects/{encoded_id}/repository/branches", json=data)
    
    def list_branches(self, project_id: str) -> List[Dict[str, Any]]:
        """List repository branches."""
        encoded_id = requests.utils.quote(project_id, safe='')
        return self._request("GET", f"projects/{encoded_id}/repository/branches")
    
    def protect_branch(self, project_id: str, branch_name: str) -> Dict[str, Any]:
        """Protect a branch."""
        encoded_id = requests.utils.quote(project_id, safe='')
        encoded_branch = requests.utils.quote(branch_name, safe='')
        return self._request("POST", f"projects/{encoded_id}/protected_branches", 
                           json={"name": branch_name})
    
    # ============================================================================
    # MERGE REQUESTS
    # ============================================================================
    
    def create_merge_request(
        self,
        project_id: str,
        source_branch: str,
        target_branch: str,
        title: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a merge request."""
        encoded_id = requests.utils.quote(project_id, safe='')
        
        data = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title
        }
        if description:
            data["description"] = description
        
        mr = self._request("POST", f"projects/{encoded_id}/merge_requests", json=data)
        logger.info(f"Created MR: !{mr['iid']}")
        return mr
    
    def merge_merge_request(self, project_id: str, mr_iid: int) -> Dict[str, Any]:
        """Merge a merge request."""
        encoded_id = requests.utils.quote(project_id, safe='')
        return self._request("PUT", f"projects/{encoded_id}/merge_requests/{mr_iid}/merge")
    
    def list_merge_requests(
        self,
        project_id: str,
        state: str = "opened"
    ) -> List[Dict[str, Any]]:
        """List merge requests."""
        encoded_id = requests.utils.quote(project_id, safe='')
        return self._request("GET", f"projects/{encoded_id}/merge_requests", params={"state": state})
    
    # ============================================================================
    # CI/CD PIPELINES
    # ============================================================================
    
    def create_pipeline(self, project_id: str, ref: str = "main") -> Dict[str, Any]:
        """Trigger a new pipeline."""
        encoded_id = requests.utils.quote(project_id, safe='')
        pipeline = self._request("POST", f"projects/{encoded_id}/pipeline", json={"ref": ref})
        logger.info(f"Triggered pipeline #{pipeline['id']}")
        return pipeline
    
    def get_pipeline(self, project_id: str, pipeline_id: int) -> Dict[str, Any]:
        """Get pipeline details."""
        encoded_id = requests.utils.quote(project_id, safe='')
        return self._request("GET", f"projects/{encoded_id}/pipelines/{pipeline_id}")
    
    def list_pipelines(self, project_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """List pipelines."""
        encoded_id = requests.utils.quote(project_id, safe='')
        return self._request("GET", f"projects/{encoded_id}/pipelines", params={"per_page": limit})
    
    def get_pipeline_jobs(self, project_id: str, pipeline_id: int) -> List[Dict[str, Any]]:
        """Get jobs in a pipeline."""
        encoded_id = requests.utils.quote(project_id, safe='')
        return self._request("GET", f"projects/{encoded_id}/pipelines/{pipeline_id}/jobs")
    
    # ============================================================================
    # ISSUES
    # ============================================================================
    
    def create_issue(
        self,
        project_id: str,
        title: str,
        description: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignee_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Create an issue."""
        encoded_id = requests.utils.quote(project_id, safe='')
        
        data = {"title": title}
        if description:
            data["description"] = description
        if labels:
            data["labels"] = ",".join(labels)
        if assignee_ids:
            data["assignee_ids"] = assignee_ids
        
        issue = self._request("POST", f"projects/{encoded_id}/issues", json=data)
        logger.info(f"Created issue #{issue['iid']}")
        return issue
    
    def list_issues(self, project_id: str, state: str = "opened") -> List[Dict[str, Any]]:
        """List issues."""
        encoded_id = requests.utils.quote(project_id, safe='')
        return self._request("GET", f"projects/{encoded_id}/issues", params={"state": state})
    
    # ============================================================================
    # USERS
    # ============================================================================
    
    def get_current_user(self) -> Dict[str, Any]:
        """Get authenticated user information."""
        return self._request("GET", "user")
    
    def list_users(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List users."""
        return self._request("GET", "users", params={"per_page": limit})
    
    # ============================================================================
    # UTILITIES
    # ============================================================================
    
    def bootstrap_repository(
        self,
        name: str,
        description: str,
        ci_config: Optional[str] = None
    ) -> Dict[str, Any]:
        """Bootstrap a complete GitLab repository with CI/CD."""
        # Create project
        project = self.create_project(
            name=name,
            description=description,
            initialize_with_readme=True
        )
        
        project_id = project["id"]
        
        # Add CI config if provided
        if ci_config:
            self.create_file(
                project_id=str(project_id),
                file_path=".gitlab-ci.yml",
                content=ci_config,
                commit_message="Add CI/CD configuration"
            )
        
        # Protect main branch
        self.protect_branch(str(project_id), "main")
        
        logger.info(f"Bootstrapped repository: {project['path_with_namespace']}")
        
        return {
            "project": project,
            "ci_configured": ci_config is not None
        }
