"""Integration tests for Keycloak, OPA, and Kafka clients."""

import sys
from pathlib import Path

# Add services/common to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "common"))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Keycloak tests
@pytest.mark.asyncio
async def test_keycloak_client_validation():
    """Test Keycloak JWT validation."""
    from keycloak_client import KeycloakClient
    
    with patch("services.common.keycloak_client.KeycloakOpenID") as mock_oidc:
        # Mock Keycloak responses
        mock_instance = MagicMock()
        mock_instance.userinfo.return_value = {
            "sub": "user-123",
            "preferred_username": "testuser",
            "email": "test@example.com",
        }
        mock_instance.decode_token.return_value = {
            "sub": "user-123",
            "preferred_username": "testuser",
            "tenant_id": "demo",
            "realm_access": {"roles": ["admin", "user"]},
        }
        mock_oidc.return_value = mock_instance
        
        client = KeycloakClient(
            server_url="http://keycloak:8080/auth",
            realm_name="somagent",
            client_id="gateway-api",
        )
        
        claims = client.validate_token("fake-jwt-token")
        
        assert claims["sub"] == "user-123"
        assert claims["tenant_id"] == "demo"
        assert "admin" in claims["capabilities"]


@pytest.mark.asyncio
async def test_keycloak_client_invalid_token():
    """Test Keycloak handles invalid tokens."""
    from keycloak_client import KeycloakClient
    from keycloak.exceptions import KeycloakError
    from fastapi import HTTPException
    
    with patch("services.common.keycloak_client.KeycloakOpenID") as mock_oidc:
        mock_instance = MagicMock()
        mock_instance.userinfo.side_effect = KeycloakError("Invalid token")
        mock_oidc.return_value = mock_instance
        
        client = KeycloakClient(
            server_url="http://keycloak:8080/auth",
            realm_name="somagent",
            client_id="gateway-api",
        )
        
        with pytest.raises(HTTPException) as exc_info:
            client.validate_token("bad-token")
        
        assert exc_info.value.status_code == 401


# OPA tests
@pytest.mark.asyncio
async def test_opa_client_authorization():
    """Test OPA authorization check."""
    from opa_client import OPAClient
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"result": True}
        mock_response.raise_for_status = MagicMock()
        
        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_response
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_client.return_value = mock_instance
        
        opa_client = OPAClient(opa_url="http://opa:8181")
        
        authorized = await opa_client.check_authorization(
            tenant_id="demo",
            user_id="user-123",
            action="read",
            resource="session",
        )
        
        assert authorized is True


@pytest.mark.asyncio
async def test_opa_client_policy_denial():
    """Test OPA policy denial."""
    from opa_client import OPAClient
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"result": {"allowed": False, "reason": "Insufficient permissions"}}
        mock_response.raise_for_status = MagicMock()
        
        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_response
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_client.return_value = mock_instance
        
        opa_client = OPAClient(opa_url="http://opa:8181")
        
        result = await opa_client.evaluate_constitution(
            action_type="tool_invocation",
            payload={"tool": "delete_database"},
            tenant_id="demo",
        )
        
        assert result["allowed"] is False


# Kafka tests
@pytest.mark.asyncio
async def test_kafka_client_send_event():
    """Test Kafka event emission."""
    from kafka_client import KafkaClient
    
    with patch("services.common.kafka_client.AIOKafkaProducer") as mock_producer_class:
        mock_producer = AsyncMock()
        mock_producer.start = AsyncMock()
        mock_producer.send_and_wait = AsyncMock()
        mock_producer.stop = AsyncMock()
        mock_producer_class.return_value = mock_producer
        
        kafka_client = KafkaClient(bootstrap_servers="kafka:9092")
        await kafka_client.start()
        
        event_id = await kafka_client.send_event(
            topic="test.topic",
            event={"message": "Hello Kafka"},
            key="test-key",
        )
        
        assert event_id is not None
        mock_producer.send_and_wait.assert_called_once()
        
        await kafka_client.stop()


@pytest.mark.asyncio
async def test_kafka_client_audit_event():
    """Test Kafka audit event emission."""
    from kafka_client import KafkaClient
    
    with patch("services.common.kafka_client.AIOKafkaProducer") as mock_producer_class:
        mock_producer = AsyncMock()
        mock_producer.start = AsyncMock()
        mock_producer.send_and_wait = AsyncMock()
        mock_producer.stop = AsyncMock()
        mock_producer_class.return_value = mock_producer
        
        kafka_client = KafkaClient(bootstrap_servers="kafka:9092")
        await kafka_client.start()
        
        event_id = await kafka_client.send_audit_event(
            session_id="session-123",
            tenant_id="demo",
            user_id="user-123",
            event_type="session.started",
            payload={"prompt": "Hello"},
        )
        
        assert event_id is not None
        
        # Verify the call was made with correct topic
        call_args = mock_producer.send_and_wait.call_args
        assert call_args[0][0] == "agent.audit"
        
        await kafka_client.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
