"""Logic for loading and verifying the signed SomaGent constitution."""

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from .models import ConstitutionBundle

logger = logging.getLogger(__name__)


class ConstitutionVerificationError(RuntimeError):
    """Raised when the constitution bundle fails validation."""


@dataclass(slots=True)
class VerifiedConstitution:
    """Container for a verified constitution bundle."""

    bundle: ConstitutionBundle
    canonical_document: bytes

    @property
    def hash(self) -> str:  # pragma: no cover - simple property
        return self.bundle.hash


def canonicalise_document(bundle: ConstitutionBundle) -> bytes:
    document_dict = bundle.document.model_dump()
    canonical_json = json.dumps(document_dict, separators=(",", ":"), sort_keys=True)
    return canonical_json.encode("utf-8")


def _verify_hash(bundle: ConstitutionBundle, canonical_document: bytes) -> None:
    computed_hash = sha256(canonical_document).hexdigest()
    if computed_hash != bundle.hash:
        raise ConstitutionVerificationError(
            "Constitution hash mismatch: bundle hash does not match computed hash"
        )


def _verify_signature(bundle: ConstitutionBundle, canonical_document: bytes, public_key_path: Path) -> None:
    signature_bytes = base64.b64decode(bundle.signature.value)
    public_key = serialization.load_pem_public_key(public_key_path.read_bytes())
    try:
        public_key.verify(signature_bytes, canonical_document, padding.PKCS1v15(), hashes.SHA256())
    except InvalidSignature as exc:  # pragma: no cover - defensive guard
        raise ConstitutionVerificationError("Signature verification failed") from exc


def _build_verified(bundle: ConstitutionBundle, public_key_path: Path) -> VerifiedConstitution:
    canonical_document = canonicalise_document(bundle)
    _verify_hash(bundle, canonical_document)
    _verify_signature(bundle, canonical_document, public_key_path)
    return VerifiedConstitution(bundle=bundle, canonical_document=canonical_document)


def load_verified_constitution(bundle_path: Path, public_key_path: Path) -> VerifiedConstitution:
    """Load, validate, and return the signed constitution bundle."""

    try:
        raw = json.loads(bundle_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConstitutionVerificationError(f"Constitution bundle not found at {bundle_path}") from exc

    bundle = ConstitutionBundle.model_validate(raw)
    verified = _build_verified(bundle, public_key_path)
    logger.info(
        "Loaded constitution bundle version=%s issued_at=%s hash=%s",
        bundle.version,
        bundle.issued_at.isoformat(),
        bundle.hash,
    )
    return verified


def normalise_tenant(tenant: str) -> str:
    return tenant.strip().lower()


class ConstitutionRegistry:
    """In-memory registry that serves the verified constitution for all tenants."""

    def __init__(self, verified: VerifiedConstitution, tenants: Iterable[str] | None = None) -> None:
        self._verified = verified
        tenant_set = {normalise_tenant(t) for t in (tenants or {"global"})}
        if not tenant_set:
            tenant_set.add("global")
        self._tenants = tenant_set

    @property
    def bundle(self) -> ConstitutionBundle:
        return self._verified.bundle

    def list_tenants(self) -> list[str]:  # pragma: no cover - simple accessor
        return sorted(self._tenants)

    def get_bundle(self, tenant: str) -> ConstitutionBundle:
        tenant_key = normalise_tenant(tenant)
        if tenant_key not in self._tenants:
            logger.debug("Tenant %s not explicitly registered; serving global constitution", tenant)
        return self._verified.bundle

    def get_hash(self, tenant: str) -> str:
        self.get_bundle(tenant)  # ensure tenant normalisation/logging
        return self._verified.hash

    def update(self, verified: VerifiedConstitution) -> None:
        self._verified = verified


def build_verified_from_bundle(bundle: ConstitutionBundle, public_key_path: Path) -> VerifiedConstitution:
    """Validate *bundle* and return a :class:`VerifiedConstitution`."""

    return _build_verified(bundle, public_key_path)


def verify_bundle(bundle: ConstitutionBundle, public_key_path: Path) -> None:
    canonical = canonicalise_document(bundle)
    _verify_hash(bundle, canonical)
    _verify_signature(bundle, canonical, public_key_path)
