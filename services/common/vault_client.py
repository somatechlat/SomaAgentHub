"""
HashiCorp Vault client for secrets management.

Provides secure secret storage, dynamic credentials, and automatic rotation.
Integrates with SPIFFE for authentication.
"""

import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import hvac

from services.common.config.base_settings import resolve_env

logger = logging.getLogger(__name__)


@dataclass
class VaultSecret:
    """Vault secret with metadata."""

    data: dict[str, Any]
    version: int
    created_time: datetime
    lease_duration: int = 0
    lease_id: str | None = None


    class VaultClient:
    """Client for HashiCorp Vault operations."""

    def __init__(
        self, vault_addr: str | None = None, vault_namespace: str | None = None
        ):
            """
            Initialize Vault client.

            Args:
                vault_addr: Vault server address (default: env VAULT_ADDR)
                vault_namespace: Vault namespace (default: env VAULT_NAMESPACE)
                """
                self.vault_addr = vault_addr or resolve_env("VAULT_ADDR", "http://vault:8200")
                self.vault_namespace = vault_namespace or resolve_env(
                "VAULT_NAMESPACE", "somaagent"
                )

                self._deployment_mode = (resolve_env("DEPLOYMENT_MODE", "DEV") or "DEV").upper()
                self._dev_mode = self._deployment_mode == "DEV"

# Delay client init; in DEV we may never instantiate hvac.Client
                self.client: hvac.Client | None = None
                self._authenticated = False
                self._dev_store: dict[str, dict[str, Any]] = {} if self._dev_mode else {}
                self._dev_versions: dict[str, int] = {} if self._dev_mode else {}

    def authenticate_with_k8s(
                self,
                role: str,
                jwt_path: str = "/var/run/secrets/kubernetes.io/serviceaccount/token",
                ):
                    """
                    Authenticate to Vault using Kubernetes service account.

                    Args:
                        role: Vault role for Kubernetes auth
                        jwt_path: Path to service account JWT token
                        """
                        if self._dev_mode:
# Mark authenticated; use env-only / in-memory secrets
                            self._authenticated = True
                            logger.warning(
                            "DEV mode: simulating Vault k8s auth; using environment/in-memory secrets."
                            )
                            return
                            try:
                                with open(jwt_path) as f:
                                    jwt = f.read().strip()
                                    if self.client is None:
                                        self.client = hvac.Client(
    url=self.vault_addr, namespace=self.vault_namespace
    )
    self.client.auth.kubernetes.login(role=role, jwt=jwt)

    self._authenticated = True
    logger.info(f"Authenticated to Vault as role: {role}")
    except Exception as e:
        logger.error(f"Vault authentication failed: {e}")
        raise

    def authenticate_with_spiffe(self, spiffe_id: str, cert_path: str, key_path: str):
            """
            Authenticate to Vault using SPIFFE identity (TLS cert auth).

            Args:
                spiffe_id: SPIFFE ID for the service
                cert_path: Path to SPIFFE SVID certificate
                key_path: Path to SPIFFE SVID private key
                """
                if self._dev_mode:
                    self._authenticated = True
                    logger.warning(
                    "DEV mode: simulating Vault SPIFFE auth; using environment/in-memory secrets."
                    )
                    return
                    try:
                        self.client = hvac.Client(
                        url=self.vault_addr,
                        namespace=self.vault_namespace,
                        cert=(cert_path, key_path),
                        )

# TLS cert auth
                        self.client.auth.cert.login()

                        self._authenticated = True
                        logger.info(f"Authenticated to Vault with SPIFFE ID: {spiffe_id}")
                        except Exception as e:
                            logger.error(f"SPIFFE authentication failed: {e}")
                            raise

    def read_secret(self, path: str, mount_point: str = "secret") -> VaultSecret:
                                """
                                Read secret from Vault KV v2 engine.

                                Args:
                                    path: Secret path (e.g., "database/postgres")
                                    mount_point: KV mount point

                                    Returns:
                                        VaultSecret with data and metadata
                                        """
                                        if self._dev_mode:
# Try in-memory first
                                            if path in self._dev_store:
                                                data = self._dev_store[path]
                                                version = self._dev_versions.get(path, 1)
                                                return VaultSecret(
    data=data,
    version=version,
    created_time=datetime.now(UTC),
    )
