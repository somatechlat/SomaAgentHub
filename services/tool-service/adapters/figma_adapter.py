"""
⚠️ WE DO NOT MOCK - Real Figma REST API integration.

Figma Adapter for Design Management
Comprehensive Figma integration for UI/UX design workflows.
"""

import requests
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class FigmaAdapter:
    """
    Figma adapter for design file and project management.
    
    API documentation: https://www.figma.com/developers/api
    """
    
    def __init__(self, access_token: str):
        """
        Initialize Figma adapter.
        
        Args:
            access_token: Personal access token from Figma account settings
        """
        self.base_url = "https://api.figma.com/v1"
        self.headers = {
            "X-Figma-Token": access_token,
            "Content-Type": "application/json"
        }
        logger.info("Figma adapter initialized")
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make API request."""
        url = f"{self.base_url}/{endpoint}"
        response = requests.request(method, url, headers=self.headers, timeout=30, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else {}
    
    # ============================================================================
    # FILES
    # ============================================================================
    
    def get_file(self, file_key: str) -> Dict[str, Any]:
        """Get complete file data including all design components."""
        return self._request("GET", f"files/{file_key}")
    
    def get_file_nodes(self, file_key: str, node_ids: List[str]) -> Dict[str, Any]:
        """Get specific nodes from a file."""
        ids = ",".join(node_ids)
        return self._request("GET", f"files/{file_key}/nodes", params={"ids": ids})
    
    def get_file_images(
        self,
        file_key: str,
        node_ids: List[str],
        scale: float = 1.0,
        format: str = "png"
    ) -> Dict[str, str]:
        """
        Render images from file nodes.
        
        Args:
            file_key: File key
            node_ids: List of node IDs to render
            scale: Image scale (1.0, 2.0, 3.0, 4.0)
            format: Image format (png, jpg, svg, pdf)
        
        Returns:
            Dictionary mapping node IDs to image URLs
        """
        ids = ",".join(node_ids)
        params = {"ids": ids, "scale": scale, "format": format}
        response = self._request("GET", f"images/{file_key}", params=params)
        return response.get("images", {})
    
    # ============================================================================
    # COMMENTS
    # ============================================================================
    
    def get_comments(self, file_key: str) -> List[Dict[str, Any]]:
        """Get all comments on a file."""
        response = self._request("GET", f"files/{file_key}/comments")
        return response.get("comments", [])
    
    def post_comment(
        self,
        file_key: str,
        message: str,
        client_meta: Optional[Dict[str, float]] = None,
        comment_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post a comment on a file.
        
        Args:
            file_key: File key
            message: Comment message
            client_meta: Position data {"x": 0.5, "y": 0.5, "node_id": "123:456"}
            comment_id: Reply to existing comment (optional)
        """
        data = {"message": message}
        if client_meta:
            data["client_meta"] = client_meta
        if comment_id:
            data["comment_id"] = comment_id
        
        return self._request("POST", f"files/{file_key}/comments", json=data)
    
    # ============================================================================
    # PROJECTS
    # ============================================================================
    
    def get_project_files(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all files in a project."""
        response = self._request("GET", f"projects/{project_id}/files")
        return response.get("files", [])
    
    def get_team_projects(self, team_id: str) -> List[Dict[str, Any]]:
        """Get all projects in a team."""
        response = self._request("GET", f"teams/{team_id}/projects")
        return response.get("projects", [])
    
    # ============================================================================
    # COMPONENTS & STYLES
    # ============================================================================
    
    def get_file_components(self, file_key: str) -> Dict[str, Any]:
        """Get all components from a file."""
        response = self._request("GET", f"files/{file_key}/components")
        return response.get("meta", {})
    
    def get_file_styles(self, file_key: str) -> Dict[str, Any]:
        """Get all styles from a file."""
        response = self._request("GET", f"files/{file_key}/styles")
        return response.get("meta", {})
    
    def get_team_components(self, team_id: str) -> List[Dict[str, Any]]:
        """Get all components published by a team."""
        response = self._request("GET", f"teams/{team_id}/components")
        return response.get("meta", {}).get("components", [])
    
    def get_team_styles(self, team_id: str) -> List[Dict[str, Any]]:
        """Get all styles published by a team."""
        response = self._request("GET", f"teams/{team_id}/styles")
        return response.get("meta", {}).get("styles", [])
    
    # ============================================================================
    # VERSIONS
    # ============================================================================
    
    def get_file_versions(self, file_key: str) -> List[Dict[str, Any]]:
        """Get version history of a file."""
        response = self._request("GET", f"files/{file_key}/versions")
        return response.get("versions", [])
    
    # ============================================================================
    # USER
    # ============================================================================
    
    def get_me(self) -> Dict[str, Any]:
        """Get current user information."""
        return self._request("GET", "me")
    
    # ============================================================================
    # WEBHOOKS
    # ============================================================================
    
    def create_webhook(
        self,
        team_id: str,
        endpoint: str,
        event_type: str,
        passcode: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a webhook for file updates.
        
        Args:
            team_id: Team ID
            endpoint: Your webhook endpoint URL
            event_type: Event type (FILE_UPDATE, FILE_VERSION_UPDATE, FILE_DELETE, LIBRARY_PUBLISH)
            passcode: Secret passcode for webhook verification
            description: Optional description
        """
        data = {
            "event_type": event_type,
            "team_id": team_id,
            "endpoint": endpoint,
            "passcode": passcode
        }
        if description:
            data["description"] = description
        
        return self._request("POST", "webhooks", json=data)
    
    def list_webhooks(self, team_id: str) -> List[Dict[str, Any]]:
        """List all webhooks for a team."""
        response = self._request("GET", f"webhooks/{team_id}")
        return response.get("webhooks", [])
    
    def delete_webhook(self, webhook_id: str):
        """Delete a webhook."""
        self._request("DELETE", f"webhooks/{webhook_id}")
        logger.info(f"Deleted webhook: {webhook_id}")
    
    # ============================================================================
    # UTILITIES
    # ============================================================================
    
    def export_design_system(
        self,
        file_key: str,
        export_path: str = "."
    ) -> Dict[str, Any]:
        """
        Export complete design system including components and styles.
        
        Args:
            file_key: Figma file key
            export_path: Local path to export assets
        
        Returns:
            Summary of exported assets
        """
        # Get components and styles
        components = self.get_file_components(file_key)
        styles = self.get_file_styles(file_key)
        
        # Get component nodes
        component_ids = [comp["node_id"] for comp in components.get("components", [])]
        
        # Export component images
        images = {}
        if component_ids:
            images = self.get_file_images(
                file_key,
                component_ids,
                scale=2.0,
                format="png"
            )
        
        logger.info(f"Exported {len(component_ids)} components from {file_key}")
        
        return {
            "components": components,
            "styles": styles,
            "images": images,
            "export_path": export_path
        }
    
    def create_design_review_workflow(
        self,
        file_key: str,
        reviewers: List[str],
        review_message: str
    ) -> List[Dict[str, Any]]:
        """
        Create design review workflow with comments.
        
        Args:
            file_key: File to review
            reviewers: List of reviewer names/emails
            review_message: Review request message
        
        Returns:
            List of created comments
        """
        comments = []
        
        # Post review request comment
        comment = self.post_comment(
            file_key,
            f"🎨 Design Review Request\n\n{review_message}\n\nReviewers: {', '.join(reviewers)}"
        )
        comments.append(comment)
        
        logger.info(f"Created design review workflow for {file_key}")
        
        return comments
    
    def analyze_design_changes(
        self,
        file_key: str,
        version_count: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze recent design changes from version history.
        
        Args:
            file_key: File key
            version_count: Number of recent versions to analyze
        
        Returns:
            Analysis of design changes
        """
        versions = self.get_file_versions(file_key)[:version_count]
        
        analysis = {
            "total_versions": len(versions),
            "recent_versions": versions,
            "contributors": list(set(v.get("user", {}).get("handle", "Unknown") for v in versions)),
            "timeline": [
                {
                    "id": v.get("id"),
                    "label": v.get("label", "Unnamed"),
                    "created_at": v.get("created_at"),
                    "description": v.get("description", "")
                }
                for v in versions
            ]
        }
        
        logger.info(f"Analyzed {len(versions)} versions of {file_key}")
        
        return analysis
