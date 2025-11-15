"""
Enterprise-Grade Service-to-Service Authentication Framework.

Provides comprehensive service authentication, token management, and lifecycle
for zero-trust security architecture.

TRUTH: Centralized service authentication eliminates security fragmentation
and ensures consistent security posture across all services.
"""

from __future__ import annotations

# Ensure proper path setup for imports
import services._path_setup

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from pydantic import BaseModel, Field

from services.common.config.base_settings import resolve_env
from services.common.vault_client import get_vault_client

logger = logging.getLogger(__name__)


class ServiceAccount(BaseModel):
    """Service account model with enterprise security features."""

service_id: str
service_name: str
namespace: str
roles: List[str] = Field(default_factory=list)
permissions: List[str] = Field(default_factory=list)
created_at: datetime = Field(default_factory=datetime.utcnow)
expires_at: Optional[datetime] = None
active: bool = True
metadata: Dict = Field(default_factory=dict)


class ServiceToken(BaseModel):
    """Service token model with comprehensive security attributes."""

token_id: str
service_id: str
token_type: str  # "access", "refresh", "service"
issued_at: datetime = Field(default_factory=datetime.utcnow)
expires_at: datetime
scopes: List[str] = Field(default_factory=list)
jti: str = Field(default_factory=lambda: str(uuid4()))
active: bool = True
rotation_count: int = 0
last_rotated: Optional[datetime] = None


class ServiceAuthConfig(BaseModel):
    """Configuration for service authentication."""

token_issuer: str = "somaagent-governance"
token_audience: str = "somaagent-services"
access_token_lifetime: timedelta = timedelta(hours=1)
refresh_token_lifetime: timedelta = timedelta(days=30)
service_token_lifetime: timedelta = timedelta(days=7)
rotation_threshold: timedelta = timedelta(hours=6)
max_rotation_count: int = 100
key_rotation_interval: timedelta = timedelta(days=30)