# Fallback: derive env-based secret mapping
# Convert path like "database/postgres" -> prefix tokens
    tokens = [t for t in path.replace("/", "_").split("_") if t]
    prefix = "SOMA_AGENT_HUB_" + "_".join([t.upper() for t in tokens]) + "_"
    env_data: dict[str, Any] = {}
    for k, v in os.environ.items():
        if k.startswith(prefix):
    # key after prefix
    short_key = k[len(prefix) :].lower()
    env_data[short_key] = v
    if not env_data:
        logger.warning(
    f"DEV mode: no env secret values for path {path}; returning empty secret."
    )
    return VaultSecret(
    data=env_data,
    version=0,
    created_time=datetime.now(UTC),
    )
    if not self._authenticated:
        raise RuntimeError("Not authenticated to Vault")

        try:
            if self.client is None:
                self.client = hvac.Client(
    url=self.vault_addr, namespace=self.vault_namespace
    )
    response = self.client.secrets.kv.v2.read_secret_version(
    path=path, mount_point=mount_point
    )

    data = response["data"]["data"]
    metadata = response["data"]["metadata"]

    return VaultSecret(
    data=data,
    version=metadata["version"],
    created_time=datetime.fromisoformat(
    metadata["created_time"].replace("Z", "+00:00")
    ),
    )
    except Exception as e:
        logger.error(f"Failed to read secret {path}: {e}")
        raise

    def write_secret(
    self, path: str, data: dict[str, Any], mount_point: str = "secret"
    ) -> int:
        """
        Write secret to Vault KV v2 engine.

        Args:
            path: Secret path
            data: Secret data
            mount_point: KV mount point

            Returns:
                Version number of created secret
                """
                if self._dev_mode:
                    current_version = self._dev_versions.get(path, 0) + 1
                    self._dev_versions[path] = current_version
                    self._dev_store[path] = data
                    logger.info(
                    f"DEV mode: stored in-memory secret {path} version {current_version}"
                    )
                    return current_version
                    if not self._authenticated:
                        raise RuntimeError("Not authenticated to Vault")

                        try:
                            if self.client is None:
                                self.client = hvac.Client(
                                url=self.vault_addr, namespace=self.vault_namespace
                                )
                                response = self.client.secrets.kv.v2.create_or_update_secret(
                                path=path, secret=data, mount_point=mount_point
                                )

                                version = response["data"]["version"]
                                logger.info(f"Wrote secret {path} version {version}")
                                return version
                                except Exception as e:
    logger.error(f"Failed to write secret {path}: {e}")
    raise

    def delete_secret(self, path: str, mount_point: str = "secret") -> None:
        """
        Delete secret from Vault (soft delete - can be undeleted).

        Args:
            path: Secret path
            mount_point: KV mount point
            """
            if self._dev_mode:
                removed = self._dev_store.pop(path, None)
                self._dev_versions.pop(path, None)
                logger.info(
                f"DEV mode: deleted in-memory secret {path} (present={removed is not None})"
                )
                return
                if not self._authenticated:
                    raise RuntimeError("Not authenticated to Vault")

                    try:
                        if self.client is None:
                            self.client = hvac.Client(
                            url=self.vault_addr, namespace=self.vault_namespace
                            )
                            self.client.secrets.kv.v2.delete_latest_version_of_secret(
                            path=path, mount_point=mount_point
                            )
                            logger.info(f"Deleted secret {path}")
                            except Exception as e:
    logger.error(f"Failed to delete secret {path}: {e}")
    raise

    def get_database_credentials(
    self, db_role: str, mount_point: str = "database"
    ) -> VaultSecret:
        """
        Get dynamic database credentials from Vault.

        Args:
            db_role: Database role name
            mount_point: Database engine mount point

            Returns:
                VaultSecret with username, password, and lease info
                """
                if self._dev_mode:
                    username = resolve_env("DB_USERNAME", "devuser") or "devuser"
                    password = resolve_env("DB_PASSWORD", "devpass") or "devpass"
                    return VaultSecret(
                    data={"username": username, "password": password},
                    version=1,
                    created_time=datetime.now(UTC),
                    lease_duration=0,
                    lease_id=None,
                    )
                    if not self._authenticated:
                        raise RuntimeError("Not authenticated to Vault")

                        try:
                            if self.client is None:
                                self.client = hvac.Client(
                                url=self.vault_addr, namespace=self.vault_namespace
                                )
                                response = self.client.secrets.database.generate_credentials(
                                name=db_role, mount_point=mount_point
                                )

                                return VaultSecret(
                                data={
                                "username": response["data"]["username"],
                                "password": response["data"]["password"],
                                },
                                version=1,
                                created_time=datetime.now(UTC),
                                lease_duration=response["lease_duration"],
                                lease_id=response["lease_id"],
                                )
                                except Exception as e:
    logger.error(f"Failed to generate DB credentials for {db_role}: {e}")
    raise

    def renew_lease(self, lease_id: str, increment: int = 3600) -> int:
        """
        Renew a secret lease.

        Args:
    lease_id: Lease ID to renew
    increment: Lease extension in seconds

    Returns:
        New lease duration
        """
        if self._dev_mode:
            logger.info("DEV mode: lease renew noop.")
            return increment
            if not self._authenticated:
                raise RuntimeError("Not authenticated to Vault")

                try:
                    response = self.client.sys.renew_lease(
                    lease_id=lease_id, increment=increment
                    )
                    logger.info(f"Renewed lease {lease_id}")
                    return response["lease_duration"]
                    except Exception as e:
                        logger.error(f"Failed to renew lease {lease_id}: {e}")
                        raise

    def revoke_lease(self, lease_id: str) -> None:
                                        """
                                        Revoke a secret lease immediately.

                                        Args:
                                            lease_id: Lease ID to revoke
                                            """
                                            if self._dev_mode:
                                                logger.info("DEV mode: lease revoke noop.")
                                                return
                                                if not self._authenticated:
                                                    raise RuntimeError("Not authenticated to Vault")

                                                    try:
                                                        self.client.sys.revoke_lease(lease_id=lease_id)
                                                        logger.info(f"Revoked lease {lease_id}")
                                                        except Exception as e:
                                                            logger.error(f"Failed to revoke lease {lease_id}: {e}")
                                                            raise


