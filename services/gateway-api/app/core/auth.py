"""Authentication utilities for the Gateway API.

This module provides a FastAPI dependency that validates a JWT token against the
Identity Service.  It is deliberately lightweight – it forwards the token to the
identity service's ``/v1/tokens/verify`` endpoint and returns the decoded claims
if the verification succeeds.

The dependency can be used in any route that requires authentication, e.g.:

```python
from .core.auth import get_current_user

@router.get("/secure-data")
def secure_endpoint(user: dict = Depends(get_current_user)):
    return {"user": user["user_id"], "tenant": user["tenant_id"]}
```

The function raises ``HTTPException`` with status 401 when the token is missing
or invalid.  It also caches the Identity Service base URL from environment
variables to avoid repeated look‑ups.
"""

from __future__ import annotations

import os
from typing import Any, Mapping

import httpx
from fastapi import Depends, Header, HTTPException, status

# The Identity Service URL can be overridden via ``IDENTITY_SERVICE_URL``.
IDENTITY_SERVICE_URL = os.getenv(
    "IDENTITY_SERVICE_URL",
    "http://identity-service:10002",
)

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    """Return a singleton async HTTP client for the Identity Service."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(base_url=IDENTITY_SERVICE_URL, timeout=5.0)
    return _client


async def _verify_token(token: str) -> Mapping[str, Any]:
    """Call the Identity Service to verify *token*.

    Returns the JSON payload from the ``/v1/tokens/verify`` endpoint on success.
    Raises ``HTTPException`` with 401 on any verification failure.
    """
    client = _get_client()
    try:
        resp = await client.post("/v1/tokens/verify", json={"token": token})
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to reach Identity Service",
        ) from exc

    if resp.status_code != 200:
        # Propagate the error message from the identity service when possible.
        try:
            detail = resp.json().get("detail", "Invalid token")
        except Exception:
            detail = "Invalid token"
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

    return resp.json()


async def get_current_user(
    authorization: str = Header(..., description="Bearer <JWT token>")
) -> Mapping[str, Any]:
    """FastAPI dependency that returns the verified user claims.

    The ``Authorization`` header must contain a ``Bearer`` token.  The token is
    forwarded to the Identity Service for verification.  On success the decoded
    token payload (as returned by the service) is returned; otherwise a 401 error
    is raised.
    """
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must be Bearer <token>",
        )
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty token provided",
        )
    return await _verify_token(token)
# ---------------------------------------------------------------------------
# Compatibility shim for the existing middleware
# ---------------------------------------------------------------------------

async def decode_token(token: str) -> dict[str, Any]:
    """Decode a JWT token using the Identity Service.

    The original implementation performed local JWT validation or delegated to
    Keycloak.  For consistency across the platform we now forward the token to
    the Identity Service ``/v1/tokens/verify`` endpoint, which returns the full
    claim set after verification.  This function is ``async`` because the HTTP
    call is asynchronous.
    """
    # Re‑use the internal verification helper which already handles errors and
    # returns a mapping of claims.
    return await _verify_token(token)
