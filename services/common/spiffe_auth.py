"""SPIFFE/SPIRE authentication for zero-trust mTLS."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

import grpc

logger = logging.getLogger(__name__)


@dataclass
class SPIFFEIdentity:
    """SPIFFE identity information."""

    spiffe_id: str
    trust_domain: str
    service_name: str
    cert_path: str
    key_path: str
    bundle_path: str


class SPIFFEAuthenticator:
    """Manages SPIFFE-based service authentication."""

    def __init__(self, socket_path: str = "unix:///run/spire/sockets/agent.sock"):
        """Initialize SPIFFE authenticator."""

        self.socket_path = os.getenv("SPIFFE_WORKLOAD_SOCKET", socket_path)
        self.identity: SPIFFEIdentity | None = None

        # Default paths for X.509 materials
        cert_dir_path = os.getenv("SPIFFE_CERT_DIR", "/tmp/spiffe")
        self.cert_dir = Path(cert_dir_path)
        try:
            self.cert_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Fallback to /tmp if /var/run/secrets is not writable
            self.cert_dir = Path("/tmp/spiffe")
            self.cert_dir.mkdir(parents=True, exist_ok=True)

    def fetch_identity(self, service_name: str) -> SPIFFEIdentity:
        """
        Fetch SPIFFE identity from Workload API.

        Args:
            service_name: Name of the service requesting identity

        Returns:
            SPIFFEIdentity with certificate paths
        """
        trust_domain = os.getenv("SPIFFE_TRUST_DOMAIN", "somaagent.io")
        spiffe_id = f"spiffe://{trust_domain}/service/{service_name}"

        # In production, this would use the SPIRE Workload API
        # For now, we use the mounted certificate paths from SPIRE agent
        identity = SPIFFEIdentity(
            spiffe_id=spiffe_id,
            trust_domain=trust_domain,
            service_name=service_name,
            cert_path=str(self.cert_dir / "svid.pem"),
            key_path=str(self.cert_dir / "svid_key.pem"),
            bundle_path=str(self.cert_dir / "bundle.pem")
        )

        missing = [path for path in (identity.cert_path, identity.key_path, identity.bundle_path) if not Path(path).exists()]
        if missing:
            raise FileNotFoundError("Missing SPIFFE materials: " + ", ".join(missing))

        self.identity = identity
        logger.info(f"Fetched SPIFFE identity: {spiffe_id}")
        return identity

    def get_tls_credentials(self) -> tuple[bytes, bytes, bytes]:
        """
        Get TLS credentials for mTLS connections.

        Returns:
            Tuple of (certificate, private_key, ca_bundle)
        """
        if not self.identity:
            raise RuntimeError("Identity not fetched. Call fetch_identity() first.")

        cert = Path(self.identity.cert_path).read_bytes()
        key = Path(self.identity.key_path).read_bytes()
        bundle = Path(self.identity.bundle_path).read_bytes()

        return cert, key, bundle

    def create_grpc_credentials(self) -> grpc.ChannelCredentials:
        """
        Create gRPC credentials for mTLS.

        Returns:
            gRPC ChannelCredentials configured for mTLS
        """
        cert, key, bundle = self.get_tls_credentials()

        return grpc.ssl_channel_credentials(
            root_certificates=bundle,
            private_key=key,
            certificate_chain=cert
        )

    def verify_peer(self, peer_spiffe_id: str) -> bool:
        """
        Verify peer's SPIFFE identity.

        Args:
            peer_spiffe_id: SPIFFE ID to verify

        Returns:
            True if peer is authorized
        """
        if not self.identity:
            return False

        # Check same trust domain
        expected_prefix = f"spiffe://{self.identity.trust_domain}/"
        if not peer_spiffe_id.startswith(expected_prefix):
            logger.warning(f"Peer {peer_spiffe_id} not in trust domain")
            return False

        logger.debug(f"Verified peer: {peer_spiffe_id}")
        return True

    def rotate_certificates(self) -> None:
        """Trigger certificate rotation via Workload API."""
        # SPIRE agent handles automatic rotation
        # This method can be used to force immediate rotation
        logger.info("Certificate rotation requested")
        self.fetch_identity(self.identity.service_name)


# Global authenticator instance
_authenticator: SPIFFEAuthenticator | None = None


def get_authenticator() -> SPIFFEAuthenticator:
    """Get or create global SPIFFE authenticator."""
    global _authenticator
    if _authenticator is None:
        _authenticator = SPIFFEAuthenticator()
    return _authenticator


def init_spiffe(service_name: str, *, optional: bool = True) -> SPIFFEIdentity | None:
    """
    Initialize SPIFFE authentication for a service.

    Args:
        service_name: Name of the service

    Returns:
        SPIFFEIdentity for the service
    """
    enabled = os.getenv("ENABLE_SPIFFE", "false").lower() == "true"
    if not enabled:
        logger.info("SPIFFE initialization skipped: ENABLE_SPIFFE is false")
        return None

    auth = get_authenticator()
    try:
        identity = auth.fetch_identity(service_name)
    except FileNotFoundError as exc:
        logger.warning("SPIFFE identity material not found for %s: %s", service_name, exc)
        if optional:
            return None
        raise
    except Exception as exc:  # pragma: no cover - defensive path
        logger.warning("SPIFFE initialization failed for %s: %s", service_name, exc)
        if optional:
            return None
        raise

    return identity
