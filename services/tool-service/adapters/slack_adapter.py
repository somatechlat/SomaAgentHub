"""
⚠️ WE DO NOT MOCK - Real Slack API adapter.

Provides comprehensive Slack integration:
- Channel management
- Messaging (send, update, delete, schedule)
- File uploads
- User management
- Slash commands
- Interactive components
- Webhooks
"""

import requests
from typing import Dict, List, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)


class SlackAdapter:
    """
    Adapter for Slack API.
    
    API Documentation: https://api.slack.com
    """
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = "https://slack.com/api"
        self.headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json; charset=utf-8",
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
        data = response.json()
        
        # Slack returns ok: false for errors
        if not data.get("ok"):
            raise Exception(f"Slack API error: {data.get('error')}")
        
        return data
    
    # Channel Management
    
    def create_channel(
        self,
        name: str,
        is_private: bool = False,
        team_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a channel.
        
        Args:
            name: Channel name (lowercase, no spaces)
            is_private: Create private channel
            team_id: Workspace ID
            
        Returns:
            Channel object
        """
        logger.info(f"Creating Slack channel: {name}")
        
        data = {"name": name, "is_private": is_private}
        if team_id:
            data["team_id"] = team_id
        
        return self._request("POST", "conversations.create", json=data)
    
    def list_channels(
        self,
        exclude_archived: bool = True,
        types: str = "public_channel,private_channel",
        limit: int = 100
    ) -> Dict[str, Any]:
        """List channels."""
        params = {
            "exclude_archived": exclude_archived,
            "types": types,
            "limit": limit,
        }
        return self._request("GET", "conversations.list", params=params)
    
    def archive_channel(self, channel_id: str) -> Dict[str, Any]:
        """Archive a channel."""
        return self._request("POST", "conversations.archive", json={"channel": channel_id})
    
    def invite_to_channel(
        self,
        channel_id: str,
        users: List[str]
    ) -> Dict[str, Any]:
        """
        Invite users to channel.
        
        Args:
            channel_id: Channel ID
            users: List of user IDs
        """
        return self._request(
            "POST",
            "conversations.invite",
            json={"channel": channel_id, "users": ",".join(users)}
        )
    
    # Messaging
    
    def send_message(
        self,
        channel_id: str,
        text: Optional[str] = None,
        blocks: Optional[List[Dict[str, Any]]] = None,
        thread_ts: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send a message.
        
        Args:
            channel_id: Channel ID
            text: Message text (fallback for blocks)
            blocks: Block Kit blocks
            thread_ts: Thread timestamp (for replies)
            attachments: Legacy attachments
            
        Returns:
            Message response with ts
        """
        logger.info(f"Sending Slack message to {channel_id}")
        
        data = {"channel": channel_id}
        
        if text:
            data["text"] = text
        if blocks:
            data["blocks"] = blocks
        if thread_ts:
            data["thread_ts"] = thread_ts
        if attachments:
            data["attachments"] = attachments
        
        return self._request("POST", "chat.postMessage", json=data)
    
    def update_message(
        self,
        channel_id: str,
        ts: str,
        text: Optional[str] = None,
        blocks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Update an existing message."""
        data = {"channel": channel_id, "ts": ts}
        
        if text:
            data["text"] = text
        if blocks:
            data["blocks"] = blocks
        
        return self._request("POST", "chat.update", json=data)
    
    def delete_message(self, channel_id: str, ts: str) -> Dict[str, Any]:
        """Delete a message."""
        return self._request(
            "POST",
            "chat.delete",
            json={"channel": channel_id, "ts": ts}
        )
    
    def schedule_message(
        self,
        channel_id: str,
        post_at: int,  # Unix timestamp
        text: Optional[str] = None,
        blocks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Schedule a message for later.
        
        Args:
            channel_id: Channel ID
            post_at: Unix timestamp
            text: Message text
            blocks: Block Kit blocks
        """
        data = {
            "channel": channel_id,
            "post_at": post_at,
        }
        
        if text:
            data["text"] = text
        if blocks:
            data["blocks"] = blocks
        
        return self._request("POST", "chat.scheduleMessage", json=data)
    
    def add_reaction(
        self,
        channel_id: str,
        timestamp: str,
        name: str
    ) -> Dict[str, Any]:
        """
        Add emoji reaction to message.
        
        Args:
            channel_id: Channel ID
            timestamp: Message timestamp
            name: Emoji name (without ::)
        """
        return self._request(
            "POST",
            "reactions.add",
            json={"channel": channel_id, "timestamp": timestamp, "name": name}
        )
    
    # File Management
    
    def upload_file(
        self,
        channels: List[str],
        file_path: Optional[str] = None,
        content: Optional[str] = None,
        filename: Optional[str] = None,
        title: Optional[str] = None,
        initial_comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a file.
        
        Args:
            channels: List of channel IDs
            file_path: Path to file
            content: File content (alternative to file_path)
            filename: Filename
            title: File title
            initial_comment: Comment with upload
        """
        logger.info(f"Uploading file to Slack channels: {channels}")
        
        data = {"channels": ",".join(channels)}
        
        if title:
            data["title"] = title
        if initial_comment:
            data["initial_comment"] = initial_comment
        
        files = {}
        if file_path:
            files["file"] = open(file_path, "rb")
        elif content:
            data["content"] = content
            if filename:
                data["filename"] = filename
        
        # Use multipart/form-data for file upload
        headers = {"Authorization": f"Bearer {self.bot_token}"}
        
        response = requests.post(
            f"{self.base_url}/files.upload",
            headers=headers,
            data=data,
            files=files,
            timeout=60
        )
        
        if files:
            files["file"].close()
        
        response.raise_for_status()
        result = response.json()
        
        if not result.get("ok"):
            raise Exception(f"Slack API error: {result.get('error')}")
        
        return result
    
    # User Management
    
    def list_users(self, limit: int = 100) -> Dict[str, Any]:
        """List all users in workspace."""
        return self._request("GET", "users.list", params={"limit": limit})
    
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user information."""
        return self._request("GET", "users.info", params={"user": user_id})
    
    def set_user_status(
        self,
        status_text: str,
        status_emoji: str,
        status_expiration: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Set user status.
        
        Args:
            status_text: Status text
            status_emoji: Status emoji (e.g., :calendar:)
            status_expiration: Unix timestamp
        """
        profile = {
            "status_text": status_text,
            "status_emoji": status_emoji,
        }
        
        if status_expiration:
            profile["status_expiration"] = status_expiration
        
        return self._request(
            "POST",
            "users.profile.set",
            json={"profile": profile}
        )
    
    # Webhooks
    
    @staticmethod
    def send_webhook(webhook_url: str, payload: Dict[str, Any]) -> None:
        """
        Send message via incoming webhook.
        
        Args:
            webhook_url: Webhook URL
            payload: Message payload
        """
        logger.info("Sending Slack webhook")
        
        response = requests.post(
            webhook_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=30
        )
        
        response.raise_for_status()
    
    # Block Kit Helpers
    
    @staticmethod
    def build_section_block(
        text: str,
        markdown: bool = True,
        accessory: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build a section block."""
        block = {
            "type": "section",
            "text": {
                "type": "mrkdwn" if markdown else "plain_text",
                "text": text
            }
        }
        
        if accessory:
            block["accessory"] = accessory
        
        return block
    
    @staticmethod
    def build_actions_block(elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build an actions block with interactive elements."""
        return {
            "type": "actions",
            "elements": elements
        }
    
    @staticmethod
    def build_button_element(
        text: str,
        action_id: str,
        value: Optional[str] = None,
        style: Optional[str] = None  # "primary", "danger"
    ) -> Dict[str, Any]:
        """Build a button element."""
        button = {
            "type": "button",
            "text": {"type": "plain_text", "text": text},
            "action_id": action_id,
        }
        
        if value:
            button["value"] = value
        if style:
            button["style"] = style
        
        return button
    
    @staticmethod
    def build_divider_block() -> Dict[str, Any]:
        """Build a divider block."""
        return {"type": "divider"}
    
    @staticmethod
    def build_header_block(text: str) -> Dict[str, Any]:
        """Build a header block."""
        return {
            "type": "header",
            "text": {"type": "plain_text", "text": text}
        }
    
    # Utility Methods
    
    def send_notification(
        self,
        channel_id: str,
        title: str,
        message: str,
        level: str = "info"  # "info", "success", "warning", "error"
    ) -> Dict[str, Any]:
        """
        Send a formatted notification.
        
        Args:
            channel_id: Channel ID
            title: Notification title
            message: Notification message
            level: Severity level
        """
        logger.info(f"Sending Slack notification: {title}")
        
        # Map level to colors
        colors = {
            "info": "#36a64f",      # Green
            "success": "#2eb886",   # Brighter green
            "warning": "#ffa500",   # Orange
            "error": "#ff0000",     # Red
        }
        
        # Build blocks
        blocks = [
            self.build_header_block(title),
            self.build_section_block(message),
        ]
        
        # Legacy attachment for color bar
        attachments = [{
            "color": colors.get(level, "#36a64f"),
            "fallback": f"{title}: {message}"
        }]
        
        return self.send_message(
            channel_id=channel_id,
            blocks=blocks,
            attachments=attachments
        )
    
    def create_project_channel(
        self,
        project_name: str,
        description: str,
        members: List[str]
    ) -> Dict[str, Any]:
        """
        Create a project channel with standard setup.
        
        Args:
            project_name: Project name
            description: Project description
            members: List of user IDs
            
        Returns:
            Channel object
        """
        logger.info(f"Creating project channel: {project_name}")
        
        # Create channel
        channel_name = project_name.lower().replace(" ", "-")[:21]  # Slack limit
        result = self.create_channel(channel_name)
        channel_id = result["channel"]["id"]
        
        # Set topic
        self._request(
            "POST",
            "conversations.setTopic",
            json={"channel": channel_id, "topic": description}
        )
        
        # Invite members
        if members:
            self.invite_to_channel(channel_id, members)
        
        # Send welcome message
        welcome_blocks = [
            self.build_header_block(f"Welcome to #{channel_name}! 🎉"),
            self.build_section_block(description),
            self.build_divider_block(),
            self.build_section_block("*Project Resources:*\n• Pin important links here\n• Use threads for discussions\n• Tag relevant team members"),
        ]
        
        self.send_message(channel_id=channel_id, blocks=welcome_blocks)
        
        return result
