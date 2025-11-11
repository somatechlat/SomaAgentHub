"""
Vault Manager Pattern
Centralized secrets management with rotation support
"""

import hvac
import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from functools import lru_cache

logger = logging.getLogger(__name__)


class VaultManager:
    """Centralized secrets management with Vault integration"""
    
    def __init__(self, vault_addr: str = None, vault_token: str = None):
        self.vault_addr = vault_addr or os.getenv("SOMASTACK_VAULT_ADDRESS", "http://vault:8200")
        self.vault_token = vault_token or os.getenv("SOMASTACK_VAULT_TOKEN", "")
        
        if not self.vault_token:
            # Development fallback
            self.vault_token = "dev-token"
            logger.warning("Using development Vault token")
        
        self.client = hvac.Client(
            url=self.vault_addr,
            token=self.vault_token
        )
        
        # Verify connection
        if not self.client.is_authenticated():
            logger.error("Failed to authenticate with Vault")
            # In development, continue with mock secrets
            if not self._is_development():
                raise ConnectionError("Cannot connect to Vault")
    
    def _is_development(self) -> bool:
        """Check if running in development mode"""
        env = os.getenv("SOMASTACK_ENVIRONMENT", "development")
        # Also check if Vault is actually accessible
        try:
            if env != "development":
                return False
            # Try to connect to Vault
            import socket
            vault_host = self.vault_addr.replace("http://", "").replace("https://", "").split(":")[0]
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((vault_host, 8200))
            sock.close()
            return result != 0  # Return True if Vault is NOT accessible
        except:
            return True
    
    def get_secret(self, path: str, key: str = None) -> Any:
        """Get secret from Vault with development fallback"""
        try:
            if self._is_development():
                return self._get_development_secret(path, key)
            
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point="secret"
            )
            
            data = response['data']['data']
            if key:
                return data.get(key)
            return data
            
        except Exception as e:
            logger.error(f"Failed to get secret {path}/{key}: {e}")
            if self._is_development():
                return self._get_development_secret(path, key)
            raise
    
    def _get_development_secret(self, path: str, key: str = None) -> Any:
        """Development secrets fallback"""
        dev_secrets = {
            "database": {
                "postgres_url": "postgresql://postgres:postgres@localhost:5432/soma",
                "redis_url": "redis://localhost:6379",
                "clickhouse_url": "http://localhost:8123"
            },
            "jwt": {
                "secret": "dev-jwt-secret-key-change-in-production",
                "algorithm": "HS256",
                "expires_in": 86400
            },
            "stripe": {
                "secret_key": "sk_test_dev_stripe_key",
                "webhook_secret": "whsec_dev_webhook_secret",
                "publishable_key": "pk_test_dev_publishable_key"
            },
            "services": {
                "llm_hub_api_key": "dev-llm-hub-key",
                "gpubroker_api_key": "dev-gpubroker-key"
            }
        }
        
        # Normalize path
        normalized_path = path.strip("/")
        parts = normalized_path.split("/")
        
        # Navigate to the secret
        current = dev_secrets
        for part in parts:
            if part in current:
                current = current[part]
            else:
                current = {}
                break
        
        if key and isinstance(current, dict):
            return current.get(key)
        return current
    
    def set_secret(self, path: str, data: Dict[str, Any]) -> bool:
        """Set secret in Vault"""
        try:
            response = self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=data,
                mount_point="secret"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to set secret {path}: {e}")
            return False
    
    def delete_secret(self, path: str) -> bool:
        """Delete secret from Vault"""
        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=path,
                mount_point="secret"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret {path}: {e}")
            return False
    
    def list_secrets(self, path: str) -> List[str]:
        """List secrets in a path"""
        try:
            response = self.client.secrets.kv.v2.list_secrets(
                path=path,
                mount_point="secret"
            )
            return response['data']['keys']
        except Exception as e:
            logger.error(f"Failed to list secrets {path}: {e}")
            return []
    
    def get_database_credentials(self, service: str) -> Dict[str, str]:
        """Get dynamic database credentials"""
        try:
            response = self.client.secrets.database.generate_credentials(
                name=f"{service}-role",
                mount_point="database"
            )
            return response['data']
        except Exception as e:
            logger.error(f"Failed to get DB credentials for {service}: {e}")
            if self._is_development():
                return {
                    "username": f"{service}_user",
                    "password": "dev_password"
                }
            raise
    
    def create_database_role(self, service: str, database: str = "soma") -> bool:
        """Create database role for a service"""
        try:
            role_config = {
                "db_name": database,
                "creation_statements": [
                    f"CREATE USER \"{service}_user\" WITH PASSWORD '{{password}}' VALID UNTIL '{{expiration}}';",
                    f"GRANT ALL PRIVILEGES ON DATABASE {database} TO \"{service}_user\";"
                ],
                "default_ttl": "1h",
                "max_ttl": "24h"
            }
            
            self.client.secrets.database.create_role(
                name=f"{service}-role",
                mount_point="database",
                **role_config
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create DB role for {service}: {e}")
            return False
    
    def rotate_secret(self, path: str) -> bool:
        """Rotate a secret (generate new value)"""
        try:
            old_data = self.get_secret(path)
            if isinstance(old_data, dict):
                # Generate new values for sensitive keys
                import secrets
                new_data = old_data.copy()
                
                for key, value in new_data.items():
                    if any(sensitive in key.lower() for sensitive in ['key', 'secret', 'password', 'token']):
                        new_data[key] = secrets.token_urlsafe(32)
                
                return self.set_secret(path, new_data)
            return False
        except Exception as e:
            logger.error(f"Failed to rotate secret {path}: {e}")
            return False
    
    def get_service_secrets(self, service_name: str) -> Dict[str, Any]:
        """Get all secrets for a specific service"""
        service_secrets = {}
        
        # Database secrets
        try:
            service_secrets.update(self.get_secret(f"database/{service_name}"))
        except:
            pass
        
        # API keys
        try:
            service_secrets.update(self.get_secret(f"services/{service_name}"))
        except:
            pass
        
        # JWT secrets
        try:
            service_secrets.update(self.get_secret("jwt"))
        except:
            pass
        
        return service_secrets


# Global vault manager instance
_vault_manager = None

@lru_cache()
def get_vault_manager() -> VaultManager:
    """Get global vault manager instance"""
    global _vault_manager
    if _vault_manager is None:
        _vault_manager = VaultManager()
    return _vault_manager


class SecretsCache:
    """Simple in-memory cache for secrets with TTL"""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached secret"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.utcnow() - timestamp < timedelta(seconds=self.ttl):
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Cache secret with TTL"""
        self.cache[key] = (value, datetime.utcnow())
    
    def clear(self) -> None:
        """Clear all cached secrets"""
        self.cache.clear()


# Global secrets cache
secrets_cache = SecretsCache()