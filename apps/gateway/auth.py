"""JWT authentication helper for Django gateway."""

from __future__ import annotations

import logging
from typing import Any

import httpx
import jwt
from django.conf import settings

logger = logging.getLogger(__name__)


class JWKSVerifier:
    """Fetch and verify JWTs using identity-service JWKS."""

    def __init__(self, jwks_url: str):
        self.jwks_url = jwks_url
        self._client = jwt.PyJWKClient(jwks_url)

    async def verify(self, token: str) -> dict[str, Any]:
        signing_key = self._client.get_signing_key_from_jwt(token).key
        # Audience is not enforced in current identity-service; skip verify_aud
        return jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )


async def fetch_jwks_url() -> str:
    """Discover JWKS URL from identity-service OIDC metadata."""
    base = settings.IDENTITY_URL.rstrip("/")
    discovery = f"{base}/.well-known/openid-configuration"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(discovery)
            resp.raise_for_status()
            data = resp.json()
            jwks_uri = data.get("jwks_uri")
            if jwks_uri:
                return jwks_uri
    except Exception as exc:
        logger.warning("Failed to discover JWKS: %s", exc)
    # Fallback to default path
    return f"{base}/.well-known/jwks.json"
