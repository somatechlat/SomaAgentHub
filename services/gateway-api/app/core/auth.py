"""JWT authentication utilities for gateway."""

from __future__ import annotations

import os
from typing import Any, Dict

import jwt
from fastapi import HTTPException, status

from .config import get_settings


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT token.
    
    If KEYCLOAK_SERVER_URL is configured, use Keycloak validation.
    Otherwise, fall back to simple JWT validation (for development).
    """
    settings = get_settings()
    
    # Check if Keycloak is configured
    keycloak_url = os.getenv("KEYCLOAK_SERVER_URL")
    
    if keycloak_url:
        # Use Keycloak validation
        try:
            from services.common.keycloak_client import get_keycloak_client
            keycloak_client = get_keycloak_client()
            claims = keycloak_client.validate_token(token)
            return claims
        except Exception as exc:
            # If Keycloak import fails or validation fails, raise auth error
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Keycloak token validation failed: {str(exc)}"
            ) from exc
    
    # Fall back to simple JWT validation (development mode)
    secret = settings.resolve_jwt_secret()
    try:
        data = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    required_fields = {"sub", "tenant_id", "capabilities"}
    if not required_fields.issubset(data):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incomplete token claims")
    return data
