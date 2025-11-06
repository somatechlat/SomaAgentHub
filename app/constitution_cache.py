"""Top-level shim for app.constitution_cache.

Re-exports the constitution cache implementation from the policy-engine service.
Tests that import ``from app.constitution_cache import get_cached_hash, invalidate_hash``
will receive the concrete implementation from ``services.policy-engine.app.constitution_cache``.
"""

from __future__ import annotations

try:
    # Import from the policy-engine service
    from services.policy_engine.app.constitution_cache import (
        get_cached_hash,
        invalidate_hash,
    )
    
    __all__ = ["get_cached_hash", "invalidate_hash"]
except ImportError:
    # Fallback if policy-engine is not available
    import warnings
    warnings.warn(
        "policy-engine service not available; app.constitution_cache functionality limited",
        ImportWarning,
    )
    
    # Provide stub implementations
    async def get_cached_hash(tenant: str) -> str:  # type: ignore
        """Stub get_cached_hash when service is unavailable."""
        return "stub-hash-placeholder"
    
    async def invalidate_hash(tenant: str) -> None:  # type: ignore
        """Stub invalidate_hash when service is unavailable."""
        pass
    
    __all__ = ["get_cached_hash", "invalidate_hash"]