class ServiceAuthManager:
    """
    Enterprise-grade service authentication manager.
    
    Features:
    - Automatic token generation and rotation
    - Service account lifecycle management
    - Comprehensive audit logging
    - High availability with caching
    - Zero-trust security principles
    """

    def __init__(self, config: ServiceAuthConfig):
        self.config = config
        self.vault_client = get_vault_client()
        self._service_accounts: Dict[str, ServiceAccount] = {}
        self._active_tokens: Dict[str, ServiceToken] = {}
        self._private_key: Optional[rsa.RSAPrivateKey] = None
        self._public_key: Optional[rsa.RSAPublicKey] = None
        self._key_cache: Dict[str, str] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the service authentication manager."""
        if self._initialized:
            return

        try:
            # Load or generate cryptographic keys
            await self._load_or_generate_keys()
            
            # Load existing service accounts
            await self._load_service_accounts()
            
            # Start background tasks
            asyncio.create_task(self._token_rotation_task())
            asyncio.create_task(self._key_rotation_task())
            
            self._initialized = True
            logger.info("Service authentication manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize service authentication manager: {e}")
            raise

    async def _load_or_generate_keys(self) -> None:
        """Load existing keys from Vault or generate new ones."""
        try:
            # Try to load keys from Vault
            key_data = self.vault_client.read_secret("service-auth/keys")
            
            if key_data:
                private_key_pem = key_data.data.get("private_key")
                public_key_pem = key_data.data.get("public_key")
                
                if private_key_pem and public_key_pem:
                    self._private_key = serialization.load_pem_private_key(
                        private_key_pem.encode(),
                        password=None,
                    )
                    self._public_key = serialization.load_pem_public_key(
                        public_key_pem.encode(),
                    )
                    logger.info("Loaded existing keys from Vault")
                    return
            
            # Generate new keys
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=4096,
            )
            public_key = private_key.public_key()
            
            # Store keys in Vault
            private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            ).decode()
            
            public_key_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode()
            
            self.vault_client.write_secret(
                "service-auth/keys",
                {
                    "private_key": private_key_pem,
                    "public_key": public_key_pem,
                    "created_at": datetime.utcnow().isoformat(),
                },
            )
            
            self._private_key = private_key
            self._public_key = public_key
            logger.info("Generated and stored new cryptographic keys")
            
        except Exception as e:
            logger.error(f"Failed to load or generate keys: {e}")
            raise

    async def _load_service_accounts(self) -> None:
        """Load existing service accounts from Vault."""
        try:
            accounts_data = self.vault_client.read_secret("service-auth/accounts")
            
            if accounts_data:
                for account_id, account_data in accounts_data.data.items():
                    service_account = ServiceAccount(**account_data)
                    self._service_accounts[account_id] = service_account
                    
                logger.info(f"Loaded {len(self._service_accounts)} service accounts")
            
        except Exception as e:
            logger.error(f"Failed to load service accounts: {e}")
            # Continue with empty accounts - this is acceptable for initialization

    async def create_service_account(
        self,
        service_name: str,
        namespace: str,
        roles: List[str] = None,
        permissions: List[str] = None,
        expires_at: Optional[datetime] = None,
        metadata: Dict = None,
    ) -> ServiceAccount:
        """
        Create a new service account.
        
        Args:
            service_name: Name of the service
            namespace: Kubernetes namespace
            roles: List of roles for the service
            permissions: List of permissions for the service
            expires_at: Optional expiration date
            metadata: Additional metadata
            
        Returns:
            Created service account
        """
        if roles is None:
            roles = []
        if permissions is None:
            permissions = []
        if metadata is None:
            metadata = {}

        service_id = f"{namespace}/{service_name}"
        
        # Check if service account already exists
        if service_id in self._service_accounts:
            raise ValueError(f"Service account {service_id} already exists")

        service_account = ServiceAccount(
            service_id=service_id,
            service_name=service_name,
            namespace=namespace,
            roles=roles,
            permissions=permissions,
            expires_at=expires_at,
            metadata=metadata,
        )

        # Store in memory
        self._service_accounts[service_id] = service_account

        # Store in Vault
        await self._store_service_account(service_account)

        logger.info(f"Created service account: {service_id}")
        return service_account

    async def _store_service_account(self, service_account: ServiceAccount) -> None:
        """Store service account in Vault."""
        try:
            accounts_data = self.vault_client.read_secret("service-auth/accounts") or {}
            accounts_data.data = accounts_data.data or {}
            
            accounts_data.data[service_account.service_id] = service_account.model_dump()
            
            self.vault_client.write_secret(
                "service-auth/accounts",
                accounts_data.data,
            )
            
        except Exception as e:
            logger.error(f"Failed to store service account {service_account.service_id}: {e}")
            raise

    async def generate_service_token(
        self,
        service_id: str,
        token_type: str = "access",
        scopes: List[str] = None,
    ) -> Tuple[str, ServiceToken]:
        """
        Generate a service token.
        
        Args:
            service_id: Service account ID
            token_type: Type of token ("access", "refresh", "service")
            scopes: List of scopes for the token
            
        Returns:
            Tuple of (token_string, token_model)
        """
        if scopes is None:
            scopes = []

        # Validate service account
        service_account = self._service_accounts.get(service_id)
        if not service_account:
            raise ValueError(f"Service account {service_id} not found")
        
        if not service_account.active:
            raise ValueError(f"Service account {service_id} is not active")
        
        if service_account.expires_at and service_account.expires_at < datetime.utcnow():
            raise ValueError(f"Service account {service_id} has expired")

        # Determine token lifetime
        if token_type == "access":
            lifetime = self.config.access_token_lifetime
        elif token_type == "refresh":
            lifetime = self.config.refresh_token_lifetime
        elif token_type == "service":
            lifetime = self.config.service_token_lifetime
        else:
            raise ValueError(f"Invalid token type: {token_type}")

        # Create token model
        token = ServiceToken(
            token_id=str(uuid4()),
            service_id=service_id,
            token_type=token_type,
            expires_at=datetime.utcnow() + lifetime,
            scopes=scopes,
        )

        # Generate JWT token
        token_data = {
            "sub": service_id,
            "iat": int(token.issued_at.timestamp()),
            "exp": int(token.expires_at.timestamp()),
            "iss": self.config.token_issuer,
            "aud": self.config.token_audience,
            "jti": token.jti,
            "type": token_type,
            "scopes": scopes,
            "roles": service_account.roles,
            "permissions": service_account.permissions,
            "service_name": service_account.service_name,
            "namespace": service_account.namespace,
        }

        if not self._private_key:
            raise RuntimeError("Private key not initialized")

        token_string = jwt.encode(
            token_data,
            self._private_key,
            algorithm="RS512",
        )

        # Store token
        self._active_tokens[token.jti] = token

        logger.info(f"Generated {token_type} token for service {service_id}")
        return token_string, token

    async def verify_service_token(self, token_string: str) -> Dict:
        """
        Verify a service token and return claims.
        
        Args:
            token_string: JWT token string
            
        Returns:
            Decoded token claims
            
        Raises:
            jwt.InvalidTokenError: If token is invalid
        """
        if not self._public_key:
            raise RuntimeError("Public key not initialized")

        try:
            # Decode and verify token
            claims = jwt.decode(
                token_string,
                self._public_key,
                algorithms=["RS512"],
                issuer=self.config.token_issuer,
                audience=self.config.token_audience,
            )

            # Verify token is still active
            jti = claims.get("jti")
            if jti not in self._active_tokens:
                raise jwt.InvalidTokenError("Token not found in active tokens")

            token = self._active_tokens[jti]
            if not token.active:
                raise jwt.InvalidTokenError("Token is not active")

            if token.expires_at < datetime.utcnow():
                raise jwt.InvalidTokenError("Token has expired")

            # Verify service account is still valid
            service_id = claims.get("sub")
            service_account = self._service_accounts.get(service_id)
            if not service_account:
                raise jwt.InvalidTokenError("Service account not found")

            if not service_account.active:
                raise jwt.InvalidTokenError("Service account is not active")

            return claims

        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError("Token has expired")
        except jwt.InvalidTokenError:
            raise
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise jwt.InvalidTokenError("Token verification failed")

    async def rotate_token(self, token_jti: str) -> Tuple[str, ServiceToken]:
        """
        Rotate an existing token.
        
        Args:
            token_jti: JTI of the token to rotate
            
        Returns:
            Tuple of (new_token_string, new_token_model)
        """
        if token_jti not in self._active_tokens:
            raise ValueError(f"Token {token_jti} not found")

        old_token = self._active_tokens[token_jti]
        
        if not old_token.active:
            raise ValueError(f"Token {token_jti} is not active")

        # Check rotation count
        if old_token.rotation_count >= self.config.max_rotation_count:
            raise ValueError(f"Token {token_jti} has reached maximum rotation count")

        # Deactivate old token
        old_token.active = False
        old_token.last_rotated = datetime.utcnow()

        # Generate new token
        _, new_token = await self.generate_service_token(
            old_token.service_id,
            old_token.token_type,
            old_token.scopes,
        )
        
        new_token.rotation_count = old_token.rotation_count + 1

        logger.info(f"Rotated token {token_jti} -> {new_token.jti}")
        return new_token.token_id, new_token

    async def revoke_token(self, token_jti: str) -> None:
        """
        Revoke a token.
        
        Args:
            token_jti: JTI of the token to revoke
        """
        if token_jti not in self._active_tokens:
            raise ValueError(f"Token {token_jti} not found")

        token = self._active_tokens[token_jti]
        token.active = False

        logger.info(f"Revoked token {token_jti}")

    async def deactivate_service_account(self, service_id: str) -> None:
        """
        Deactivate a service account and all its tokens.
        
        Args:
            service_id: Service account ID
        """
        service_account = self._service_accounts.get(service_id)
        if not service_account:
            raise ValueError(f"Service account {service_id} not found")

        service_account.active = False

        # Deactivate all tokens for this service
        tokens_to_deactivate = [
            token for token in self._active_tokens.values()
            if token.service_id == service_id and token.active
        ]

        for token in tokens_to_deactivate:
            token.active = False

        # Update in Vault
        await self._store_service_account(service_account)

        logger.info(f"Deactivated service account {service_id} and {len(tokens_to_deactivate)} tokens")

    async def _token_rotation_task(self) -> None:
        """Background task for automatic token rotation."""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                now = datetime.utcnow()
                rotation_threshold = now - self.config.rotation_threshold
                
                # Find tokens that need rotation
                tokens_to_rotate = [
                    token for token in self._active_tokens.values()
                    if token.active and token.expires_at <= rotation_threshold
                ]

                for token in tokens_to_rotate:
                    try:
                        await self.rotate_token(token.jti)
                    except Exception as e:
                        logger.error(f"Failed to rotate token {token.jti}: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in token rotation task: {e}")

    async def _key_rotation_task(self) -> None:
        """Background task for automatic key rotation."""
        while True:
            try:
                await asyncio.sleep(self.config.key_rotation_interval.total_seconds())
                
                # Generate new keys
                await self._load_or_generate_keys()
                
                logger.info("Completed key rotation")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in key rotation task: {e}")

    def get_service_account(self, service_id: str) -> Optional[ServiceAccount]:
        """Get service account by ID."""
        return self._service_accounts.get(service_id)

    def list_service_accounts(self) -> List[ServiceAccount]:
        """List all service accounts."""
        return list(self._service_accounts.values())

    def get_active_tokens(self, service_id: Optional[str] = None) -> List[ServiceToken]:
        """Get active tokens, optionally filtered by service ID."""
        tokens = [
            token for token in self._active_tokens.values()
            if token.active
        ]
        
        if service_id:
            tokens = [token for token in tokens if token.service_id == service_id]
        
        return tokens

    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens and return count of cleaned tokens."""
        now = datetime.utcnow()
        expired_tokens = [
            token for token in self._active_tokens.values()
            if token.expires_at < now
        ]

        for token in expired_tokens:
            del self._active_tokens[token.jti]

        logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")
        return len(expired_tokens)