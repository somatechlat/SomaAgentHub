"""Identity service client for SomaGent platform.

Provides user authentication, capability checks, and role management.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

import httpx


class IdentityClient:
    """Client for identity service API."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
        api_key: Optional[str] = None,
    ):
        """Initialize identity client.
        
        Args:
            base_url: Identity service base URL
            timeout: Request timeout in seconds
            api_key: API key for service-to-service auth (optional)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.api_key = api_key

    async def check_user_capability(
        self,
        user_id: str,
        capability: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """Check if user has a specific capability.
        
        Args:
            user_id: User identifier (email or UUID)
            capability: Capability to check (e.g., "training.admin", "agent.create")
            tenant_id: Tenant context (optional)
            
        Returns:
            True if user has the capability, False otherwise
        """
        url = f"{self.base_url}/v1/users/{user_id}/capabilities/{capability}"
        
        params = {}
        if tenant_id:
            params["tenant_id"] = tenant_id
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=headers,
                )
                
                # 200 = has capability, 404 = does not have capability
                if response.status_code == 200:
                    return True
                elif response.status_code == 404:
                    return False
                else:
                    response.raise_for_status()
                    return False
                    
        except httpx.TimeoutException as exc:
            raise RuntimeError(
                f"Identity service timeout checking capability: {capability}"
            ) from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return False
            raise RuntimeError(
                f"Identity service error: {exc.response.status_code}"
            ) from exc

    async def get_user_capabilities(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
    ) -> List[str]:
        """Get all capabilities for a user.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant context (optional)
            
        Returns:
            List of capability strings
        """
        url = f"{self.base_url}/v1/users/{user_id}/capabilities"
        
        params = {}
        if tenant_id:
            params["tenant_id"] = tenant_id
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                return data.get("capabilities", [])
                
        except httpx.TimeoutException as exc:
            raise RuntimeError("Identity service timeout fetching capabilities") from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Identity service error: {exc.response.status_code}"
            ) from exc

    async def get_user_roles(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
    ) -> List[str]:
        """Get all roles for a user.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant context (optional)
            
        Returns:
            List of role names
        """
        url = f"{self.base_url}/v1/users/{user_id}/roles"
        
        params = {}
        if tenant_id:
            params["tenant_id"] = tenant_id
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                return data.get("roles", [])
                
        except httpx.TimeoutException as exc:
            raise RuntimeError("Identity service timeout fetching roles") from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Identity service error: {exc.response.status_code}"
            ) from exc

    async def verify_user(
        self,
        user_id: str,
    ) -> Dict[str, any]:
        """Verify user exists and get basic profile.
        
        Args:
            user_id: User identifier
            
        Returns:
            User profile dictionary
        """
        url = f"{self.base_url}/v1/users/{user_id}"
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException as exc:
            raise RuntimeError("Identity service timeout verifying user") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise ValueError(f"User not found: {user_id}") from exc
            raise RuntimeError(
                f"Identity service error: {exc.response.status_code}"
            ) from exc

    async def health_check(self) -> bool:
        """Check if identity service is accessible."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False


def get_identity_client() -> IdentityClient:
    """Get identity client from environment variables.
    
    Required environment variables:
        IDENTITY_SERVICE_URL: Identity service base URL
        IDENTITY_API_KEY: API key (optional)
        IDENTITY_TIMEOUT: Request timeout in seconds (optional, default: 10.0)
    """
    url = os.getenv("IDENTITY_SERVICE_URL")
    if not url:
        raise RuntimeError("IDENTITY_SERVICE_URL environment variable not set")
    
    api_key = os.getenv("IDENTITY_API_KEY")
    timeout = float(os.getenv("IDENTITY_TIMEOUT", "10.0"))
    
    return IdentityClient(
        base_url=url,
        timeout=timeout,
        api_key=api_key,
    )
