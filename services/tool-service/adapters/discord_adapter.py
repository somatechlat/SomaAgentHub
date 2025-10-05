"""
⚠️ WE DO NOT MOCK - Real Discord API integration.

Discord Adapter for Team Communication
Comprehensive Discord bot integration for team collaboration and notifications.
"""

import requests
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class DiscordAdapter:
    """
    Discord adapter for team communication and collaboration.
    
    API documentation: https://discord.com/developers/docs/intro
    """
    
    def __init__(self, bot_token: str):
        """
        Initialize Discord adapter.
        
        Args:
            bot_token: Discord bot token
        """
        self.bot_token = bot_token
        self.base_url = "https://discord.com/api/v10"
        self.headers = {
            "Authorization": f"Bot {bot_token}",
            "Content-Type": "application/json"
        }
        logger.info("Discord adapter initialized")
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make API request."""
        url = f"{self.base_url}/{endpoint}"
        response = requests.request(method, url, headers=self.headers, timeout=30, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else {}
    
    # ============================================================================
    # CHANNELS
    # ============================================================================
    
    def create_channel(
        self,
        guild_id: str,
        name: str,
        type: int = 0,  # 0=text, 2=voice, 4=category
        topic: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a channel in a guild."""
        data = {"name": name, "type": type}
        if topic:
            data["topic"] = topic
        if parent_id:
            data["parent_id"] = parent_id
        
        channel = self._request("POST", f"guilds/{guild_id}/channels", json=data)
        logger.info(f"Created channel: {channel['name']}")
        return channel
    
    def get_channel(self, channel_id: str) -> Dict[str, Any]:
        """Get channel by ID."""
        return self._request("GET", f"channels/{channel_id}")
    
    def list_guild_channels(self, guild_id: str) -> List[Dict[str, Any]]:
        """List all channels in a guild."""
        return self._request("GET", f"guilds/{guild_id}/channels")
    
    def delete_channel(self, channel_id: str):
        """Delete a channel."""
        self._request("DELETE", f"channels/{channel_id}")
        logger.info(f"Deleted channel: {channel_id}")
    
    # ============================================================================
    # MESSAGES
    # ============================================================================
    
    def send_message(
        self,
        channel_id: str,
        content: Optional[str] = None,
        embeds: Optional[List[Dict[str, Any]]] = None,
        components: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Send a message to a channel."""
        data = {}
        if content:
            data["content"] = content
        if embeds:
            data["embeds"] = embeds
        if components:
            data["components"] = components
        
        message = self._request("POST", f"channels/{channel_id}/messages", json=data)
        logger.info(f"Sent message to channel {channel_id}")
        return message
    
    def edit_message(
        self,
        channel_id: str,
        message_id: str,
        content: Optional[str] = None,
        embeds: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Edit an existing message."""
        data = {}
        if content:
            data["content"] = content
        if embeds:
            data["embeds"] = embeds
        
        return self._request("PATCH", f"channels/{channel_id}/messages/{message_id}", json=data)
    
    def delete_message(self, channel_id: str, message_id: str):
        """Delete a message."""
        self._request("DELETE", f"channels/{channel_id}/messages/{message_id}")
        logger.info(f"Deleted message {message_id}")
    
    def add_reaction(self, channel_id: str, message_id: str, emoji: str):
        """Add a reaction to a message."""
        # URL encode emoji
        import urllib.parse
        encoded_emoji = urllib.parse.quote(emoji)
        self._request("PUT", f"channels/{channel_id}/messages/{message_id}/reactions/{encoded_emoji}/@me")
    
    # ============================================================================
    # EMBEDS (Rich Messages)
    # ============================================================================
    
    def create_embed(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[int] = None,
        fields: Optional[List[Dict[str, Any]]] = None,
        footer: Optional[Dict[str, str]] = None,
        thumbnail: Optional[str] = None,
        image: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create an embed object."""
        embed = {}
        if title:
            embed["title"] = title
        if description:
            embed["description"] = description
        if color:
            embed["color"] = color
        if fields:
            embed["fields"] = fields
        if footer:
            embed["footer"] = footer
        if thumbnail:
            embed["thumbnail"] = {"url": thumbnail}
        if image:
            embed["image"] = {"url": image}
        
        return embed
    
    def send_embed(
        self,
        channel_id: str,
        title: str,
        description: str,
        color: int = 0x00ff00,
        fields: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Send an embed message."""
        embed = self.create_embed(title=title, description=description, color=color, fields=fields)
        return self.send_message(channel_id=channel_id, embeds=[embed])
    
    # ============================================================================
    # THREADS
    # ============================================================================
    
    def create_thread(
        self,
        channel_id: str,
        name: str,
        message_id: Optional[str] = None,
        auto_archive_duration: int = 1440  # minutes
    ) -> Dict[str, Any]:
        """Create a thread."""
        data = {
            "name": name,
            "auto_archive_duration": auto_archive_duration
        }
        
        if message_id:
            # Create thread from message
            thread = self._request("POST", f"channels/{channel_id}/messages/{message_id}/threads", json=data)
        else:
            # Create standalone thread
            data["type"] = 11  # Public thread
            thread = self._request("POST", f"channels/{channel_id}/threads", json=data)
        
        logger.info(f"Created thread: {thread['name']}")
        return thread
    
    # ============================================================================
    # WEBHOOKS
    # ============================================================================
    
    def create_webhook(self, channel_id: str, name: str) -> Dict[str, Any]:
        """Create a webhook for a channel."""
        webhook = self._request("POST", f"channels/{channel_id}/webhooks", json={"name": name})
        logger.info(f"Created webhook: {webhook['name']}")
        return webhook
    
    def execute_webhook(self, webhook_id: str, webhook_token: str, content: str) -> Dict[str, Any]:
        """Execute a webhook (send message)."""
        url = f"{self.base_url}/webhooks/{webhook_id}/{webhook_token}"
        response = requests.post(url, json={"content": content}, timeout=30)
        response.raise_for_status()
        return response.json() if response.content else {}
    
    # ============================================================================
    # ROLES
    # ============================================================================
    
    def create_role(
        self,
        guild_id: str,
        name: str,
        permissions: Optional[str] = None,
        color: Optional[int] = None,
        hoist: bool = False,
        mentionable: bool = False
    ) -> Dict[str, Any]:
        """Create a role in a guild."""
        data = {"name": name, "hoist": hoist, "mentionable": mentionable}
        if permissions:
            data["permissions"] = permissions
        if color:
            data["color"] = color
        
        role = self._request("POST", f"guilds/{guild_id}/roles", json=data)
        logger.info(f"Created role: {role['name']}")
        return role
    
    def assign_role(self, guild_id: str, user_id: str, role_id: str):
        """Assign a role to a user."""
        self._request("PUT", f"guilds/{guild_id}/members/{user_id}/roles/{role_id}")
        logger.info(f"Assigned role {role_id} to user {user_id}")
    
    # ============================================================================
    # MEMBERS
    # ============================================================================
    
    def get_guild_member(self, guild_id: str, user_id: str) -> Dict[str, Any]:
        """Get a guild member."""
        return self._request("GET", f"guilds/{guild_id}/members/{user_id}")
    
    def list_guild_members(self, guild_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """List guild members."""
        return self._request("GET", f"guilds/{guild_id}/members", params={"limit": limit})
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def create_project_workspace(
        self,
        guild_id: str,
        project_name: str,
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a complete project workspace with category and channels.
        
        Args:
            guild_id: Discord server ID
            project_name: Name of the project
            channels: List of channel names to create
        
        Returns:
            Dictionary with category and created channels
        """
        # Create category
        category = self.create_channel(
            guild_id=guild_id,
            name=project_name,
            type=4  # Category
        )
        
        # Default channels if not provided
        if not channels:
            channels = ["general", "development", "testing", "announcements"]
        
        # Create channels under category
        created_channels = []
        for channel_name in channels:
            channel = self.create_channel(
                guild_id=guild_id,
                name=channel_name,
                type=0,  # Text channel
                parent_id=category["id"]
            )
            created_channels.append(channel)
        
        logger.info(f"Created project workspace for '{project_name}' with {len(created_channels)} channels")
        
        return {
            "category": category,
            "channels": created_channels
        }
    
    def send_notification(
        self,
        channel_id: str,
        title: str,
        message: str,
        severity: str = "info",
        fields: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send a formatted notification message.
        
        Args:
            channel_id: Channel to send to
            title: Notification title
            message: Notification message
            severity: info, warning, error, success
            fields: Additional fields
        """
        # Color based on severity
        colors = {
            "info": 0x3498db,      # Blue
            "warning": 0xf39c12,   # Orange
            "error": 0xe74c3c,     # Red
            "success": 0x2ecc71    # Green
        }
        color = colors.get(severity, 0x95a5a6)
        
        return self.send_embed(
            channel_id=channel_id,
            title=title,
            description=message,
            color=color,
            fields=fields
        )
