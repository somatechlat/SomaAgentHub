"""Top-level shim for app.core.constitution.

Re-exports the constitution verification implementation from the constitution-service.
Tests that import ``from app.core.constitution import verify_bundle`` will receive
the concrete implementation from ``services.constitution-service.app.core.constitution``.
"""

from __future__ import annotations

try:
    # Import from the constitution-service
    from services.constitution_service.app.core.constitution import (
        ConstitutionVerificationError,
        VerifiedConstitution,
        canonicalise_document,
        verify_bundle,
    )
    
    __all__ = [
        "ConstitutionVerificationError",
        "VerifiedConstitution", 
        "canonicalise_document",
        "verify_bundle",
    ]
except ImportError:
    # Fallback if constitution-service is not available
    import warnings
    warnings.warn(
        "constitution-service not available; app.core.constitution functionality limited",
        ImportWarning,
    )
    
    # Provide stub implementations
    class ConstitutionVerificationError(RuntimeError):  # type: ignore
        """Stub ConstitutionVerificationError when service is unavailable."""
        pass
    
    class VerifiedConstitution:  # type: ignore
        """Stub VerifiedConstitution when service is unavailable."""
        pass
    
    def canonicalise_document(*args, **kwargs):  # type: ignore
        """Stub canonicalise_document when service is unavailable."""
        raise ImportError("constitution-service not available")
    
    def verify_bundle(*args, **kwargs):  # type: ignore
        """Stub verify_bundle when service is unavailable."""
        raise ImportError("constitution-service not available")
    
    __all__ = [
        "ConstitutionVerificationError",
        "VerifiedConstitution",
        "canonicalise_document",
        "verify_bundle",
    ]
