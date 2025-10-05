"""
Integration tests for Python SDK.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from somaagent import SomaAgentClient, AsyncSomaAgentClient
from somaagent.exceptions import APIError, AuthenticationError, RateLimitError
from somaagent.models import Message, Conversation


class TestSyncClient:
    """Test synchronous SDK client."""
    
    @patch('somaagent.client.requests.Session')
    def test_authentication(self, mock_session):
        """Test API key authentication."""
        client = SomaAgentClient(api_key="test-key")
        
        assert client.api_key == "test-key"
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"] == "Bearer test-key"
    
    @patch('somaagent.client.requests.Session.request')
    def test_create_conversation(self, mock_request):
        """Test conversation creation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "conv-123",
            "user_id": "user-456",
            "messages": [],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "metadata": {}
        }
        mock_request.return_value = mock_response
        
        client = SomaAgentClient(api_key="test-key")
        conversation = client.create_conversation()
        
        assert conversation.id == "conv-123"
        assert isinstance(conversation, Conversation)
    
    @patch('somaagent.client.requests.Session.request')
    def test_send_message(self, mock_request):
        """Test sending message."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "msg-123",
            "conversation_id": "conv-123",
            "role": "assistant",
            "content": "Hello!",
            "created_at": "2024-01-01T00:00:00Z",
            "metadata": {}
        }
        mock_request.return_value = mock_response
        
        client = SomaAgentClient(api_key="test-key")
        message = client.send_message("conv-123", "Hi there")
        
        assert message.content == "Hello!"
        assert isinstance(message, Message)
    
    @patch('somaagent.client.requests.Session.request')
    def test_api_error_handling(self, mock_request):
        """Test API error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.content = b'{"error": "Internal error"}'
        mock_response.json.return_value = {"error": "Internal error"}
        mock_request.return_value = mock_response
        
        client = SomaAgentClient(api_key="test-key")
        
        with pytest.raises(APIError) as exc:
            client.create_conversation()
        
        assert exc.value.status_code == 500
    
    @patch('somaagent.client.requests.Session.request')
    def test_rate_limit_error(self, mock_request):
        """Test rate limit handling."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_request.return_value = mock_response
        
        client = SomaAgentClient(api_key="test-key")
        
        with pytest.raises(RateLimitError):
            client.create_conversation()


class TestAsyncClient:
    """Test asynchronous SDK client."""
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""
        async with AsyncSomaAgentClient(api_key="test-key") as client:
            assert client.session is not None
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.request')
    async def test_create_conversation_async(self, mock_request):
        """Test async conversation creation."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "id": "conv-123",
            "user_id": "user-456",
            "messages": [],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "metadata": {}
        })
        mock_request.return_value.__aenter__.return_value = mock_response
        
        async with AsyncSomaAgentClient(api_key="test-key") as client:
            conversation = await client.create_conversation()
            assert conversation.id == "conv-123"
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.request')
    async def test_send_message_async(self, mock_request):
        """Test async message sending."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "id": "msg-123",
            "conversation_id": "conv-123",
            "role": "assistant",
            "content": "Response",
            "created_at": "2024-01-01T00:00:00Z",
            "metadata": {}
        })
        mock_request.return_value.__aenter__.return_value = mock_response
        
        async with AsyncSomaAgentClient(api_key="test-key") as client:
            message = await client.send_message("conv-123", "Question")
            assert message.content == "Response"


class TestCLI:
    """Test CLI tool."""
    
    def test_cli_import(self):
        """Test CLI can be imported."""
        from cli.soma import cli
        
        assert cli is not None
    
    @patch('somaagent.SomaAgentClient')
    def test_config_storage(self, mock_client):
        """Test API key storage."""
        from cli.soma import save_api_key, load_api_key
        
        # Save API key
        save_api_key("test-api-key")
        
        # Load API key
        loaded = load_api_key()
        assert loaded == "test-api-key"
