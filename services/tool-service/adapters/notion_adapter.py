"""
⚠️ WE DO NOT MOCK - Real Notion API adapter.

Provides comprehensive Notion integration:
    - Database creation and queries
    - Page creation and updates
    - Block management
    - Team collaboration
"""

import logging
from typing import Any

import requests

from services.common.config.base_settings import resolve_env

logger = logging.getLogger(__name__)


class NotionAdapter:
    """
    Adapter for Notion API.

    API Documentation: https://developers.notion.com
    """

    def __init__(self, api_token: str | None = None):
        self.api_token = api_token or resolve_env("NOTION_API_TOKEN")
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

        if not self.api_token:
            logger.warning("NOTION_API_TOKEN not found. API calls will fail.")

    def _request(self, method: str, endpoint: str, **kwargs) -> dict[str, Any]:
        """Make authenticated API request."""
        url = f"{self.base_url}/{endpoint}"

        response = requests.request(method=method, url=url, headers=self.headers, timeout=30, **kwargs)

        response.raise_for_status()
        return response.json()

    # ----------------------------------------------------------------------
    # Database Operations
    # ----------------------------------------------------------------------

    def query_database(
        self,
        database_id: str,
        filter_criteria: dict[str, Any] | None = None,
        sorts: list[dict[str, Any]] | None = None,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """
        Query a database.

        Args:
            database_id: Database ID
            filter_criteria: Filter object
            sorts: Sort object
        """
        data = {"page_size": page_size}
        if filter_criteria:
            data["filter"] = filter_criteria
        if sorts:
            data["sorts"] = sorts

        return self._request("POST", f"databases/{database_id}/query", json=data)

    def create_database(
        self,
        parent_page_id: str,
        title: str,
        properties: dict[str, Any],
        icon: dict[str, Any] | None = None,
        cover: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new database."""
        data = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": properties,
        }

        if icon:
            data["icon"] = icon
        if cover:
            data["cover"] = cover

        return self._request("POST", "databases", json=data)

    def retrieve_database(self, database_id: str) -> dict[str, Any]:
        """Retrieve database metadata."""
        return self._request("GET", f"databases/{database_id}")

    # ----------------------------------------------------------------------
    # Page Operations
    # ----------------------------------------------------------------------

    def create_page(
        self,
        parent_id: str,
        properties: dict[str, Any],
        children: list[dict[str, Any]] | None = None,
        icon: dict[str, Any] | None = None,
        cover: dict[str, Any] | None = None,
        parent_type: str = "database_id",
    ) -> dict[str, Any]:
        """
        Create a new page.

        Args:
            parent_id: Parent database or page ID
            properties: Page properties (must match schema)
            children: Page content (blocks)
            parent_type: "database_id" or "page_id"
        """
        data = {
            "parent": {parent_type: parent_id},
            "properties": properties,
        }

        if children:
            data["children"] = children
        if icon:
            data["icon"] = icon
        if cover:
            data["cover"] = cover

        return self._request("POST", "pages", json=data)

    def retrieve_page(self, page_id: str) -> dict[str, Any]:
        """Retrieve page properties."""
        return self._request("GET", f"pages/{page_id}")

    def update_page_properties(
        self,
        page_id: str,
        properties: dict[str, Any],
        icon: dict[str, Any] | None = None,
        cover: dict[str, Any] | None = None,
        archived: bool | None = None,
    ) -> dict[str, Any]:
        """Update page properties."""
        data = {"properties": properties}

        if icon:
            data["icon"] = icon
        if cover:
            data["cover"] = cover
        if archived is not None:
            data["archived"] = archived

        return self._request("PATCH", f"pages/{page_id}", json=data)

    # ----------------------------------------------------------------------
    # Block Operations
    # ----------------------------------------------------------------------

    def retrieve_block_children(self, block_id: str, page_size: int = 100) -> dict[str, Any]:
        """Retrieve children blocks of a block or page."""
        return self._request("GET", f"blocks/{block_id}/children", params={"page_size": page_size})

    def append_block_children(self, block_id: str, children: list[dict[str, Any]]) -> dict[str, Any]:
        """Append blocks to a parent."""
        return self._request("PATCH", f"blocks/{block_id}/children", json={"children": children})

    def update_block(self, block_id: str, block_content: dict[str, Any]) -> dict[str, Any]:
        """Update a block's content."""
        return self._request("PATCH", f"blocks/{block_id}", json=block_content)

    def delete_block(self, block_id: str) -> dict[str, Any]:
        """Delete (archive) a block."""
        return self._request("DELETE", f"blocks/{block_id}")

    # ----------------------------------------------------------------------
    # Search
    # ----------------------------------------------------------------------

    def search(
        self,
        query: str,
        filter_criteria: dict[str, Any] | None = None,
        sort: dict[str, Any] | None = None,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """Search pages and databases."""
        data = {"query": query, "page_size": page_size}

        if filter_criteria:
            data["filter"] = filter_criteria
        if sort:
            data["sort"] = sort

        return self._request("POST", "search", json=data)

    # ----------------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------------

    @staticmethod
    def build_text_block(content: str, style: str = "paragraph") -> dict[str, Any]:
        """
        Build a text block.

        Args:
            content: Text content
            style: "paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", etc.
        """
        return {
            "object": "block",
            "type": style,
            style: {"rich_text": [{"type": "text", "text": {"content": content}}]},
        }

    @staticmethod
    def build_todo_block(content: str, checked: bool = False) -> dict[str, Any]:
        """Build a to-do block."""
        return {
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": [{"type": "text", "text": {"content": content}}],
                "checked": checked,
            },
        }

    @staticmethod
    def build_code_block(content: str, language: str = "plain text") -> dict[str, Any]:
        """Build a code block."""
        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{"type": "text", "text": {"content": content}}],
                "language": language,
            },
        }
