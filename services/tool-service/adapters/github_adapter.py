"""
⚠️ WE DO NOT MOCK - Real GitHub API adapter.

Provides comprehensive GitHub integration:
- Repository management
- Issues and pull requests
- Actions workflows
- Project boards
- Team management
"""

import requests
from typing import Dict, List, Any, Optional
import base64
import logging

logger = logging.getLogger(__name__)


class GitHubAdapter:
    """
    Adapter for GitHub API.
    
    API Documentation: https://docs.github.com/en/rest
    """
    
    def __init__(self, access_token: str, base_url: str = "https://api.github.com"):
        self.access_token = access_token
        self.base_url = base_url
        self.headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make authenticated API request."""
        url = f"{self.base_url}/{endpoint}"
        
        response = requests.request(
            method=method,
            url=url,
            headers=self.headers,
            timeout=30,
            **kwargs
        )
        
        response.raise_for_status()
        return response.json() if response.content else {}
    
    # Repository Management
    
    def create_repository(
        self,
        name: str,
        description: str = "",
        private: bool = True,
        auto_init: bool = True,
        gitignore_template: Optional[str] = None,
        license_template: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new repository.
        
        Args:
            name: Repository name
            description: Repository description
            private: Whether repository is private
            auto_init: Initialize with README
            gitignore_template: .gitignore template (e.g., 'Python')
            license_template: License template (e.g., 'mit')
            
        Returns:
            Created repository data
        """
        logger.info(f"Creating GitHub repository: {name}")
        
        data = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": auto_init,
        }
        
        if gitignore_template:
            data["gitignore_template"] = gitignore_template
        if license_template:
            data["license_template"] = license_template
        
        return self._request("POST", "user/repos", json=data)
    
    def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository details."""
        return self._request("GET", f"repos/{owner}/{repo}")
    
    def list_repositories(self, visibility: str = "all") -> List[Dict[str, Any]]:
        """
        List user repositories.
        
        Args:
            visibility: Filter by visibility (all, public, private)
        """
        return self._request("GET", "user/repos", params={"visibility": visibility})
    
    def delete_repository(self, owner: str, repo: str) -> None:
        """Delete a repository."""
        logger.warning(f"Deleting repository: {owner}/{repo}")
        self._request("DELETE", f"repos/{owner}/{repo}")
    
    # File Operations
    
    def create_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Create a new file in repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            content: File content (will be base64 encoded)
            message: Commit message
            branch: Branch name
            
        Returns:
            Commit data
        """
        logger.info(f"Creating file: {path}")
        
        content_encoded = base64.b64encode(content.encode()).decode()
        
        data = {
            "message": message,
            "content": content_encoded,
            "branch": branch,
        }
        
        return self._request("PUT", f"repos/{owner}/{repo}/contents/{path}", json=data)
    
    def update_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        sha: str,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """Update an existing file."""
        content_encoded = base64.b64encode(content.encode()).decode()
        
        data = {
            "message": message,
            "content": content_encoded,
            "sha": sha,
            "branch": branch,
        }
        
        return self._request("PUT", f"repos/{owner}/{repo}/contents/{path}", json=data)
    
    def get_file_content(self, owner: str, repo: str, path: str) -> Dict[str, Any]:
        """Get file content."""
        return self._request("GET", f"repos/{owner}/{repo}/contents/{path}")
    
    # Issue Management
    
    def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str = "",
        assignees: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        milestone: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a new issue."""
        logger.info(f"Creating issue: {title}")
        
        data = {
            "title": title,
            "body": body,
        }
        
        if assignees:
            data["assignees"] = assignees
        if labels:
            data["labels"] = labels
        if milestone:
            data["milestone"] = milestone
        
        return self._request("POST", f"repos/{owner}/{repo}/issues", json=data)
    
    def update_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        **kwargs
    ) -> Dict[str, Any]:
        """Update an issue."""
        return self._request("PATCH", f"repos/{owner}/{repo}/issues/{issue_number}", json=kwargs)
    
    def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: Optional[str] = None,
        assignee: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List repository issues."""
        params = {"state": state}
        if labels:
            params["labels"] = labels
        if assignee:
            params["assignee"] = assignee
        
        return self._request("GET", f"repos/{owner}/{repo}/issues", params=params)
    
    # Pull Request Management
    
    def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str = "main",
        body: str = "",
        draft: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: PR title
            head: Branch containing changes
            base: Branch to merge into
            body: PR description
            draft: Create as draft PR
        """
        logger.info(f"Creating PR: {title}")
        
        data = {
            "title": title,
            "head": head,
            "base": base,
            "body": body,
            "draft": draft,
        }
        
        return self._request("POST", f"repos/{owner}/{repo}/pulls", json=data)
    
    def merge_pull_request(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        merge_method: str = "merge"  # merge, squash, rebase
    ) -> Dict[str, Any]:
        """Merge a pull request."""
        logger.info(f"Merging PR #{pull_number}")
        
        data = {"merge_method": merge_method}
        
        return self._request("PUT", f"repos/{owner}/{repo}/pulls/{pull_number}/merge", json=data)
    
    # Branch Management
    
    def create_branch(
        self,
        owner: str,
        repo: str,
        branch: str,
        from_branch: str = "main"
    ) -> Dict[str, Any]:
        """Create a new branch from existing branch."""
        logger.info(f"Creating branch: {branch}")
        
        # Get SHA of from_branch
        ref_data = self._request("GET", f"repos/{owner}/{repo}/git/ref/heads/{from_branch}")
        sha = ref_data["object"]["sha"]
        
        # Create new branch
        data = {
            "ref": f"refs/heads/{branch}",
            "sha": sha,
        }
        
        return self._request("POST", f"repos/{owner}/{repo}/git/refs", json=data)
    
    def delete_branch(self, owner: str, repo: str, branch: str) -> None:
        """Delete a branch."""
        logger.warning(f"Deleting branch: {branch}")
        self._request("DELETE", f"repos/{owner}/{repo}/git/refs/heads/{branch}")
    
    # GitHub Actions
    
    def trigger_workflow(
        self,
        owner: str,
        repo: str,
        workflow_id: str,
        ref: str = "main",
        inputs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Trigger a GitHub Actions workflow.
        
        Args:
            owner: Repository owner
            repo: Repository name
            workflow_id: Workflow file name or ID
            ref: Git reference (branch/tag)
            inputs: Workflow inputs
        """
        logger.info(f"Triggering workflow: {workflow_id}")
        
        data = {"ref": ref}
        if inputs:
            data["inputs"] = inputs
        
        self._request("POST", f"repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches", json=data)
    
    def list_workflow_runs(
        self,
        owner: str,
        repo: str,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List workflow runs."""
        params = {}
        if status:
            params["status"] = status
        
        endpoint = f"repos/{owner}/{repo}/actions/runs"
        if workflow_id:
            endpoint = f"repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"
        
        return self._request("GET", endpoint, params=params)
    
    # Project Boards (Projects V2)
    
    def create_project(
        self,
        owner: str,
        title: str,
        body: str = ""
    ) -> Dict[str, Any]:
        """Create a GitHub Project (V2)."""
        logger.info(f"Creating project: {title}")
        
        # GraphQL query for Projects V2
        query = """
        mutation($ownerId: ID!, $title: String!, $body: String) {
          createProjectV2(input: {ownerId: $ownerId, title: $title, body: $body}) {
            projectV2 {
              id
              title
              url
            }
          }
        }
        """
        
        # Get owner ID first
        owner_data = self._request("GET", f"users/{owner}")
        
        variables = {
            "ownerId": owner_data["node_id"],
            "title": title,
            "body": body,
        }
        
        response = requests.post(
            "https://api.github.com/graphql",
            headers=self.headers,
            json={"query": query, "variables": variables},
            timeout=30,
        )
        
        response.raise_for_status()
        return response.json()["data"]["createProjectV2"]["projectV2"]
    
    # Labels
    
    def create_label(
        self,
        owner: str,
        repo: str,
        name: str,
        color: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """Create an issue label."""
        data = {
            "name": name,
            "color": color,
            "description": description,
        }
        
        return self._request("POST", f"repos/{owner}/{repo}/labels", json=data)
    
    # Milestones
    
    def create_milestone(
        self,
        owner: str,
        repo: str,
        title: str,
        due_on: Optional[str] = None,
        description: str = ""
    ) -> Dict[str, Any]:
        """Create a milestone."""
        data = {
            "title": title,
            "description": description,
        }
        
        if due_on:
            data["due_on"] = due_on
        
        return self._request("POST", f"repos/{owner}/{repo}/milestones", json=data)
    
    # Webhooks
    
    def create_webhook(
        self,
        owner: str,
        repo: str,
        url: str,
        events: List[str] = ["push", "pull_request"],
        secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a repository webhook."""
        logger.info(f"Creating webhook for: {url}")
        
        config = {
            "url": url,
            "content_type": "json",
        }
        
        if secret:
            config["secret"] = secret
        
        data = {
            "name": "web",
            "active": True,
            "events": events,
            "config": config,
        }
        
        return self._request("POST", f"repos/{owner}/{repo}/hooks", json=data)
    
    # Utility Methods
    
    def bootstrap_repository(
        self,
        name: str,
        description: str,
        template: str = "python"
    ) -> Dict[str, Any]:
        """
        Bootstrap a complete repository with standard structure.
        
        Args:
            name: Repository name
            description: Repository description
            template: Template type (python, node, react, etc.)
            
        Returns:
            Repository setup data
        """
        logger.info(f"Bootstrapping repository: {name}")
        
        # Create repository
        repo = self.create_repository(
            name=name,
            description=description,
            private=True,
            auto_init=True,
            gitignore_template=template.capitalize(),
            license_template="mit",
        )
        
        owner = repo["owner"]["login"]
        repo_name = repo["name"]
        
        # Create default labels
        labels = [
            {"name": "bug", "color": "d73a4a", "description": "Something isn't working"},
            {"name": "enhancement", "color": "a2eeef", "description": "New feature or request"},
            {"name": "documentation", "color": "0075ca", "description": "Documentation improvements"},
            {"name": "good first issue", "color": "7057ff", "description": "Good for newcomers"},
        ]
        
        for label in labels:
            try:
                self.create_label(owner, repo_name, **label)
            except Exception as e:
                logger.warning(f"Failed to create label: {e}")
        
        # Create develop branch
        try:
            self.create_branch(owner, repo_name, "develop", "main")
        except Exception as e:
            logger.warning(f"Failed to create develop branch: {e}")
        
        return {
            "repository": repo,
            "owner": owner,
            "repo_name": repo_name,
            "url": repo["html_url"],
        }
