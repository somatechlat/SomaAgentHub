"""
Service Authentication API Endpoints.

Enterprise-grade API for service-to-service authentication management.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from ..core.service_auth import (
    ServiceAccount,
    ServiceAuthConfig,
    ServiceAuthManager,
    ServiceToken,
)

logger = logging.getLogger(__name__)

# Security scheme for API authentication
security = HTTPBearer()

# Global service auth manager instance
_service_auth_manager: Optional[ServiceAuthManager] = None


def get_service_auth_manager() -> ServiceAuthManager:
    """Get the global service authentication manager."""
    global _service_auth_manager
    if _service_auth_manager is None:
        config = ServiceAuthConfig()
        _service_auth_manager = ServiceAuthManager(config)
    return _service_auth_manager


async def get_current_service(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> Dict:
    """
    Get the current authenticated service from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        Decoded token claims
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        auth_manager = get_service_auth_manager()
        claims = await auth_manager.verify_service_token(credentials.credentials)
        return claims
    except Exception as e:
        logger.error(f"Service authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")


# Pydantic models for API
class CreateServiceAccountRequest(BaseModel):
    """Request model for creating a service account."""

    service_name: str = Field(..., description="Name of the service")
    namespace: str = Field(..., description="Kubernetes namespace")
    roles: List[str] = Field(default_factory=list, description="List of roles")
    permissions: List[str] = Field(default_factory=list, description="List of permissions")
    expires_at: Optional[str] = Field(None, description="Expiration date (ISO format)")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")


class CreateServiceAccountResponse(BaseModel):
    """Response model for creating a service account."""

    success: bool
    service_account: Optional[ServiceAccount] = None
    error_message: Optional[str] = None


class GenerateTokenRequest(BaseModel):
    """Request model for generating a service token."""

    service_id: str = Field(..., description="Service account ID")
    token_type: str = Field(default="access", description="Token type (access, refresh, service)")
    scopes: List[str] = Field(default_factory=list, description="List of scopes")


class GenerateTokenResponse(BaseModel):
    """Response model for generating a service token."""

    success: bool
    token: Optional[str] = None
    token_info: Optional[ServiceToken] = None
    error_message: Optional[str] = None


class VerifyTokenResponse(BaseModel):
    """Response model for verifying a service token."""

    valid: bool
    claims: Optional[Dict] = None
    error_message: Optional[str] = None


class RotateTokenResponse(BaseModel):
    """Response model for rotating a service token."""

    success: bool
    new_token: Optional[str] = None
    new_token_info: Optional[ServiceToken] = None
    error_message: Optional[str] = None


class RevokeTokenRequest(BaseModel):
    """Request model for revoking a service token."""

    token_jti: str = Field(..., description="JTI of the token to revoke")


class RevokeTokenResponse(BaseModel):
    """Response model for revoking a service token."""

    success: bool
    error_message: Optional[str] = None


class DeactivateServiceAccountRequest(BaseModel):
    """Request model for deactivating a service account."""

    service_id: str = Field(..., description="Service account ID")


class DeactivateServiceAccountResponse(BaseModel):
    """Response model for deactivating a service account."""

    success: bool
    error_message: Optional[str] = None


class ServiceAccountListResponse(BaseModel):
    """Response model for listing service accounts."""

    service_accounts: List[ServiceAccount]
    total: int


class TokenListResponse(BaseModel):
    """Response model for listing tokens."""

    tokens: List[ServiceToken]
    total: int


# Create router
router = APIRouter(prefix="/service-auth", tags=["service-authentication"])


