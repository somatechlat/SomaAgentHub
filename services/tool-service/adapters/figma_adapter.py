"""
⚠️ WE DO NOT MOCK - Real Figma REST API integration.

Figma Adapter for Design Management
Comprehensive Figma integration for UI/UX design workflows.
"""

import logging
from typing import Any

import requests

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
            access_token: Personal access token
        """
        self.access_token = access_token
        self.base_url = "https://api.figma.com/v1"
        self.headers = {
            "X-Figma-Token": access_token,
            "Content-Type": "application/json",
        }
        logger.info("Figma adapter initialized")

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make API request."""
        url = f"{self.base_url}/{endpoint}"
        response = requests.request(method, url, headers=self.headers, timeout=30, **kwargs)
        response.raise_for_status()
        return response.json()

    # ============================================================================
    # FILES
    # ============================================================================

    def get_file(self, file_key: str, depth: int | None = None) -> dict[str, Any]:
        """
        Get file content.

        Args:
            file_key: File key from URL
            depth: Depth of node tree to traverse
        """
        params = {}
        if depth:
            params["depth"] = depth
        return self._request("GET", f"files/{file_key}", params=params)

    def get_file_nodes(self, file_key: str, node_ids: list[str], depth: int | None = None) -> dict[str, Any]:
        """Get specific nodes from a file."""
        params = {"ids": ",".join(node_ids)}
        if depth:
            params["depth"] = depth
        return self._request("GET", f"files/{file_key}/nodes", params=params)

    def get_image_fills(self, file_key: str) -> dict[str, Any]:
        """Get image fills for a file."""
        return self._request("GET", f"files/{file_key}/images")

    # ============================================================================
    # COMMENTS
    # ============================================================================

    def get_comments(self, file_key: str) -> list[dict[str, Any]]:
        """Get comments for a file."""
        response = self._request("GET", f"files/{file_key}/comments")
        return response.get("comments", [])

    def post_comment(self, file_key: str, message: str, client_meta: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Post a comment to a file.

        Args:
            file_key: File key
            message: Comment text
            client_meta: Position data (x, y, node_id)
        """
        data = {"message": message}
        if client_meta:
            data["client_meta"] = client_meta

        comment = self._request("POST", f"files/{file_key}/comments", json=data)
        logger.info(f"Posted comment to file {file_key}")
        return comment

    def delete_comment(self, file_key: str, comment_id: str):
        """Delete a comment."""
        self._request("DELETE", f"files/{file_key}/comments/{comment_id}")
        logger.info(f"Deleted comment {comment_id}")

    # ============================================================================
    # IMAGES
    # ============================================================================

    def get_images(
        self,
        file_key: str,
        node_ids: list[str],
        scale: float = 1.0,
        format: str = "png",
    ) -> dict[str, str]:
        """
        Render nodes as images.

        Args:
            file_key: File key
            node_ids: List of node IDs
            scale: Image scale (0.01 - 4)
            format: png, jpg, svg, pdf

        Returns:
            Dictionary mapping node IDs to image URLs
        """
        params = {
            "ids": ",".join(node_ids),
            "scale": scale,
            "format": format,
        }
        response = self._request("GET", f"images/{file_key}", params=params)
        return response.get("images", {})

    # ============================================================================
    # PROJECTS & TEAMS
    # ============================================================================

    def get_team_projects(self, team_id: str) -> list[dict[str, Any]]:
        """List projects in a team."""
        response = self._request("GET", f"teams/{team_id}/projects")
        return response.get("projects", [])

    def get_project_files(self, project_id: str) -> list[dict[str, Any]]:
        """List files in a project."""
        response = self._request("GET", f"projects/{project_id}/files")
        return response.get("files", [])

    # ============================================================================
    # COMPONENTS & STYLES
    # ============================================================================

    def get_team_components(self, team_id: str, page_size: int = 30) -> list[dict[str, Any]]:
        """List components in a team library."""
        response = self._request("GET", f"teams/{team_id}/components", params={"page_size": page_size})
        return response.get("meta", {}).get("components", [])

    def get_team_styles(self, team_id: str, page_size: int = 30) -> list[dict[str, Any]]:
        """List styles in a team library."""
        response = self._request("GET", f"teams/{team_id}/styles", params={"page_size": page_size})
        return response.get("meta", {}).get("styles", [])

    def get_file_components(self, file_key: str) -> list[dict[str, Any]]:
        """List components in a file."""
        response = self._request("GET", f"files/{file_key}/components")
        return response.get("meta", {}).get("components", [])

    # ============================================================================
    # UTILITIES
    # ============================================================================

    def export_design_assets(self, file_key: str, node_ids: list[str], output_dir: str) -> list[str]:
        """
        Export nodes as images and save to disk.

        Args:
            file_key: File key
            node_ids: List of node IDs
            output_dir: Directory to save images

        Returns:
            List of saved file paths
        """
        import os

        # Get image URLs
        images = self.get_images(file_key, node_ids, scale=2.0, format="png")
        saved_files = []

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for node_id, url in images.items():
            if not url:
                continue

            # Download image
            response = requests.get(url)
            if response.status_code == 200:
                # Sanitize filename
                filename = f"{node_id.replace(':', '_')}.png"
                filepath = os.path.join(output_dir, filename)

                with open(filepath, "wb") as f:
                    f.write(response.content)

                saved_files.append(filepath)
                logger.info(f"Exported asset: {filepath}")

        return saved_files

    def inspect_node_properties(self, file_key: str, node_id: str) -> dict[str, Any]:
        """
        Inspect properties of a specific node (e.g., for CSS generation).

        Args:
            file_key: File key
            node_id: Node ID
        """
        response = self.get_file_nodes(file_key, [node_id])
        nodes = response.get("nodes", {})
        node = nodes.get(node_id, {}).get("document", {})

        # Extract relevant properties
        properties = {
            "name": node.get("name"),
            "type": node.get("type"),
            "fills": node.get("fills"),
            "strokes": node.get("strokes"),
            "strokeWeight": node.get("strokeWeight"),
            "effects": node.get("effects"),
            "style": node.get("style"),  # Text styles
            "layoutMode": node.get("layoutMode"),
            "constraints": node.get("constraints"),
        }

        return properties
