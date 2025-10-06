"""Manifest signing helpers for persona exports and constitution updates."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Optional

from .config import settings

try:  # pragma: no cover - optional cryptography dependency
    from nacl.signing import SigningKey, VerifyKey  # type: ignore
except Exception:  # pragma: no cover - fallback when PyNaCl is unavailable
    SigningKey = None
    VerifyKey = None


@dataclass(slots=True)
class SignatureBundle:
    """Encapsulates a detached signature and metadata."""

    algorithm: str
    signature: str
    public_key: str


class ManifestSigningError(RuntimeError):
    """Raised when signing or verification fails."""


class ManifestSigner:
    """Thin wrapper around Ed25519 signing for persona manifests."""

    def __init__(self, private_key: bytes, *, public_key: Optional[bytes] = None) -> None:
        if SigningKey is None:
            raise ManifestSigningError(
                "PyNaCl is required for signing manifests. Install with `pip install pynacl`."
            )
        self._signing_key = SigningKey(private_key)
        self._verify_key = VerifyKey(public_key or self._signing_key.verify_key.encode())

    @property
    def public_key(self) -> bytes:
        return self._verify_key.encode()

    def sign(self, payload: bytes) -> SignatureBundle:
        signed = self._signing_key.sign(payload)
        return SignatureBundle(
            algorithm="ed25519",
            signature=base64.b64encode(signed.signature).decode("utf-8"),
            public_key=base64.b64encode(self.public_key).decode("utf-8"),
        )

    def verify(self, payload: bytes, signature_b64: str, *, public_key_b64: Optional[str] = None) -> bool:
        key = self._verify_key
        if public_key_b64:
            if VerifyKey is None:
                raise ManifestSigningError("PyNaCl required for verification")
            key = VerifyKey(base64.b64decode(public_key_b64))
        signature = base64.b64decode(signature_b64)
        try:
            key.verify(payload, signature)
        except Exception:  # pragma: no cover - PyNaCl exception details vary
            return False
        return True


def load_signer_from_env() -> ManifestSigner:
    """Instantiate a manifest signer from environment or service settings."""

    private_key_path = settings.private_key_path or os.getenv("SOMAGENT_SIGNING_KEY")
    if not private_key_path or not os.path.exists(private_key_path):
        raise ManifestSigningError("Manifest signing key not configured")
    with open(private_key_path, "rb") as handle:
        private_key = handle.read().strip()
    public_key_path = settings.public_key_path or os.getenv("SOMAGENT_PUBLIC_KEY")
    public_key_bytes: Optional[bytes] = None
    if public_key_path and os.path.exists(public_key_path):
        with open(public_key_path, "rb") as handle:
            public_key_bytes = handle.read().strip()
    return ManifestSigner(private_key, public_key=public_key_bytes)
