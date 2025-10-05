"""
⚠️ WE DO NOT MOCK - Real Linear.app API integration.

Linear Adapter for Project Management
Provides comprehensive Linear.app integration for issue tracking and project management.
"""

import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LinearAdapter:
    """
    Linear.app adapter for issue and project management.
    
    Linear is a modern project management tool focused on speed and developer workflows.
    GraphQL API documentation: https://developers.linear.app/docs/graphql/working-with-the-graphql-api
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Linear adapter.
        
        Args:
            api_key: Linear API key (Personal API Key or OAuth token)
        """
        self.api_key = api_key
        self.api_url = "https://api.linear.app/graphql"
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }
        logger.info("Linear adapter initialized")
    
    def _graphql_query(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute GraphQL query."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        response = requests.post(self.api_url, json=payload, headers=self.headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")
        
        return result["data"]
    
    # ============================================================================
    # ISSUES
    # ============================================================================
    
    def create_issue(
        self,
        team_id: str,
        title: str,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        assignee_id: Optional[str] = None,
        label_ids: Optional[List[str]] = None,
        project_id: Optional[str] = None,
        state_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new issue.
        
        Args:
            team_id: Team identifier
            title: Issue title
            description: Issue description (Markdown)
            priority: Priority (0=None, 1=Urgent, 2=High, 3=Normal, 4=Low)
            assignee_id: User ID to assign
            label_ids: List of label IDs
            project_id: Project ID
            state_id: Workflow state ID
        
        Returns:
            Created issue data
        """
        mutation = """
        mutation CreateIssue($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    url
                    createdAt
                }
            }
        }
        """
        
        input_data = {
            "teamId": team_id,
            "title": title
        }
        
        if description:
            input_data["description"] = description
        if priority is not None:
            input_data["priority"] = priority
        if assignee_id:
            input_data["assigneeId"] = assignee_id
        if label_ids:
            input_data["labelIds"] = label_ids
        if project_id:
            input_data["projectId"] = project_id
        if state_id:
            input_data["stateId"] = state_id
        
        result = self._graphql_query(mutation, {"input": input_data})
        logger.info(f"Created issue: {result['issueCreate']['issue']['identifier']}")
        return result["issueCreate"]["issue"]
    
    def get_issue(self, issue_id: str) -> Dict[str, Any]:
        """Get issue by ID."""
        query = """
        query GetIssue($id: String!) {
            issue(id: $id) {
                id
                identifier
                title
                description
                priority
                state {
                    id
                    name
                    type
                }
                assignee {
                    id
                    name
                    email
                }
                labels {
                    nodes {
                        id
                        name
                        color
                    }
                }
                project {
                    id
                    name
                }
                createdAt
                updatedAt
                completedAt
                url
            }
        }
        """
        
        result = self._graphql_query(query, {"id": issue_id})
        return result["issue"]
    
    def update_issue(
        self,
        issue_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        assignee_id: Optional[str] = None,
        state_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing issue."""
        mutation = """
        mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
            issueUpdate(id: $id, input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    updatedAt
                }
            }
        }
        """
        
        input_data = {}
        if title:
            input_data["title"] = title
        if description:
            input_data["description"] = description
        if priority is not None:
            input_data["priority"] = priority
        if assignee_id:
            input_data["assigneeId"] = assignee_id
        if state_id:
            input_data["stateId"] = state_id
        
        result = self._graphql_query(mutation, {"id": issue_id, "input": input_data})
        return result["issueUpdate"]["issue"]
    
    def search_issues(
        self,
        query: str,
        team_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search issues using Linear's search syntax.
        
        Examples:
            - "is:open priority:urgent"
            - "assignee:me state:in_progress"
            - "label:bug team:engineering"
        """
        graphql_query = """
        query SearchIssues($query: String!, $first: Int!) {
            issueSearch(query: $query, first: $first) {
                nodes {
                    id
                    identifier
                    title
                    priority
                    state {
                        name
                    }
                    assignee {
                        name
                    }
                    url
                }
            }
        }
        """
        
        result = self._graphql_query(graphql_query, {"query": query, "first": limit})
        return result["issueSearch"]["nodes"]
    
    # ============================================================================
    # PROJECTS
    # ============================================================================
    
    def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        team_ids: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        target_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new project.
        
        Args:
            name: Project name
            description: Project description
            team_ids: List of team IDs
            start_date: Start date (ISO 8601)
            target_date: Target completion date (ISO 8601)
        """
        mutation = """
        mutation CreateProject($input: ProjectCreateInput!) {
            projectCreate(input: $input) {
                success
                project {
                    id
                    name
                    url
                    createdAt
                }
            }
        }
        """
        
        input_data = {"name": name}
        if description:
            input_data["description"] = description
        if team_ids:
            input_data["teamIds"] = team_ids
        if start_date:
            input_data["startDate"] = start_date
        if target_date:
            input_data["targetDate"] = target_date
        
        result = self._graphql_query(mutation, {"input": input_data})
        logger.info(f"Created project: {result['projectCreate']['project']['name']}")
        return result["projectCreate"]["project"]
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get project details."""
        query = """
        query GetProject($id: String!) {
            project(id: $id) {
                id
                name
                description
                state
                progress
                startDate
                targetDate
                completedAt
                url
                issues {
                    nodes {
                        id
                        identifier
                        title
                        state {
                            name
                        }
                    }
                }
                teams {
                    nodes {
                        id
                        name
                    }
                }
            }
        }
        """
        
        result = self._graphql_query(query, {"id": project_id})
        return result["project"]
    
    def list_projects(self, team_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List projects."""
        query = """
        query ListProjects($first: Int!) {
            projects(first: $first) {
                nodes {
                    id
                    name
                    state
                    progress
                    url
                }
            }
        }
        """
        
        result = self._graphql_query(query, {"first": limit})
        return result["projects"]["nodes"]
    
    # ============================================================================
    # TEAMS
    # ============================================================================
    
    def get_teams(self) -> List[Dict[str, Any]]:
        """Get all teams in the organization."""
        query = """
        query GetTeams {
            teams {
                nodes {
                    id
                    name
                    key
                    description
                }
            }
        }
        """
        
        result = self._graphql_query(query)
        return result["teams"]["nodes"]
    
    def get_team_workflow_states(self, team_id: str) -> List[Dict[str, Any]]:
        """Get workflow states for a team."""
        query = """
        query GetWorkflowStates($teamId: String!) {
            team(id: $teamId) {
                states {
                    nodes {
                        id
                        name
                        type
                        position
                        color
                    }
                }
            }
        }
        """
        
        result = self._graphql_query(query, {"teamId": team_id})
        return result["team"]["states"]["nodes"]
    
    # ============================================================================
    # LABELS
    # ============================================================================
    
    def create_label(
        self,
        name: str,
        color: Optional[str] = None,
        description: Optional[str] = None,
        team_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a label."""
        mutation = """
        mutation CreateLabel($input: IssueLabelCreateInput!) {
            issueLabelCreate(input: $input) {
                success
                issueLabel {
                    id
                    name
                    color
                }
            }
        }
        """
        
        input_data = {"name": name}
        if color:
            input_data["color"] = color
        if description:
            input_data["description"] = description
        if team_id:
            input_data["teamId"] = team_id
        
        result = self._graphql_query(mutation, {"input": input_data})
        return result["issueLabelCreate"]["issueLabel"]
    
    def get_labels(self, team_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all labels."""
        query = """
        query GetLabels {
            issueLabels {
                nodes {
                    id
                    name
                    color
                    description
                }
            }
        }
        """
        
        result = self._graphql_query(query)
        return result["issueLabels"]["nodes"]
    
    # ============================================================================
    # USERS
    # ============================================================================
    
    def get_viewer(self) -> Dict[str, Any]:
        """Get authenticated user information."""
        query = """
        query GetViewer {
            viewer {
                id
                name
                email
                avatarUrl
                organization {
                    id
                    name
                }
            }
        }
        """
        
        result = self._graphql_query(query)
        return result["viewer"]
    
    def get_users(self) -> List[Dict[str, Any]]:
        """Get all users in the organization."""
        query = """
        query GetUsers {
            users {
                nodes {
                    id
                    name
                    email
                    active
                }
            }
        }
        """
        
        result = self._graphql_query(query)
        return result["users"]["nodes"]
    
    # ============================================================================
    # UTILITIES
    # ============================================================================
    
    def bootstrap_project(
        self,
        name: str,
        team_id: str,
        description: Optional[str] = None,
        initial_issues: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Bootstrap a complete project with team, labels, and initial issues.
        
        Args:
            name: Project name
            team_id: Team to associate with
            description: Project description
            initial_issues: List of initial issues [{"title": "...", "description": "..."}]
        
        Returns:
            Dictionary with project and created issues
        """
        # Create project
        project = self.create_project(
            name=name,
            description=description,
            team_ids=[team_id]
        )
        
        # Create initial issues if provided
        created_issues = []
        if initial_issues:
            for issue_data in initial_issues:
                issue = self.create_issue(
                    team_id=team_id,
                    title=issue_data["title"],
                    description=issue_data.get("description"),
                    project_id=project["id"]
                )
                created_issues.append(issue)
        
        logger.info(f"Bootstrapped project '{name}' with {len(created_issues)} issues")
        
        return {
            "project": project,
            "issues": created_issues
        }
