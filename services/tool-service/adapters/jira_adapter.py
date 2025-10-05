"""
⚠️ WE DO NOT MOCK - Real Jira adapter for enterprise project management.

Provides comprehensive Jira integration:
- Issue management (create, update, transition)
- Project management
- Sprint operations (Agile)
- Board management
- User and permission management
- JQL queries
"""

import requests
from typing import Dict, List, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)


class JiraAdapter:
    """
    Adapter for Jira REST API.
    
    Jira Documentation: https://developer.atlassian.com/cloud/jira/platform/rest/v3
    """
    
    def __init__(
        self,
        jira_url: str,
        email: str,
        api_token: str
    ):
        """
        Initialize Jira adapter.
        
        Args:
            jira_url: Jira instance URL (e.g., https://yourcompany.atlassian.net)
            email: User email
            api_token: API token
        """
        self.jira_url = jira_url.rstrip("/")
        self.email = email
        self.api_token = api_token
        self.auth = (email, api_token)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    
    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Any:
        """Make authenticated API request."""
        url = f"{self.jira_url}/rest/api/3/{endpoint}"
        
        response = requests.request(
            method=method,
            url=url,
            auth=self.auth,
            headers=self.headers,
            timeout=30,
            **kwargs
        )
        
        response.raise_for_status()
        return response.json() if response.content else {}
    
    # Issue Management
    
    def create_issue(
        self,
        project_key: str,
        summary: str,
        issue_type: str = "Task",
        description: Optional[str] = None,
        assignee: Optional[str] = None,
        priority: Optional[str] = None,
        labels: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create Jira issue.
        
        Args:
            project_key: Project key
            summary: Issue summary
            issue_type: Issue type (Task, Story, Bug, Epic)
            description: Issue description
            assignee: Assignee account ID
            priority: Priority name
            labels: Labels list
            custom_fields: Custom field values
            
        Returns:
            Created issue
        """
        logger.info(f"Creating Jira issue: {summary}")
        
        fields = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }
        
        if description:
            fields["description"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}]
                    }
                ]
            }
        
        if assignee:
            fields["assignee"] = {"id": assignee}
        
        if priority:
            fields["priority"] = {"name": priority}
        
        if labels:
            fields["labels"] = labels
        
        if custom_fields:
            fields.update(custom_fields)
        
        data = {"fields": fields}
        return self._request("POST", "issue", json=data)
    
    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """Get issue details."""
        return self._request("GET", f"issue/{issue_key}")
    
    def update_issue(
        self,
        issue_key: str,
        fields: Dict[str, Any]
    ) -> None:
        """Update issue fields."""
        logger.info(f"Updating issue: {issue_key}")
        
        data = {"fields": fields}
        self._request("PUT", f"issue/{issue_key}", json=data)
    
    def transition_issue(
        self,
        issue_key: str,
        transition_id: str,
        comment: Optional[str] = None
    ) -> None:
        """
        Transition issue to new status.
        
        Args:
            issue_key: Issue key
            transition_id: Transition ID
            comment: Optional comment
        """
        logger.info(f"Transitioning issue {issue_key} to {transition_id}")
        
        data = {"transition": {"id": transition_id}}
        
        if comment:
            data["update"] = {
                "comment": [{
                    "add": {
                        "body": {
                            "type": "doc",
                            "version": 1,
                            "content": [{
                                "type": "paragraph",
                                "content": [{"type": "text", "text": comment}]
                            }]
                        }
                    }
                }]
            }
        
        self._request("POST", f"issue/{issue_key}/transitions", json=data)
    
    def add_comment(
        self,
        issue_key: str,
        comment: str
    ) -> Dict[str, Any]:
        """Add comment to issue."""
        data = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [{
                    "type": "paragraph",
                    "content": [{"type": "text", "text": comment}]
                }]
            }
        }
        
        return self._request("POST", f"issue/{issue_key}/comment", json=data)
    
    def delete_issue(self, issue_key: str) -> None:
        """Delete issue."""
        logger.warning(f"Deleting issue: {issue_key}")
        self._request("DELETE", f"issue/{issue_key}")
    
    # Search & JQL
    
    def search_issues(
        self,
        jql: str,
        max_results: int = 50,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search issues using JQL.
        
        Args:
            jql: JQL query string
            max_results: Maximum results
            fields: Fields to return
            
        Returns:
            Search results
        """
        logger.info(f"Searching Jira with JQL: {jql}")
        
        params = {
            "jql": jql,
            "maxResults": max_results,
        }
        
        if fields:
            params["fields"] = ",".join(fields)
        
        return self._request("GET", "search", params=params)
    
    # Project Management
    
    def create_project(
        self,
        key: str,
        name: str,
        project_type_key: str = "software",
        lead_account_id: str = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create project."""
        logger.info(f"Creating Jira project: {name}")
        
        data = {
            "key": key,
            "name": name,
            "projectTypeKey": project_type_key,
        }
        
        if lead_account_id:
            data["leadAccountId"] = lead_account_id
        
        if description:
            data["description"] = description
        
        return self._request("POST", "project", json=data)
    
    def get_project(self, project_key: str) -> Dict[str, Any]:
        """Get project details."""
        return self._request("GET", f"project/{project_key}")
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects."""
        return self._request("GET", "project")
    
    # Sprint Management (Agile)
    
    def create_sprint(
        self,
        board_id: int,
        name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        goal: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create sprint.
        
        Args:
            board_id: Board ID
            name: Sprint name
            start_date: Start date (ISO 8601)
            end_date: End date (ISO 8601)
            goal: Sprint goal
        """
        logger.info(f"Creating sprint: {name}")
        
        # Use Agile API (different base)
        url = f"{self.jira_url}/rest/agile/1.0/sprint"
        
        data = {
            "name": name,
            "originBoardId": board_id,
        }
        
        if start_date:
            data["startDate"] = start_date
        if end_date:
            data["endDate"] = end_date
        if goal:
            data["goal"] = goal
        
        response = requests.post(
            url,
            auth=self.auth,
            headers=self.headers,
            json=data,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()
    
    def move_issues_to_sprint(
        self,
        sprint_id: int,
        issues: List[str]
    ) -> None:
        """Move issues to sprint."""
        logger.info(f"Moving {len(issues)} issues to sprint {sprint_id}")
        
        url = f"{self.jira_url}/rest/agile/1.0/sprint/{sprint_id}/issue"
        
        data = {"issues": issues}
        
        response = requests.post(
            url,
            auth=self.auth,
            headers=self.headers,
            json=data,
            timeout=30
        )
        
        response.raise_for_status()
    
    # Board Management
    
    def create_board(
        self,
        name: str,
        board_type: str = "scrum",
        filter_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create board.
        
        Args:
            name: Board name
            board_type: Board type (scrum, kanban)
            filter_id: Filter ID for board
        """
        logger.info(f"Creating {board_type} board: {name}")
        
        url = f"{self.jira_url}/rest/agile/1.0/board"
        
        data = {
            "name": name,
            "type": board_type,
        }
        
        if filter_id:
            data["filterId"] = filter_id
        
        response = requests.post(
            url,
            auth=self.auth,
            headers=self.headers,
            json=data,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()
    
    def list_boards(self) -> Dict[str, Any]:
        """List all boards."""
        url = f"{self.jira_url}/rest/agile/1.0/board"
        
        response = requests.get(
            url,
            auth=self.auth,
            headers=self.headers,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()
    
    # User Management
    
    def search_users(self, query: str) -> List[Dict[str, Any]]:
        """Search for users."""
        return self._request("GET", "user/search", params={"query": query})
    
    # Utility Methods
    
    def bulk_create_issues(
        self,
        issues: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Bulk create issues.
        
        Args:
            issues: List of issue data dicts
            
        Returns:
            Bulk operation results
        """
        logger.info(f"Bulk creating {len(issues)} issues")
        
        issue_updates = [{"fields": issue} for issue in issues]
        data = {"issueUpdates": issue_updates}
        
        return self._request("POST", "issue/bulk", json=data)
    
    def create_epic(
        self,
        project_key: str,
        summary: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create epic."""
        return self.create_issue(
            project_key=project_key,
            summary=summary,
            issue_type="Epic",
            description=description
        )
    
    def link_issue_to_epic(
        self,
        issue_key: str,
        epic_key: str
    ) -> None:
        """Link issue to epic."""
        logger.info(f"Linking {issue_key} to epic {epic_key}")
        
        # This uses a custom field (customfield_10014 is common for epic link)
        self.update_issue(
            issue_key,
            {"customfield_10014": epic_key}
        )
