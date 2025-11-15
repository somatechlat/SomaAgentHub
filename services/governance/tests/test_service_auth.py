"""
Enterprise-Grade Service Authentication Tests.

Comprehensive test suite for service-to-service authentication framework.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.service_auth import (
    ServiceAccount,
    ServiceAuthConfig,
    ServiceAuthManager,
    ServiceToken,
)


@pytest.fixture
def auth_config():
    """Create test authentication configuration."""
    return ServiceAuthConfig(
        token_issuer="test-issuer",
        token_audience="test-audience",
        access_token_lifetime=timedelta(hours=1),
        refresh_token_lifetime=timedelta(days=1),
        service_token_lifetime=timedelta(days=7),
        rotation_threshold=timedelta(minutes=30),
        max_rotation_count=10,
        key_rotation_interval=timedelta(days=1),
    )


@pytest.fixture
def mock_vault_client():
    """Create mock Vault client."""
    mock_client = AsyncMock()
    mock_client.read_secret.return_value = None
    mock_client.write_secret.return_value = None
    return mock_client


@pytest.fixture
async def auth_manager(auth_config, mock_vault_client):
    """Create and initialize service authentication manager."""
    with patch('app.core.service_auth.get_vault_client', return_value=mock_vault_client):
        manager = ServiceAuthManager(auth_config)
        await manager.initialize()
        return manager


class TestServiceAccount:
    """Test service account functionality."""

    @pytest.mark.asyncio
    async def test_create_service_account(self, auth_manager):
        """Test creating a service account."""
        service_account = await auth_manager.create_service_account(
            service_name="test-service",
            namespace="test-namespace",
            roles=["test-role"],
            permissions=["test-permission"],
            metadata={"key": "value"},
        )

        assert service_account.service_id == "test-namespace/test-service"
        assert service_account.service_name == "test-service"
        assert service_account.namespace == "test-namespace"
        assert service_account.roles == ["test-role"]
        assert service_account.permissions == ["test-permission"]
        assert service_account.metadata == {"key": "value"}
        assert service_account.active is True

    @pytest.mark.asyncio
    async def test_create_duplicate_service_account(self, auth_manager):
        """Test creating a duplicate service account raises error."""
        await auth_manager.create_service_account(
            service_name="test-service",
            namespace="test-namespace",
        )

        with pytest.raises(ValueError, match="already exists"):
            await auth_manager.create_service_account(
                service_name="test-service",
                namespace="test-namespace",
            )

    @pytest.mark.asyncio
    async def test_get_service_account(self, auth_manager):
        """Test getting a service account."""
        created_account = await auth_manager.create_service_account(
            service_name="test-service",
            namespace="test-namespace",
        )

        retrieved_account = auth_manager.get_service_account("test-namespace/test-service")
        
        assert retrieved_account is not None
        assert retrieved_account.service_id == created_account.service_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_service_account(self, auth_manager):
        """Test getting a nonexistent service account."""
        account = auth_manager.get_service_account("nonexistent/service")
        assert account is None

    @pytest.mark.asyncio
    async def test_list_service_accounts(self, auth_manager):
        """Test listing service accounts."""
        await auth_manager.create_service_account(
            service_name="service1",
            namespace="test-namespace",
        )
        await auth_manager.create_service_account(
            service_name="service2",
            namespace="test-namespace",
        )

        accounts = auth_manager.list_service_accounts()
        assert len(accounts) == 2

    @pytest.mark.asyncio
    async def test_deactivate_service_account(self, auth_manager):
        """Test deactivating a service account."""
        service_account = await auth_manager.create_service_account(
            service_name="test-service",
            namespace="test-namespace",
        )

        await auth_manager.deactivate_service_account("test-namespace/test-service")
        
        assert service_account.active is False

    @pytest.mark.asyncio
    async def test_deactivate_nonexistent_service_account(self, auth_manager):
        """Test deactivating a nonexistent service account raises error."""
        with pytest.raises(ValueError, match="not found"):
            await auth_manager.deactivate_service_account("nonexistent/service")


class TestServiceToken:
    """Test service token functionality."""

    @pytest.mark.asyncio
    async def test_generate_access_token(self, auth_manager):
        """Test generating an access token."""
        await auth_manager.create_service_account(
            service_name="test-service",
            namespace="test-namespace",
        )

        token_string, token_info = await auth_manager.generate_service_token(
            service_id="test-namespace/test-service",
            token_type="access",
            scopes=["read", "write"],
        )

        assert token_string is not None
        assert len(token_string) > 0
        assert token_info.token_type == "access"
        assert token_info.scopes == ["read", "write"]
        assert token_info.active is True
        assert token_info.service_id == "test-namespace/test-service"

    @pytest.mark.asyncio
    async def test_generate_token_nonexistent_service(self, auth_manager):
        """Test generating token for nonexistent service raises error."""
        with pytest.raises(ValueError, match="not found"):
            await auth_manager.generate_service_token(
                service_id="nonexistent/service",
                token_type="access",
            )

    @pytest.mark.asyncio
    async def test_generate_token_inactive_service(self, auth_manager):
        """Test generating token for inactive service raises error."""
        service_account = await auth_manager.create_service_account(
            service_name="test-service",
            namespace="test-namespace",
        )
        service_account.active = False

        with pytest.raises(ValueError, match="not active"):
            await auth_manager.generate_service_token(
                service_id="test-namespace/test-service",
                token_type="access",
            )

    @pytest.mark.asyncio
    async def test_verify_service_token(self, auth_manager):
        """Test verifying a service token."""
        await auth_manager.create_service_account(
            service_name="test-service",
            namespace="test-namespace",
        )

        token_string, _ = await auth_manager.generate_service_token(
            service_id="test-namespace/test-service",
            token_type="access",
        )

        claims = await auth_manager.verify_service_token(token_string)
        
        assert claims["sub"] == "test-namespace/test-service"
        assert claims["iss"] == "test-issuer"
        assert claims["aud"] == "test-audience"
        assert claims["type"] == "access"
        assert claims["service_name"] == "test-service"
        assert claims["namespace"] == "test-namespace"

    @pytest.mark.asyncio
    async def test_verify_invalid_token(self, auth_manager):
        """Test verifying an invalid token raises error."""
        with pytest.raises(Exception):
            await auth_manager.verify_service_token("invalid-token")

    @pytest.mark.asyncio
    async def test_rotate_token(self, auth_manager):
        """Test rotating a token."""
        await auth_manager.create_service_account(
            service_name="test-service",
            namespace="test-namespace",
        )

        _, original_token = await auth_manager.generate_service_token(
            service_id="test-namespace/test-service",
            token_type="access",
        )

        new_token_string, new_token = await auth_manager.rotate_token(original_token.jti)
        
        assert new_token_string is not None
        assert new_token.jti != original_token.jti
        assert new_token.rotation_count == 1
        assert original_token.active is False

    @pytest.mark.asyncio
    async def test_rotate_nonexistent_token(self, auth_manager):
        """Test rotating a nonexistent token raises error."""
        with pytest.raises(ValueError, match="not found"):
            await auth_manager.rotate_token("nonexistent-jti")

    @pytest.mark.asyncio
    async def test_rotate_inactive_token(self, auth_manager):
        """Test rotating an inactive token raises error."""
        await auth_manager.create_service_account(
            service_name="test-service",
            namespace="test-namespace",
        )

        _, original_token = await auth_manager.generate_service_token(
            service_id="test-namespace/test-service",
            token_type="access",
        )
        original_token.active = False

        with pytest.raises(ValueError, match="not active"):
            await auth_manager.rotate_token(original_token.jti)

    @pytest.mark.asyncio
    async def test_revoke_token(self, auth_manager):
        """Test revoking a token."""
        await auth_manager.create_service_account(
            service_name="test-service",
            namespace="test-namespace",
        )

        _, token = await auth_manager.generate_service_token(
            service_id="test-namespace/test-service",
            token_type="access",
        )

        await auth_manager.revoke_token(token.jti)
        
        assert token.active is False

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_token(self, auth_manager):
        """Test revoking a nonexistent token raises error."""
        with pytest.raises(ValueError, match="not found"):
            await auth_manager.revoke_token("nonexistent-jti")

    @pytest.mark.asyncio
    async def test_get_active_tokens(self, auth_manager):
        """Test getting active tokens."""
        await auth_manager.create_service_account(
            service_name="test-service",
            namespace="test-namespace",
        )

        await auth_manager.generate_service_token(
            service_id="test-namespace/test-service",
            token_type="access",
        )
        await auth_manager.generate_service_token(
            service_id="test-namespace/test-service",
            token_type="refresh",
        )

        tokens = auth_manager.get_active_tokens("test-namespace/test-service")
        assert len(tokens) == 2

        all_tokens = auth_manager.get_active_tokens()
        assert len(all_tokens) == 2

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens(self, auth_manager):
        """Test cleaning up expired tokens."""
        await auth_manager.create_service_account(
            service_name="test-service",
            namespace="test-namespace",
        )

        # Create tokens with different expiration times
        _, expired_token = await auth_manager.generate_service_token(
            service_id="test-namespace/test-service",
            token_type="access",
        )
        expired_token.expires_at = datetime.utcnow() - timedelta(hours=1)

        _, active_token = await auth_manager.generate_service_token(
            service_id="test-namespace/test-service",
            token_type="access",
        )

        cleaned_count = await auth_manager.cleanup_expired_tokens()
        
        assert cleaned_count == 1
        assert expired_token.jti not in auth_manager._active_tokens
        assert active_token.jti in auth_manager._active_tokens


class TestServiceAuthIntegration:
    """Integration tests for service authentication."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, auth_manager):
        """Test complete service account and token lifecycle."""
        # Create service account
        service_account = await auth_manager.create_service_account(
            service_name="integration-service",
            namespace="test-namespace",
            roles=["integration-role"],
            permissions=["integration-permission"],
        )

        # Generate token
        token_string, token_info = await auth_manager.generate_service_token(
            service_id=service_account.service_id,
            token_type="access",
            scopes=["integration-scope"],
        )

        # Verify token
        claims = await auth_manager.verify_service_token(token_string)
        assert claims["sub"] == service_account.service_id
        assert claims["roles"] == ["integration-role"]
        assert claims["permissions"] == ["integration-permission"]
        assert claims["scopes"] == ["integration-scope"]

        # Rotate token
        new_token_string, new_token_info = await auth_manager.rotate_token(token_info.jti)
        assert new_token_string != token_string
        assert new_token_info.rotation_count == 1

        # Verify new token
        new_claims = await auth_manager.verify_service_token(new_token_string)
        assert new_claims["jti"] == new_token_info.jti

        # Revoke token
        await auth_manager.revoke_token(new_token_info.jti)
        
        # Verify token is revoked
        with pytest.raises(Exception):
            await auth_manager.verify_service_token(new_token_string)

        # Deactivate service account
        await auth_manager.deactivate_service_account(service_account.service_id)
        assert service_account.active is False

    @pytest.mark.asyncio
    async def test_token_expiration_handling(self, auth_manager):
        """Test handling of token expiration."""
        await auth_manager.create_service_account(
            service_name="expiry-service",
            namespace="test-namespace",
        )

        # Create expired token
        _, token = await auth_manager.generate_service_token(
            service_id="test-namespace/expiry-service",
            token_type="access",
        )
        token.expires_at = datetime.utcnow() - timedelta(hours=1)

        # Should fail verification
        with pytest.raises(Exception, match="expired"):
            await auth_manager.verify_service_token(token.token_id)

    @pytest.mark.asyncio
    async def test_service_account_expiration_handling(self, auth_manager):
        """Test handling of service account expiration."""
        service_account = await auth_manager.create_service_account(
            service_name="expiry-service",
            namespace="test-namespace",
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )

        # Should fail to generate token
        with pytest.raises(ValueError, match="expired"):
            await auth_manager.generate_service_token(
                service_id=service_account.service_id,
                token_type="access",
            )


@pytest.mark.asyncio
async def test_initialization_failure():
    """Test handling of initialization failure."""
    config = ServiceAuthConfig()
    
    with patch('app.core.service_auth.get_vault_client', side_effect=Exception("Vault error")):
        manager = ServiceAuthConfig()
        with pytest.raises(Exception):
            await ServiceAuthManager(config).initialize()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])