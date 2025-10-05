"""
⚠️ WE DO NOT MOCK - Real Notion API adapter.

Provides comprehensive Notion integration:
- Database creation and queries
- Page creation and updates
- Block management
- Team collaboration
"""

import requests
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class NotionAdapter:
    """
    Adapter for Notion API.
    
    API Documentation: https://developers.notion.com
    """
    
    def __init__(self, api_token: str, notion_version: str = "2022-06-28"):
        self.api_token = api_token
        self.notion_version = notion_version
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Notion-Version": notion_version,
            "Content-Type": "application/json",
        }
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
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
    
    # Database Management
    
    def create_database(
        self,
        parent_page_id: str,
        title: str,
        properties: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create a new database.
        
        Args:
            parent_page_id: Parent page ID
            title: Database title
            properties: Database schema properties
            
        Returns:
            Created database object
        """
        logger.info(f"Creating Notion database: {title}")
        
        data = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": properties,
        }
        
        return self._request("POST", "databases", json=data)
    
    def query_database(
        self,
        database_id: str,
        filter_conditions: Optional[Dict[str, Any]] = None,
        sorts: Optional[List[Dict[str, Any]]] = None,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """
        Query database with filters and sorts.
        
        Args:
            database_id: Database ID
            filter_conditions: Filter object
            sorts: Sort configuration
            page_size: Number of results per page
            
        Returns:
            Query results
        """
        data = {"page_size": page_size}
        
        if filter_conditions:
            data["filter"] = filter_conditions
        if sorts:
            data["sorts"] = sorts
        
        return self._request("POST", f"databases/{database_id}/query", json=data)
    
    # Page Management
    
    def create_page(
        self,
        parent_database_id: Optional[str] = None,
        parent_page_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        children: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new page.
        
        Args:
            parent_database_id: Parent database ID
            parent_page_id: Parent page ID
            properties: Page properties
            children: Child blocks
            
        Returns:
            Created page object
        """
        logger.info("Creating Notion page")
        
        data = {}
        
        if parent_database_id:
            data["parent"] = {"type": "database_id", "database_id": parent_database_id}
        elif parent_page_id:
            data["parent"] = {"type": "page_id", "page_id": parent_page_id}
        else:
            raise ValueError("Must provide either parent_database_id or parent_page_id")
        
        if properties:
            data["properties"] = properties
        if children:
            data["children"] = children
        
        return self._request("POST", "pages", json=data)
    
    def update_page(
        self,
        page_id: str,
        properties: Dict[str, Any],
        archived: bool = False,
    ) -> Dict[str, Any]:
        """Update a page's properties."""
        data = {
            "properties": properties,
            "archived": archived,
        }
        
        return self._request("PATCH", f"pages/{page_id}", json=data)
    
    def get_page(self, page_id: str) -> Dict[str, Any]:
        """Get page details."""
        return self._request("GET", f"pages/{page_id}")
    
    # Block Management
    
    def append_blocks(
        self,
        block_id: str,
        children: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Append blocks to a page or block."""
        data = {"children": children}
        return self._request("PATCH", f"blocks/{block_id}/children", json=data)
    
    def get_block_children(
        self,
        block_id: str,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """Get child blocks."""
        return self._request(
            "GET",
            f"blocks/{block_id}/children",
            params={"page_size": page_size}
        )
    
    def delete_block(self, block_id: str) -> Dict[str, Any]:
        """Delete a block."""
        return self._request("DELETE", f"blocks/{block_id}")
    
    # Search
    
    def search(
        self,
        query: str,
        filter_type: Optional[str] = None,  # "page" or "database"
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """
        Search Notion workspace.
        
        Args:
            query: Search query
            filter_type: Filter by type
            page_size: Results per page
            
        Returns:
            Search results
        """
        data = {
            "query": query,
            "page_size": page_size,
        }
        
        if filter_type:
            data["filter"] = {"property": "object", "value": filter_type}
        
        return self._request("POST", "search", json=data)
    
    # Users
    
    def list_users(self, page_size: int = 100) -> Dict[str, Any]:
        """List all users in workspace."""
        return self._request("GET", "users", params={"page_size": page_size})
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user details."""
        return self._request("GET", f"users/{user_id}")
    
    # Helper Methods - Block Builders
    
    @staticmethod
    def build_heading_block(text: str, level: int = 1) -> Dict[str, Any]:
        """Build a heading block."""
        heading_type = f"heading_{level}"
        return {
            "type": heading_type,
            heading_type: {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
    
    @staticmethod
    def build_paragraph_block(text: str) -> Dict[str, Any]:
        """Build a paragraph block."""
        return {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
    
    @staticmethod
    def build_code_block(code: str, language: str = "python") -> Dict[str, Any]:
        """Build a code block."""
        return {
            "type": "code",
            "code": {
                "rich_text": [{"type": "text", "text": {"content": code}}],
                "language": language,
            }
        }
    
    @staticmethod
    def build_todo_block(text: str, checked: bool = False) -> Dict[str, Any]:
        """Build a to-do block."""
        return {
            "type": "to_do",
            "to_do": {
                "rich_text": [{"type": "text", "text": {"content": text}}],
                "checked": checked,
            }
        }
    
    @staticmethod
    def build_bulleted_list_block(text: str) -> Dict[str, Any]:
        """Build a bulleted list item."""
        return {
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
    
    # Helper Methods - Property Builders
    
    @staticmethod
    def build_title_property(title: str) -> Dict[str, Any]:
        """Build a title property."""
        return {
            "title": [{"type": "text", "text": {"content": title}}]
        }
    
    @staticmethod
    def build_rich_text_property(text: str) -> Dict[str, Any]:
        """Build a rich text property."""
        return {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }
    
    @staticmethod
    def build_select_property(option: str) -> Dict[str, Any]:
        """Build a select property."""
        return {"select": {"name": option}}
    
    @staticmethod
    def build_multi_select_property(options: List[str]) -> Dict[str, Any]:
        """Build a multi-select property."""
        return {
            "multi_select": [{"name": option} for option in options]
        }
    
    @staticmethod
    def build_checkbox_property(checked: bool) -> Dict[str, Any]:
        """Build a checkbox property."""
        return {"checkbox": checked}
    
    @staticmethod
    def build_date_property(start: str, end: Optional[str] = None) -> Dict[str, Any]:
        """Build a date property."""
        date_obj = {"start": start}
        if end:
            date_obj["end"] = end
        return {"date": date_obj}
    
    # Utility Methods
    
    def create_task_database(
        self,
        parent_page_id: str,
        title: str = "Tasks"
    ) -> Dict[str, Any]:
        """
        Create a standard task database with common properties.
        
        Args:
            parent_page_id: Parent page ID
            title: Database title
            
        Returns:
            Created database
        """
        logger.info(f"Creating task database: {title}")
        
        properties = {
            "Name": {"title": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Not Started", "color": "gray"},
                        {"name": "In Progress", "color": "blue"},
                        {"name": "Completed", "color": "green"},
                        {"name": "Blocked", "color": "red"},
                    ]
                }
            },
            "Priority": {
                "select": {
                    "options": [
                        {"name": "Low", "color": "gray"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "High", "color": "orange"},
                        {"name": "Urgent", "color": "red"},
                    ]
                }
            },
            "Due Date": {"date": {}},
            "Assignee": {"people": {}},
            "Tags": {"multi_select": {}},
        }
        
        return self.create_database(parent_page_id, title, properties)
    
    def create_meeting_notes_page(
        self,
        parent_database_id: str,
        title: str,
        date: str,
        attendees: List[str],
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Create a meeting notes page.
        
        Args:
            parent_database_id: Parent database ID
            title: Meeting title
            date: Meeting date
            attendees: List of attendees
            notes: Meeting notes
            
        Returns:
            Created page
        """
        logger.info(f"Creating meeting notes: {title}")
        
        # Build properties
        properties = {
            "Name": self.build_title_property(title),
            "Date": self.build_date_property(date),
            "Attendees": self.build_multi_select_property(attendees),
        }
        
        # Build content blocks
        children = [
            self.build_heading_block("Agenda", 2),
            self.build_paragraph_block(""),
            self.build_heading_block("Discussion", 2),
            self.build_paragraph_block(notes) if notes else self.build_paragraph_block(""),
            self.build_heading_block("Action Items", 2),
            self.build_todo_block("Add action items here"),
        ]
        
        return self.create_page(
            parent_database_id=parent_database_id,
            properties=properties,
            children=children
        )
