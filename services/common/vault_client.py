"""
HashiCorp Vault client for secrets management.

Provides secure secret storage, dynamic credentials, and automatic rotation.
Integrates with SPIFFE for authentication.
"""

import os
import hvac
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VaultSecret:
    """Vault secret with metadata."""
    
    data: Dict[str, Any]
    version: int
    created_time: datetime
    lease_duration: int = 0
    lease_id: Optional[str] = None


class VaultClient:
    """Client for HashiCorp Vault operations."""
    
    def __init__(
        self,
        vault_addr: Optional[str] = None,
        vault_namespace: Optional[str] = None
    ):
        """
        Initialize Vault client.
        
        Args:
            vault_addr: Vault server address (default: env VAULT_ADDR)
            vault_namespace: Vault namespace (default: env VAULT_NAMESPACE)
        """
        self.vault_addr = vault_addr or os.getenv("VAULT_ADDR", "http://vault:8200")
        self.vault_namespace = vault_namespace or os.getenv("VAULT_NAMESPACE", "somaagent")
        
        self.client = hvac.Client(url=self.vault_addr, namespace=self.vault_namespace)
        self._authenticated = False
    
    def authenticate_with_k8s(self, role: str, jwt_path: str = "/var/run/secrets/kubernetes.io/serviceaccount/token"):
        """
        Authenticate to Vault using Kubernetes service account.
        
        Args:
            role: Vault role for Kubernetes auth
            jwt_path: Path to service account JWT token
        """
        try:
            with open(jwt_path, 'r') as f:
                jwt = f.read().strip()
            
            self.client.auth.kubernetes.login(
                role=role,
                jwt=jwt
            )
            
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
        try:
            self.client = hvac.Client(
                url=self.vault_addr,
                namespace=self.vault_namespace,
                cert=(cert_path, key_path)
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
        if not self._authenticated:
            raise RuntimeError("Not authenticated to Vault")
        
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=mount_point
            )
            
            data = response['data']['data']
            metadata = response['data']['metadata']
            
            return VaultSecret(
                data=data,
                version=metadata['version'],
                created_time=datetime.fromisoformat(metadata['created_time'].replace('Z', '+00:00'))
            )
        except Exception as e:
            logger.error(f"Failed to read secret {path}: {e}")
            raise
    
    def write_secret(self, path: str, data: Dict[str, Any], mount_point: str = "secret") -> int:
        """
        Write secret to Vault KV v2 engine.
        
        Args:
            path: Secret path
            data: Secret data
            mount_point: KV mount point
            
        Returns:
            Version number of created secret
        """
        if not self._authenticated:
            raise RuntimeError("Not authenticated to Vault")
        
        try:
            response = self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=data,
                mount_point=mount_point
            )
            
            version = response['data']['version']
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
        if not self._authenticated:
            raise RuntimeError("Not authenticated to Vault")
        
        try:
            self.client.secrets.kv.v2.delete_latest_version_of_secret(
                path=path,
                mount_point=mount_point
            )
            logger.info(f"Deleted secret {path}")
        except Exception as e:
            logger.error(f"Failed to delete secret {path}: {e}")
            raise
    
    def get_database_credentials(self, db_role: str, mount_point: str = "database") -> VaultSecret:
        """
        Get dynamic database credentials from Vault.
        
        Args:
            db_role: Database role name
            mount_point: Database engine mount point
            
        Returns:
            VaultSecret with username, password, and lease info
        """
        if not self._authenticated:
            raise RuntimeError("Not authenticated to Vault")
        
        try:
            response = self.client.secrets.database.generate_credentials(
                name=db_role,
                mount_point=mount_point
            )
            
            return VaultSecret(
                data={
                    'username': response['data']['username'],
                    'password': response['data']['password']
                },
                version=1,
                created_time=datetime.utcnow(),
                lease_duration=response['lease_duration'],
                lease_id=response['lease_id']
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
        if not self._authenticated:
            raise RuntimeError("Not authenticated to Vault")
        
        try:
            response = self.client.sys.renew_lease(
                lease_id=lease_id,
                increment=increment
            )
            logger.info(f"Renewed lease {lease_id}")
            return response['lease_duration']
        except Exception as e:
            logger.error(f"Failed to renew lease {lease_id}: {e}")
            raise
    
    def revoke_lease(self, lease_id: str) -> None:
        """
        Revoke a secret lease immediately.
        
        Args:
            lease_id: Lease ID to revoke
        """
        if not self._authenticated:
            raise RuntimeError("Not authenticated to Vault")
        
        try:
            self.client.sys.revoke_lease(lease_id=lease_id)
            logger.info(f"Revoked lease {lease_id}")
        except Exception as e:
            logger.error(f"Failed to revoke lease {lease_id}: {e}")
            raise


# Global Vault client instance
_vault_client: Optional[VaultClient] = None


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
    
    if auth_method == "kubernetes":
        client.authenticate_with_k8s(role)
    elif auth_method == "spiffe":
        from .spiffe_auth import get_authenticator
        auth = get_authenticator()
        identity = auth.identity
        if not identity:
            raise RuntimeError("SPIFFE identity not initialized")
        client.authenticate_with_spiffe(
            identity.spiffe_id,
            identity.cert_path,
            identity.key_path
        )
    else:
        raise ValueError(f"Unknown auth method: {auth_method}")
    
    return client
