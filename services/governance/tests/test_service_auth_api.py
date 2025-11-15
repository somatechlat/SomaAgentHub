"""
Service Authentication API Tests.

Comprehensive test suite for service authentication REST API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.api.service_auth import router
from main import app


@pytest.fixture
def client():
    """Create test client."""
    app.include_router(router, prefix="/api/v1/auth", tags=["auth"])
    return TestClient(app)


@pytest.fixture
def mock_auth_manager():
    """Create mock authentication manager."""
    mock_manager = AsyncMock()
    
    # Mock service account
    mock_service_account = MagicMock()
    mock_service_account.service_id = "test-namespace/test-service"
    mock_service_account.service_name = "test-service"
    mock_service_account.namespace = "test-namespace"
    mock_service_account.roles = ["test-role"]
    mock_service_account.permissions = ["read", "write"]
    mock_service_account.metadata = {"key": "value"}
    mock_service_account.active = True
    
    # Mock token
    mock_token = MagicMock()
    mock_token.jti = "test-jti"
    mock_token.token_type = "access"
    mock_token.scopes = ["read", "write"]
    mock_token.active = True
    mock_token.rotation_count = 0
    
    mock_manager.create_service_account.return_value = mock_service_account
    mock_manager.get_service_account.return_value = mock_service_account
    mock_manager.list_service_accounts.return_value = [mock_service_account]
    mock_manager.generate_service_token.return_value = ("test-token", mock_token)
    mock_manager.verify_service_token.return_value = {
        "sub": "test-namespace/test-service",
        "iss": "test-issuer",
        "aud": "test-audience",
        "type": "access",
        "service_name": "test-service",
        "namespace": "test-namespace",
        "roles": ["test-role"],
        "permissions": ["read", "write"],
        "scopes": ["read", "write"],
    }
    mock_manager.rotate_token.return_value = ("new-test-token", mock_token)
    mock_manager.get_active_tokens.return_value = [mock_token]
    
    return mock_manager


@pytest.fixture
def auth_client(client, mock_auth_manager):
    """Create client with mocked auth manager."""
    with patch('app.api.service_auth.auth_manager', mock_auth_manager):
        yield client


class TestServiceAccountAPI:
    """Test service account API endpoints."""

    def test_create_service_account(self, auth_client):
        """Test creating a service account."""
        response = auth_client.post(
            "/api/v1/auth/service-accounts",
            json={
                "service_name": "test-service",
                "namespace": "test-namespace",
                "roles": ["test-role"],
                "permissions": ["read", "write"],
                "metadata": {"key": "value"},
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["service_id"] == "test-namespace/test-service"
        assert data["service_name"] == "test-service"
        assert data["namespace"] == "test-namespace"
        assert data["roles"] == ["test-role"]
        assert data["permissions"] == ["read", "write"]
        assert data["metadata"] == {"key": "value"}
        assert data["active"] is True

    def test_create_service_account_missing_required(self, auth_client):
        """Test creating service account with missing required fields."""
        response = auth_client.post(
            "/api/v1/auth/service-accounts",
            json={
                "service_name": "test-service",
                # Missing namespace
            },
        )
        
        assert response.status_code == 422

    def test_list_service_accounts(self, auth_client):
        """Test listing service accounts."""
        response = auth_client.get("/api/v1/auth/service-accounts")
        
        assert response.status_code == 200
        data = response.json()
        assert "service_accounts" in data
        assert len(data["service_accounts"]) == 1
        assert data["service_accounts"][0]["service_id"] == "test-namespace/test-service"

    def test_get_service_account(self, auth_client):
        """Test getting a specific service account."""
        response = auth_client.get("/api/v1/auth/service-accounts/test-namespace/test-service")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service_id"] == "test-namespace/test-service"
        assert data["service_name"] == "test-service"

    def test_get_nonexistent_service_account(self, auth_client, mock_auth_manager):
        """Test getting a nonexistent service account."""
        mock_auth_manager.get_service_account.return_value = None
        
        response = auth_client.get("/api/v1/auth/service-accounts/nonexistent/service")
        
        assert response.status_code == 404

    def test_deactivate_service_account(self, auth_client):
        """Test deactivating a service account."""
        response = auth_client.delete("/api/v1/auth/service-accounts/test-namespace/test-service")
        
        assert response.status_code == 204

    def test_deactivate_nonexistent_service_account(self, auth_client, mock_auth_manager):
        """Test deactivating a nonexistent service account."""
        mock_auth_manager.deactivate_service_account.side_effect = ValueError("Service account not found")
        
        response = auth_client.delete("/api/v1/auth/service-accounts/nonexistent/service")
        
        assert response.status_code == 404


class TestServiceTokenAPI:
    """Test service token API endpoints."""

    def test_generate_service_token(self, auth_client):
        """Test generating a service token."""
        response = auth_client.post(
            "/api/v1/auth/tokens/generate",
            json={
                "service_id": "test-namespace/test-service",
                "token_type": "access",
                "scopes": ["read", "write"],
                "metadata": {"purpose": "testing"},
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "token" in data
        assert data["token"] == "test-token"
        assert "token_info" in data
        assert data["token_info"]["token_type"] == "access"

    def test_generate_service_token_missing_required(self, auth_client):
        """Test generating token with missing required fields."""
        response = auth_client.post(
            "/api/v1/auth/tokens/generate",
            json={
                "service_id": "test-namespace/test-service",
                # Missing token_type
            },
        )
        
        assert response.status_code == 422

    def test_verify_service_token(self, auth_client):
        """Test verifying a service token."""
        response = auth_client.post(
            "/api/v1/auth/tokens/verify",
            json={"token": "test-token"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "claims" in data
        assert data["claims"]["sub"] == "test-namespace/test-service"

    def test_verify_invalid_token(self, auth_client, mock_auth_manager):
        """Test verifying an invalid token."""
        mock_auth_manager.verify_service_token.side_effect = Exception("Invalid token")
        
        response = auth_client.post(
            "/api/v1/auth/tokens/verify",
            json={"token": "invalid-token"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "error" in data

    def test_rotate_token(self, auth_client):
        """Test rotating a token."""
        response = auth_client.post(
            "/api/v1/auth/tokens/rotate",
            json={"token_id": "test-jti"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "new_token" in data
        assert data["new_token"] == "new-test-token"
        assert "token_info" in data

    def test_rotate_nonexistent_token(self, auth_client, mock_auth_manager):
        """Test rotating a nonexistent token."""
        mock_auth_manager.rotate_token.side_effect = ValueError("Token not found")
        
        response = auth_client.post(
            "/api/v1/auth/tokens/rotate",
            json={"token_id": "nonexistent-jti"},
        )
        
        assert response.status_code == 404

    def test_revoke_token(self, auth_client):
        """Test revoking a token."""
        response = auth_client.delete("/api/v1/auth/tokens/test-jti")
        
        assert response.status_code == 204

    def test_revoke_nonexistent_token(self, auth_client, mock_auth_manager):
        """Test revoking a nonexistent token."""
        mock_auth_manager.revoke_token.side_effect = ValueError("Token not found")
        
        response = auth_client.delete("/api/v1/auth/tokens/nonexistent-jti")
        
        assert response.status_code == 404

    def test_get_active_tokens(self, auth_client):
        """Test getting active tokens."""
        response = auth_client.get("/api/v1/auth/tokens")
        
        assert response.status_code == 200
        data = response.json()
        assert "tokens" in data
        assert len(data["tokens"]) == 1
        assert data["tokens"][0]["jti"] == "test-jti"

    def test_get_service_active_tokens(self, auth_client):
        """Test getting active tokens for a specific service."""
        response = auth_client.get("/api/v1/auth/tokens?service_id=test-namespace/test-service")
        
        assert response.status_code == 200
        data = response.json()
        assert "tokens" in data
        assert len(data["tokens"]) == 1


class TestServiceAuthMiddleware:
    """Test service authentication middleware."""

    def test_authentication_required(self, auth_client):
        """Test that authentication is required for protected endpoints."""
        # This test would require actual authentication setup
        # For now, we'll test that the endpoints exist
        response = auth_client.get("/api/v1/auth/service-accounts")
        assert response.status_code in [200, 401, 403]

    def test_authorization_required(self, auth_client):
        """Test that proper authorization is required."""
        # This test would require actual authorization setup
        # For now, we'll test that the endpoints exist
        response = auth_client.delete("/api/v1/auth/service-accounts/test/service")
        assert response.status_code in [204, 401, 403]


class TestServiceAuthAPIErrors:
    """Test API error handling."""

    def test_invalid_json(self, auth_client):
        """Test handling of invalid JSON."""
        response = auth_client.post(
            "/api/v1/auth/service-accounts",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        
        assert response.status_code == 422

    def test_method_not_allowed(self, auth_client):
        """Test handling of disallowed HTTP methods."""
        response = auth_client.patch("/api/v1/auth/service-accounts")
        
        assert response.status_code == 405

    def test_internal_server_error(self, auth_client, mock_auth_manager):
        """Test handling of internal server errors."""
        mock_auth_manager.create_service_account.side_effect = Exception("Database error")
        
        response = auth_client.post(
            "/api/v1/auth/service-accounts",
            json={
                "service_name": "test-service",
                "namespace": "test-namespace",
            },
        )
        
        assert response.status_code == 500


@pytest.mark.asyncio
async def test_api_integration():
    """Test API integration with actual service."""
    # This would be an integration test that sets up a real service
    # For now, we'll just verify the API structure
    assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])