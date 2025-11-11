"""
Session Management Pattern
Centralized JWT-based session handling
"""

import jwt
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from functools import lru_cache

from ..secrets.vault_manager import get_vault_manager

logger = logging.getLogger(__name__)


@dataclass
class SessionData:
    """Session data structure"""
    user_id: str
    tenant_id: str
    permissions: List[str]
    session_id: str
    created_at: datetime
    expires_at: datetime
    metadata: Dict[str, Any] = None


class SessionManager:
    """Centralized session management with JWT tokens"""
    
    def __init__(self):
        self.vault_manager = get_vault_manager()
        self._secret_key = None
        self.algorithm = "HS256"
        self.default_expiry_hours = 24
    
    @property
    def secret_key(self) -> str:
        """Get JWT secret key from Vault"""
        if self._secret_key is None:
            self._secret_key = self.vault_manager.get_secret("jwt", "secret")
            if not self._secret_key or self._secret_key == "your-secret-key":
                # Generate new key if not set
                self._secret_key = secrets.token_urlsafe(64)
                logger.warning("Generated new JWT secret key - not persisted to Vault")
        return self._secret_key
    
    def create_session(
        self, 
        user_id: str, 
        tenant_id: str, 
        permissions: List[str] = None,
        expiry_hours: int = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Create new JWT session token"""
        
        permissions = permissions or []
        expiry_hours = expiry_hours or self.default_expiry_hours
        metadata = metadata or {}
        
        # Generate unique session ID
        session_id = secrets.token_urlsafe(32)
        
        # Calculate expiry
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=expiry_hours)
        
        # Create payload
        payload = {
            "session_id": session_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "permissions": permissions,
            "metadata": metadata,
            "created_at": now.isoformat(),
            "exp": expires_at,
            "iat": now,
            "version": "1.0"
        }
        
        # Create JWT token
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        logger.info(f"Created session {session_id} for user {user_id} in tenant {tenant_id}")
        return token
    
    def validate_session(self, token: str) -> SessionData:
        """Validate and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Convert datetime strings back to datetime objects
            created_at = datetime.fromisoformat(payload["created_at"])
            expires_at = datetime.fromisoformat(payload["exp"].isoformat())
            
            return SessionData(
                user_id=payload["user_id"],
                tenant_id=payload["tenant_id"],
                permissions=payload["permissions"],
                session_id=payload["session_id"],
                created_at=created_at,
                expires_at=expires_at,
                metadata=payload.get("metadata", {})
            )
            
        except jwt.ExpiredSignatureError:
            raise ValueError("Session has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid session token: {e}")
    
    def refresh_session(self, token: str, extend_hours: int = 24) -> str:
        """Refresh existing session with new expiry"""
        try:
            # Validate current session
            session_data = self.validate_session(token)
            
            # Create new session with same data but extended expiry
            return self.create_session(
                user_id=session_data.user_id,
                tenant_id=session_data.tenant_id,
                permissions=session_data.permissions,
                expiry_hours=extend_hours,
                metadata=session_data.metadata
            )
            
        except ValueError as e:
            logger.error(f"Failed to refresh session: {e}")
            raise
    
    def revoke_session(self, session_id: str) -> bool:
        """Revoke session (add to blacklist)"""
        # In a distributed system, this would add to Redis or database
        logger.info(f"Revoked session {session_id}")
        return True
    
    def has_permission(self, token: str, permission: str) -> bool:
        """Check if session has specific permission"""
        try:
            session_data = self.validate_session(token)
            return permission in session_data.permissions
        except ValueError:
            return False
    
    def has_any_permission(self, token: str, permissions: List[str]) -> bool:
        """Check if session has any of the specified permissions"""
        try:
            session_data = self.validate_session(token)
            return any(p in session_data.permissions for p in permissions)
        except ValueError:
            return False
    
    def generate_temporary_token(
        self, 
        user_id: str, 
        tenant_id: str, 
        expiry_minutes: int = 30
    ) -> str:
        """Generate short-lived temporary token"""
        return self.create_session(
            user_id=user_id,
            tenant_id=tenant_id,
            permissions=["temporary"],
            expiry_hours=expiry_minutes / 60
        )
    
    def get_session_info(self, token: str) -> Dict[str, Any]:
        """Get session information without full validation"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": False})
            return {
                "session_id": payload.get("session_id"),
                "user_id": payload.get("user_id"),
                "tenant_id": payload.get("tenant_id"),
                "permissions": payload.get("permissions", []),
                "expiry": payload.get("exp"),
                "is_expired": datetime.utcnow() > datetime.fromtimestamp(payload.get("exp", 0))
            }
        except jwt.InvalidTokenError:
            return {}


class SessionBlacklist:
    """Simple in-memory session blacklist (use Redis in production)"""
    
    def __init__(self):
        self.blacklisted = set()
    
    def add(self, session_id: str) -> None:
        """Add session to blacklist"""
        self.blacklisted.add(session_id)
    
    def remove(self, session_id: str) -> None:
        """Remove session from blacklist"""
        self.blacklisted.discard(session_id)
    
    def is_blacklisted(self, session_id: str) -> bool:
        """Check if session is blacklisted"""
        return session_id in self.blacklisted


# Global instances
_session_manager = None
_blacklist = SessionBlacklist()

@lru_cache()
def get_session_manager() -> SessionManager:
    """Get global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def get_blacklist() -> SessionBlacklist:
    """Get global blacklist instance"""
    return _blacklist


# Convenience functions
def create_user_session(user_id: str, tenant_id: str, permissions: List[str] = None) -> str:
    """Quick function to create user session"""
    return get_session_manager().create_session(user_id, tenant_id, permissions)


def validate_user_session(token: str) -> SessionData:
    """Quick function to validate user session"""
    return get_session_manager().validate_session(token)


def refresh_user_session(token: str) -> str:
    """Quick function to refresh user session"""
    return get_session_manager().refresh_session(token)