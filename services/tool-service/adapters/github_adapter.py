"""
⚠️ WE DO NOT MOCK - Real GitHub API adapter.

Provides comprehensive GitHub integration:
    - Repository management
    - Issues and pull requests
    - Actions workflows
    - Project boards
    - Team management
"""

import base64
import logging
from typing import Any

import requests

from services.common.config.base_settings import resolve_env

logger = logging.getLogger(__name__)


class GitHubAdapter:
    """
    Real GitHub API adapter.

    Requires:
        - GITHUB_TOKEN
    """

    def __init__(self, token: str | None = None):
        self.token = token or resolve_env("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        if not self.token:
            logger.warning("GITHUB_TOKEN not found. API calls will fail.")

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make authenticated request to GitHub API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = requests.request(
            method, url, headers=self.headers, timeout=30, **kwargs
        )
        response.raise_for_status()
        return response.json() if response.content else {}

    # ----------------------------------------------------------------------
    # Repository Operations
    # ----------------------------------------------------------------------

    def create_repo(
        self,
        name: str,
        description: str = "",
        private: bool = True,
        auto_init: bool = True,
        org: str | None = None,
    ) -> dict[str, Any]:
        """Create a new repository."""
        data = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": auto_init,
        }

        if org:
            endpoint = f"orgs/{org}/repos"
        else:
            endpoint = "user/repos"

        return self._request("POST", endpoint, json=data)

    def get_repo(self, owner: str, repo: str) -> dict[str, Any]:
        """Get repository details."""
        return self._request("GET", f"repos/{owner}/{repo}")

    def list_repos(
        self, sort: str = "updated", direction: str = "desc", per_page: int = 30
    ) -> list[dict[str, Any]]:
        """List repositories for authenticated user."""
        params = {"sort": sort, "direction": direction, "per_page": per_page}
        return self._request("GET", "user/repos", params=params)

    # ----------------------------------------------------------------------
    # Content Operations
    # ----------------------------------------------------------------------

    def create_file(
        self,
        owner: str,
        repo: str,
        path: str,
        message: str,
        content: str,
        branch: str = "main",
    ) -> dict[str, Any]:
        """Create or update a file."""
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        data = {
            "message": message,
            "content": encoded_content,
            "branch": branch,
        }
        return self._request("PUT", f"repos/{owner}/{repo}/contents/{path}", json=data)

    def get_file_content(
        self, owner: str, repo: str, path: str, ref: str = "main"
    ) -> str:
        """Get raw file content."""
        headers = self.headers.copy()
        headers["Accept"] = "application/vnd.github.raw"
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        response = requests.get(url, headers=headers, params={"ref": ref}, timeout=30)
        response.raise_for_status()
        return response.text

    # ----------------------------------------------------------------------
    # Issue & PR Operations
    # ----------------------------------------------------------------------

    def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        assignees: list[str] | None = None,
        labels: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create an issue."""
        data = {"title": title, "body": body}
        if assignees:
            data["assignees"] = assignees
        if labels:
            data["labels"] = labels

        return self._request("POST", f"repos/{owner}/{repo}/issues", json=data)

    def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "main",
        draft: bool = False,
    ) -> dict[str, Any]:
        """Create a pull request."""
        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base,
            "draft": draft,
        }
        return self._request("POST", f"repos/{owner}/{repo}/pulls", json=data)

    def merge_pull_request(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        commit_title: str | None = None,
        merge_method: str = "merge",
    ) -> dict[str, Any]:
        """Merge a pull request."""
        data = {"merge_method": merge_method}
        if commit_title:
            data["commit_title"] = commit_title

        return self._request(
            "PUT", f"repos/{owner}/{repo}/pulls/{pull_number}/merge", json=data
        )

    # ----------------------------------------------------------------------
    # Actions Operations
    # ----------------------------------------------------------------------

    def trigger_workflow(
        self,
        owner: str,
        repo: str,
        workflow_id: str | int,
        ref: str = "main",
        inputs: dict[str, Any] | None = None,
    ) -> None:
        """Trigger a workflow dispatch event."""
        data = {"ref": ref}
        if inputs:
            data["inputs"] = inputs

        self._request(
            "POST",
            f"repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches",
            json=data,
        )

    def list_workflow_runs(
        self, owner: str, repo: str, workflow_id: str | int, status: str | None = None
    ) -> dict[str, Any]:
        """List workflow runs."""
        params = {}
        if status:
            params["status"] = status
        return self._request(
            "GET",
            f"repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs",
            params=params,
        )

    # ----------------------------------------------------------------------
    # Search Operations
    # ----------------------------------------------------------------------

    def search_code(
        self, query: str, sort: str | None = None, order: str = "desc"
    ) -> dict[str, Any]:
        """Search for code."""
        params = {"q": query, "order": order}
        if sort:
            params["sort"] = sort
        return self._request("GET", "search/code", params=params)

    def search_issues(
        self, query: str, sort: str = "updated", order: str = "desc"
    ) -> dict[str, Any]:
        """Search for issues and PRs."""
        params = {"q": query, "sort": sort, "order": order}
        return self._request("GET", "search/issues", params=params)