# Global Vault client instance
                                                            _vault_client: VaultClient | None = None


    def get_vault_client() -> VaultClient:
        """Get or create global Vault client."""
        global _vault_client
        if _vault_client is None:
    _vault_client = VaultClient()
    return _vault_client


    def init_vault(role: str, auth_method: str = "kubernetes") -> VaultClient:
                                                                        """
                                                                        Initialize Vault client with authentication.

                                                                        Args:
                                                                            role: Vault role for authentication
                                                                            auth_method: Authentication method ("kubernetes" or "spiffe")

                                                                            Returns:
                                                                                Authenticated VaultClient
                                                                                """
                                                                                client = get_vault_client()

# DEV mode: perform simulated auth without network calls
                                                                                if (resolve_env("DEPLOYMENT_MODE", "DEV") or "DEV").upper() == "DEV":
                                                                                    if auth_method == "kubernetes":
                                                                                        client.authenticate_with_k8s(role)
                                                                                        elif auth_method == "spiffe":
                                                                                            client.authenticate_with_spiffe(
                                                                                            "spiffe://dev/local", "dev-cert", "dev-key"
                                                                                            )  # placeholders
                                                                                            else:
                                                                                                raise ValueError(f"Unknown auth method: {auth_method}")
                                                                                                logger.warning("DEV mode: Vault auth simulated; using env/in-memory secrets.")
                                                                                                return client

                                                                                                if auth_method == "kubernetes":
                                                                                                    client.authenticate_with_k8s(role)
                                                                                                    elif auth_method == "spiffe":
                                                                                                        from .spiffe_auth import get_authenticator

                                                                                                        auth = get_authenticator()
                                                                                                        identity = auth.identity
                                                                                                        if not identity:
                                                                                                            raise RuntimeError("SPIFFE identity not initialized")
                                                                                                            client.authenticate_with_spiffe(
                                                                                                            identity.spiffe_id, identity.cert_path, identity.key_path
                                                                                                            )
                                                                                                            else:
                                                                                                                raise ValueError(f"Unknown auth method: {auth_method}")

                                                                                                                return client
