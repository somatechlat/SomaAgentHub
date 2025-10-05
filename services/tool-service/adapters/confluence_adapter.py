"""
⚠️ WE DO NOT MOCK - Real Confluence REST API integration.

Confluence Adapter for Documentation Management
Comprehensive Atlassian Confluence integration for knowledge management.
"""

import requests
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ConfluenceAdapter:
    """
    Confluence adapter for documentation and knowledge management.
    
    API documentation: https://developer.atlassian.com/cloud/confluence/rest/v1/intro/
    """
    
    def __init__(self, url: str, email: str, api_token: str):
        """
        Initialize Confluence adapter.
        
        Args:
            url: Confluence instance URL (e.g., https://your-domain.atlassian.net)
            email: User email for authentication
            api_token: API token from Atlassian account
        """
        self.base_url = f"{url}/wiki/rest/api"
        self.auth = (email, api_token)
        self.headers = {"Content-Type": "application/json"}
        logger.info(f"Confluence adapter initialized for {url}")
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make API request."""
        url = f"{self.base_url}/{endpoint}"
        response = requests.request(
            method, url, auth=self.auth, headers=self.headers, timeout=30, **kwargs
        )
        response.raise_for_status()
        return response.json() if response.content else {}
    
    # ============================================================================
    # SPACES
    # ============================================================================
    
    def create_space(
        self,
        key: str,
        name: str,
        description: Optional[str] = None,
        type: str = "global"
    ) -> Dict[str, Any]:
        """Create a new space."""
        data = {
            "key": key,
            "name": name,
            "type": type
        }
        if description:
            data["description"] = {"plain": {"value": description, "representation": "plain"}}
        
        space = self._request("POST", "space", json=data)
        logger.info(f"Created space: {space['key']}")
        return space
    
    def get_space(self, space_key: str) -> Dict[str, Any]:
        """Get space by key."""
        return self._request("GET", f"space/{space_key}")
    
    def list_spaces(self, limit: int = 25) -> List[Dict[str, Any]]:
        """List all spaces."""
        response = self._request("GET", "space", params={"limit": limit})
        return response.get("results", [])
    
    def delete_space(self, space_key: str):
        """Delete a space."""
        self._request("DELETE", f"space/{space_key}")
        logger.info(f"Deleted space: {space_key}")
    
    # ============================================================================
    # PAGES
    # ============================================================================
    
    def create_page(
        self,
        space_key: str,
        title: str,
        body: str,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new page."""
        data = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {
                "storage": {
                    "value": body,
                    "representation": "storage"
                }
            }
        }
        
        if parent_id:
            data["ancestors"] = [{"id": parent_id}]
        
        page = self._request("POST", "content", json=data)
        logger.info(f"Created page: {page['title']}")
        return page
    
    def get_page(self, page_id: str, expand: Optional[str] = "body.storage,version") -> Dict[str, Any]:
        """Get page by ID."""
        params = {"expand": expand} if expand else {}
        return self._request("GET", f"content/{page_id}", params=params)
    
    def update_page(
        self,
        page_id: str,
        title: str,
        body: str,
        version_number: int
    ) -> Dict[str, Any]:
        """Update an existing page."""
        data = {
            "version": {"number": version_number + 1},
            "title": title,
            "type": "page",
            "body": {
                "storage": {
                    "value": body,
                    "representation": "storage"
                }
            }
        }
        
        page = self._request("PUT", f"content/{page_id}", json=data)
        logger.info(f"Updated page: {page['title']}")
        return page
    
    def delete_page(self, page_id: str):
        """Delete a page."""
        self._request("DELETE", f"content/{page_id}")
        logger.info(f"Deleted page: {page_id}")
    
    def search_pages(
        self,
        cql: str,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Search pages using CQL (Confluence Query Language).
        
        Examples:
            - "type=page and space=DEV"
            - "text ~ 'API documentation'"
            - "label = 'architecture'"
        """
        params = {"cql": cql, "limit": limit}
        response = self._request("GET", "content/search", params=params)
        return response.get("results", [])
    
    # ============================================================================
    # ATTACHMENTS
    # ============================================================================
    
    def upload_attachment(
        self,
        page_id: str,
        file_path: str,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload an attachment to a page."""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {}
            if comment:
                data['comment'] = comment
            
            url = f"{self.base_url}/content/{page_id}/child/attachment"
            response = requests.post(
                url,
                auth=self.auth,
                files=files,
                data=data,
                headers={"X-Atlassian-Token": "no-check"},
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Uploaded attachment to page {page_id}")
            return result["results"][0] if result.get("results") else result
    
    def list_attachments(self, page_id: str) -> List[Dict[str, Any]]:
        """List all attachments on a page."""
        response = self._request("GET", f"content/{page_id}/child/attachment")
        return response.get("results", [])
    
    # ============================================================================
    # LABELS
    # ============================================================================
    
    def add_label(self, page_id: str, label: str):
        """Add a label to a page."""
        data = {"prefix": "global", "name": label}
        self._request("POST", f"content/{page_id}/label", json=data)
        logger.info(f"Added label '{label}' to page {page_id}")
    
    def get_labels(self, page_id: str) -> List[str]:
        """Get all labels on a page."""
        response = self._request("GET", f"content/{page_id}/label")
        return [label["name"] for label in response.get("results", [])]
    
    # ============================================================================
    # COMMENTS
    # ============================================================================
    
    def add_comment(
        self,
        page_id: str,
        comment: str
    ) -> Dict[str, Any]:
        """Add a comment to a page."""
        data = {
            "type": "comment",
            "container": {"id": page_id, "type": "page"},
            "body": {
                "storage": {
                    "value": comment,
                    "representation": "storage"
                }
            }
        }
        
        result = self._request("POST", "content", json=data)
        logger.info(f"Added comment to page {page_id}")
        return result
    
    def list_comments(self, page_id: str) -> List[Dict[str, Any]]:
        """List all comments on a page."""
        response = self._request("GET", f"content/{page_id}/child/comment")
        return response.get("results", [])
    
    # ============================================================================
    # UTILITIES
    # ============================================================================
    
    def create_documentation_space(
        self,
        project_name: str,
        description: str,
        initial_pages: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Create a complete documentation space for a project.
        
        Args:
            project_name: Name of the project
            description: Space description
            initial_pages: List of pages [{"title": "...", "body": "..."}]
        
        Returns:
            Dictionary with space and created pages
        """
        # Create space
        space_key = project_name.upper().replace(" ", "").replace("-", "")[:10]
        space = self.create_space(
            key=space_key,
            name=f"{project_name} Documentation",
            description=description
        )
        
        # Create home page
        home_page = self.create_page(
            space_key=space_key,
            title="Home",
            body=f"<h1>Welcome to {project_name}</h1><p>{description}</p>"
        )
        
        # Create initial pages
        created_pages = [home_page]
        if initial_pages:
            for page_data in initial_pages:
                page = self.create_page(
                    space_key=space_key,
                    title=page_data["title"],
                    body=page_data["body"],
                    parent_id=home_page["id"]
                )
                created_pages.append(page)
        
        logger.info(f"Created documentation space '{space_key}' with {len(created_pages)} pages")
        
        return {
            "space": space,
            "pages": created_pages
        }
    
    def create_api_documentation_page(
        self,
        space_key: str,
        api_name: str,
        endpoints: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a formatted API documentation page.
        
        Args:
            space_key: Space to create page in
            api_name: Name of the API
            endpoints: List of endpoint dictionaries
        """
        # Build HTML table
        body = f"<h1>{api_name} API Documentation</h1>"
        body += "<table><tr><th>Method</th><th>Endpoint</th><th>Description</th></tr>"
        
        for endpoint in endpoints:
            body += f"<tr>"
            body += f"<td>{endpoint.get('method', 'GET')}</td>"
            body += f"<td><code>{endpoint.get('path', '')}</code></td>"
            body += f"<td>{endpoint.get('description', '')}</td>"
            body += f"</tr>"
        
        body += "</table>"
        
        page = self.create_page(
            space_key=space_key,
            title=f"{api_name} API",
            body=body
        )
        
        # Add labels
        self.add_label(page["id"], "api")
        self.add_label(page["id"], "documentation")
        
        return page
