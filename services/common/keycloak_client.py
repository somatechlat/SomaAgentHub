"""Keycloak OIDC client wrapper for SomaGent platform.

This module provides a reusable Keycloak client that can validate JWT tokens
and retrieve user information. It uses the python-keycloak library.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, Optional
from functools import lru_cache

from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakError
from fastapi import HTTPException, status


# Ensure module can be accessed via both 'keycloak_client' and 'services.common.keycloak_client' for testing patches
sys.modules.setdefault('services.common.keycloak_client', sys.modules[__name__])


class KeycloakClient:
    """Wrapper for Keycloak OpenID Connect operations."""

    def __init__(
        self,
        server_url: str,
        realm_name: str,
        client_id: str,
        client_secret: Optional[str] = None,
    ):
        """Initialize Keycloak client.
        
        Args:
            server_url: Keycloak server URL (e.g., https://keycloak.example.com/auth/)
            realm_name: Keycloak realm name
            client_id: Client ID for this application
            client_secret: Client secret (optional, for confidential clients)
        """
        self.server_url = server_url
        self.realm_name = realm_name
        self.client_id = client_id
        self.client_secret = client_secret
        
        self._oidc_client = KeycloakOpenID(
            server_url=server_url,
            realm_name=realm_name,
            client_id=client_id,
            client_secret_key=client_secret,
        )

    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate a JWT token and return decoded claims.
        
        Args:
            token: JWT token string (without "Bearer " prefix)
            
        Returns:
            Dictionary containing token claims (sub, tenant_id, capabilities, etc.)
            
        Raises:
            HTTPException: If token is invalid, expired, or malformed
        """
        try:
            # Validate token signature and expiration using Keycloak's public key
            userinfo = self._oidc_client.userinfo(token)
            
            # Also decode the token to get all claims
            token_info = self._oidc_client.decode_token(
                token,
                validate=True,
                options={"verify_signature": True, "verify_aud": False, "verify_exp": True}
            )
            
            # Merge userinfo and token_info to provide complete claims
            claims = {**token_info, **userinfo}
            
            # Ensure required fields are present
            required_fields = {"sub", "preferred_username"}
            if not required_fields.issubset(claims.keys()):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Incomplete token claims: missing {required_fields - claims.keys()}"
                )
            
            # Map Keycloak claims to SomaGent expected format
            # Extract tenant_id from custom claim or realm role
            tenant_id = claims.get("tenant_id") or claims.get("azp") or "default"
            capabilities = claims.get("capabilities", [])
            
            # If capabilities is in realm_access or resource_access, extract it
            if not capabilities and "realm_access" in claims:
                capabilities = claims["realm_access"].get("roles", [])
            
            return {
                "sub": claims["sub"],
                "tenant_id": tenant_id,
                "user_id": claims.get("preferred_username", claims["sub"]),
                "email": claims.get("email"),
                "capabilities": capabilities,
                "name": claims.get("name"),
                "raw_claims": claims,
            }
            
        except KeycloakError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation failed: {str(exc)}"
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(exc)}"
            ) from exc

    def get_public_key(self) -> str:
        """Retrieve the realm's public key for offline token validation."""
        try:
            return self._oidc_client.public_key()
        except KeycloakError as exc:
            raise RuntimeError(f"Failed to fetch Keycloak public key: {exc}") from exc

    def introspect_token(self, token: str) -> Dict[str, Any]:
        """Introspect a token to check its validity and get metadata.
        
        This makes a server-side call to Keycloak for token introspection.
        """
        try:
            result = self._oidc_client.introspect(token)
            if not result.get("active"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token is not active"
                )
            return result
        except KeycloakError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token introspection failed: {str(exc)}"
            ) from exc


@lru_cache
def get_keycloak_client() -> KeycloakClient:
    """Return a cached Keycloak client instance from environment variables.
    
    Required environment variables:
        KEYCLOAK_SERVER_URL: Keycloak server URL
        KEYCLOAK_REALM: Realm name
        KEYCLOAK_CLIENT_ID: Client ID
        KEYCLOAK_CLIENT_SECRET: Client secret (optional)
    """
    server_url = os.getenv("KEYCLOAK_SERVER_URL")
    realm = os.getenv("KEYCLOAK_REALM")
    client_id = os.getenv("KEYCLOAK_CLIENT_ID")
    client_secret = os.getenv("KEYCLOAK_CLIENT_SECRET")
    
    if not server_url or not realm or not client_id:
        raise RuntimeError(
            "Keycloak configuration incomplete. Required: KEYCLOAK_SERVER_URL, "
            "KEYCLOAK_REALM, KEYCLOAK_CLIENT_ID"
        )
    
    return KeycloakClient(
        server_url=server_url,
        realm_name=realm,
        client_id=client_id,
        client_secret=client_secret,
    )