@router.post("/accounts", response_model=CreateServiceAccountResponse)
async def create_service_account(
    request: CreateServiceAccountRequest,
    current_service: Dict = Depends(get_current_service),
):
    """
    Create a new service account.
    
    Requires authentication and appropriate permissions.
    """
    try:
        auth_manager = get_service_auth_manager()
        
        # Check if current service has permission to create service accounts
        if "service-admin" not in current_service.get("roles", []):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Parse expiration date if provided
        expires_at = None
        if request.expires_at:
            from datetime import datetime
            expires_at = datetime.fromisoformat(request.expires_at.replace("Z", "+00:00"))
        
        # Create service account
        service_account = await auth_manager.create_service_account(
            service_name=request.service_name,
            namespace=request.namespace,
            roles=request.roles,
            permissions=request.permissions,
            expires_at=expires_at,
            metadata=request.metadata,
        )
        
        return CreateServiceAccountResponse(
            success=True,
            service_account=service_account,
        )
        
    except ValueError as e:
        logger.error(f"Failed to create service account: {e}")
        return CreateServiceAccountResponse(
            success=False,
            error_message=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error creating service account: {e}")
        return CreateServiceAccountResponse(
            success=False,
            error_message="Internal server error",
        )


@router.get("/accounts", response_model=ServiceAccountListResponse)
async def list_service_accounts(
    current_service: Dict = Depends(get_current_service),
):
    """
    List all service accounts.
    
    Requires authentication and appropriate permissions.
    """
    try:
        auth_manager = get_service_auth_manager()
        
        # Check if current service has permission to list service accounts
        if "service-admin" not in current_service.get("roles", []):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        service_accounts = auth_manager.list_service_accounts()
        
        return ServiceAccountListResponse(
            service_accounts=service_accounts,
            total=len(service_accounts),
        )
        
    except Exception as e:
        logger.error(f"Failed to list service accounts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/accounts/{service_id}", response_model=ServiceAccount)
async def get_service_account(
    service_id: str,
    current_service: Dict = Depends(get_current_service),
):
    """
    Get a specific service account.
    
    Requires authentication and appropriate permissions.
    """
    try:
        auth_manager = get_service_auth_manager()
        
        # Check if current service has permission to get service accounts
        if "service-admin" not in current_service.get("roles", []):
            # Allow services to get their own account
            if current_service.get("sub") != service_id:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        service_account = auth_manager.get_service_account(service_id)
        if not service_account:
            raise HTTPException(status_code=404, detail="Service account not found")
        
        return service_account
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get service account {service_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/tokens/generate", response_model=GenerateTokenResponse)
async def generate_service_token(
    request: GenerateTokenRequest,
    current_service: Dict = Depends(get_current_service),
):
    """
    Generate a service token.
    
    Requires authentication and appropriate permissions.
    """
    try:
        auth_manager = get_service_auth_manager()
        
        # Check if current service has permission to generate tokens
        if "service-admin" not in current_service.get("roles", []):
            # Allow services to generate tokens for themselves
            if current_service.get("sub") != request.service_id:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Generate token
        token_string, token_info = await auth_manager.generate_service_token(
            service_id=request.service_id,
            token_type=request.token_type,
            scopes=request.scopes,
        )
        
        return GenerateTokenResponse(
            success=True,
            token=token_string,
            token_info=token_info,
        )
        
    except ValueError as e:
        logger.error(f"Failed to generate token: {e}")
        return GenerateTokenResponse(
            success=False,
            error_message=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error generating token: {e}")
        return GenerateTokenResponse(
            success=False,
            error_message="Internal server error",
        )


@router.post("/tokens/verify", response_model=VerifyTokenResponse)
async def verify_service_token(
    token: str,
    current_service: Dict = Depends(get_current_service),
):
    """
    Verify a service token.
    
    Requires authentication and appropriate permissions.
    """
    try:
        auth_manager = get_service_auth_manager()
        
        # Check if current service has permission to verify tokens
        if "service-admin" not in current_service.get("roles", []):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Verify token
        claims = await auth_manager.verify_service_token(token)
        
        return VerifyTokenResponse(
            valid=True,
            claims=claims,
        )
        
    except Exception as e:
        logger.error(f"Failed to verify token: {e}")
        return VerifyTokenResponse(
            valid=False,
            error_message=str(e),
        )


@router.post("/tokens/rotate", response_model=RotateTokenResponse)
async def rotate_service_token(
    token_jti: str,
    current_service: Dict = Depends(get_current_service),
):
    """
    Rotate a service token.
    
    Requires authentication and appropriate permissions.
    """
    try:
        auth_manager = get_service_auth_manager()
        
        # Check if current service has permission to rotate tokens
        if "service-admin" not in current_service.get("roles", []):
            # Allow services to rotate their own tokens
            token = auth_manager._active_tokens.get(token_jti)
            if not token or token.service_id != current_service.get("sub"):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Rotate token
        new_token, new_token_info = await auth_manager.rotate_token(token_jti)
        
        return RotateTokenResponse(
            success=True,
            new_token=new_token,
            new_token_info=new_token_info,
        )
        
    except ValueError as e:
        logger.error(f"Failed to rotate token: {e}")
        return RotateTokenResponse(
            success=False,
            error_message=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error rotating token: {e}")
        return RotateTokenResponse(
            success=False,
            error_message="Internal server error",
        )


@router.post("/tokens/revoke", response_model=RevokeTokenResponse)
async def revoke_service_token(
    request: RevokeTokenRequest,
    current_service: Dict = Depends(get_current_service),
):
    """
    Revoke a service token.
    
    Requires authentication and appropriate permissions.
    """
    try:
        auth_manager = get_service_auth_manager()
        
        # Check if current service has permission to revoke tokens
        if "service-admin" not in current_service.get("roles", []):
            # Allow services to revoke their own tokens
            token = auth_manager._active_tokens.get(request.token_jti)
            if not token or token.service_id != current_service.get("sub"):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Revoke token
        await auth_manager.revoke_token(request.token_jti)
        
        return RevokeTokenResponse(
            success=True,
        )
        
    except ValueError as e:
        logger.error(f"Failed to revoke token: {e}")
        return RevokeTokenResponse(
            success=False,
            error_message=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error revoking token: {e}")
        return RevokeTokenResponse(
            success=False,
            error_message="Internal server error",
        )


@router.post("/accounts/deactivate", response_model=DeactivateServiceAccountResponse)
async def deactivate_service_account(
    request: DeactivateServiceAccountRequest,
    current_service: Dict = Depends(get_current_service),
):
    """
    Deactivate a service account.
    
    Requires authentication and appropriate permissions.
    """
    try:
        auth_manager = get_service_auth_manager()
        
        # Check if current service has permission to deactivate service accounts
        if "service-admin" not in current_service.get("roles", []):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Deactivate service account
        await auth_manager.deactivate_service_account(request.service_id)
        
        return DeactivateServiceAccountResponse(
            success=True,
        )
        
    except ValueError as e:
        logger.error(f"Failed to deactivate service account: {e}")
        return DeactivateServiceAccountResponse(
            success=False,
            error_message=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error deactivating service account: {e}")
        return DeactivateServiceAccountResponse(
            success=False,
            error_message="Internal server error",
        )


@router.get("/tokens", response_model=TokenListResponse)
async def list_service_tokens(
    service_id: Optional[str] = None,
    current_service: Dict = Depends(get_current_service),
):
    """
    List active service tokens.
    
    Requires authentication and appropriate permissions.
    """
    try:
        auth_manager = get_service_auth_manager()
        
        # Check if current service has permission to list tokens
        if "service-admin" not in current_service.get("roles", []):
            # Allow services to list their own tokens
            if service_id and service_id != current_service.get("sub"):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            # If no service_id specified, default to current service
            service_id = current_service.get("sub")
        
        # Get tokens
        tokens = auth_manager.get_active_tokens(service_id)
        
        return TokenListResponse(
            tokens=tokens,
            total=len(tokens),
        )
        
    except Exception as e:
        logger.error(f"Failed to list tokens: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/tokens/cleanup")
async def cleanup_expired_tokens(
    current_service: Dict = Depends(get_current_service),
):
    """
    Clean up expired tokens.
    
    Requires authentication and appropriate permissions.
    """
    try:
        auth_manager = get_service_auth_manager()
        
        # Check if current service has permission to cleanup tokens
        if "service-admin" not in current_service.get("roles", []):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Clean up expired tokens
        cleaned_count = await auth_manager.cleanup_expired_tokens()
        
        return {
            "success": True,
            "cleaned_count": cleaned_count,
            "message": f"Cleaned up {cleaned_count} expired tokens",
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired tokens: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def service_auth_health():
    """Health check endpoint for service authentication."""
    try:
        auth_manager = get_service_auth_manager()
        service_accounts = auth_manager.list_service_accounts()
        active_tokens = auth_manager.get_active_tokens()
        
        return {
            "status": "healthy",
            "service_accounts_count": len(service_accounts),
            "active_tokens_count": len(active_tokens),
            "initialized": auth_manager._initialized,
        }
        
    except Exception as e:
        logger.error(f"Service authentication health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }