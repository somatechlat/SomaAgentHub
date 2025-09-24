"""Dependencies for gateway routes."""

from fastapi import Depends, HTTPException, status

from .core.context import get_request_context
from .models.context import RequestContext


def request_context_dependency() -> RequestContext:
    ctx = get_request_context()
    if ctx is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Request context missing")
    return ctx
