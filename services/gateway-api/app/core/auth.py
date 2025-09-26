"""JWT authentication utilities for gateway."""

from __future__ import annotations

from typing import Any, Dict

import jwt
from fastapi import HTTPException, status

from .config import get_settings


def decode_token(token: str) -> Dict[str, Any]:
    settings = get_settings()
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
