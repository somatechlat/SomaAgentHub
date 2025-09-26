"""API routes for the Constitution service.

Provides a simple endpoint to retrieve the constitution hash for a tenant.
In a real deployment this would fetch the signed constitution from SomaBrain
and cache the hash in Redis. For now we return a deterministic placeholder
or, if Redis is available, read ``constitution:{tenant}``.
"""

from fastapi import APIRouter, HTTPException, status
# Import the async helper from the sibling redis_client module.
from ...redis_client import get_constitution_hash

router = APIRouter(prefix="/v1", tags=["constitution"])

@router.get("/constitution/{tenant}", response_model=str)
async def get_constitution(tenant: str):
    """Return the constitution hash for *tenant*.

    The underlying ``get_constitution_hash`` is async, so we simply await it.
    FastAPI will handle the coroutine correctly.
    """
    try:
        hash_val = await get_constitution_hash(tenant)
        return hash_val
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))
