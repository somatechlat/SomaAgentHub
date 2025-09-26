"""Release verification helpers."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


def _canonical_json(obj: Any) -> bytes:
    """Return canonical JSON bytes for deterministic hashing."""

    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def compute_manifest_digest(manifest: Any) -> str:
    """Compute SHA-256 digest of adapter manifest metadata."""

    return hashlib.sha256(_canonical_json(manifest)).hexdigest()


def compute_release_signature(
    adapter_id: str,
    version: str,
    secret: str,
    *,
    manifest_digest: str | None = None,
) -> str:
    """Return HMAC signature for the adapter release (including manifest digest)."""

    payload = f"{adapter_id}:{version}:{manifest_digest or ''}"
    digest = hmac.new(secret.encode(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"sha256:{digest}"


def verify_release_signature(adapter_metadata: dict[str, Any], secret: str) -> bool:
    """Validate adapter signature + optional manifest digest."""

    adapter_id = adapter_metadata.get("id")
    version = adapter_metadata.get("version")
    signature = adapter_metadata.get("signature")
    manifest = adapter_metadata.get("manifest")
    manifest_digest = adapter_metadata.get("manifest_digest")

    if not adapter_id or not version or not signature:
        return False

    if manifest is not None:
        computed_digest = compute_manifest_digest(manifest)
        if manifest_digest != computed_digest:
            return False
    elif manifest_digest:
        return False
    else:
        computed_digest = None

    expected = compute_release_signature(
        adapter_id,
        version,
        secret,
        manifest_digest=computed_digest,
    )
    return hmac.compare_digest(expected, signature)
