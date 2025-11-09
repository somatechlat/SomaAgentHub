"""
Production security hardening with input validation, security headers, and vulnerability protection.

This module provides:
- Input validation and sanitization
- Security headers (CSP, HSTS, etc.)
- CORS policy configuration
- SQL injection prevention
- XSS protection
- Request size limits
- Security scanning
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from fastapi import HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, validator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Security configuration
SECURITY_CONFIG = {
    "max_request_size_mb": 10,
    "max_body_size_mb": 5,
    "allowed_domains": [
        "soma-agent-hub.com",
        "api.soma-agent-hub.com",
        "localhost",
    ],
    "allowed_origins": [
        "https://soma-agent-hub.com",
        "https://app.soma-agent-hub.com",
        "https://admin.soma-agent-hub.com",
    ],
    "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allowed_headers": [
        "Content-Type",
        "Authorization",
        "X-API-Key",
        "X-Correlation-ID",
        "X-User-ID",
        "X-Session-ID",
    ],
    "exposed_headers": [
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "X-Correlation-ID",
    ],
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers."""

    async def dispatch(self, request: Request, call_next):
        """Add security headers to all responses."""
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "connect-src 'self' https://soma-agent-hub.com",
            "font-src 'self'",
            "object-src 'none'",
            "media-src 'self'",
            "frame-src 'none'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        return response


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce request size limits."""

    def __init__(self, app, max_size_mb: int = 5):
        super().__init__(app)
        self.max_size_bytes = max_size_mb * 1024 * 1024

    async def dispatch(self, request: Request, call_next):
        """Check request size."""
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_size_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Request too large. Maximum size is {self.max_size_bytes // (1024*1024)}MB",
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Content-Length header",
                )

        return await call_next(request)


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for input validation and sanitization."""

    async def dispatch(self, request: Request, call_next):
        """Validate and sanitize inputs."""
        # Validate query parameters
        if request.query_params:
            for key, value in request.query_params.items():
                if not self._is_safe_input(key) or not self._is_safe_input(str(value)):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid query parameter: {key}",
                    )

        # Validate path parameters
        for key, value in request.path_params.items():
            if not self._is_safe_path_param(str(value)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid path parameter: {key}",
                )

        return await call_next(request)

    def _is_safe_input(self, value: str) -> bool:
        """Check if input is safe (no SQL injection patterns)."""
        # Basic SQL injection prevention
        dangerous_patterns = [
            r"(\bunion\b|\bselect\b|\binsert\b|\bupdate\b|\bdelete\b|\bdrop\b|\bcreate\b|\\x00)",
            r"(\bOR\b|\bAND\b)\s+\d+\s*=\s*\d+",
            r"(\bOR\b|\bAND\b)\s*['\"]?\w*['\"]?\s*=\s*['\"]?\w*['\"]?",
            r"(\bOR\b|\bAND\b)\s*['\"]?.*['\"]?\s*LIKE\s*['\"]?.*['\"]?",
            r"(\bOR\b|\bAND\b)\s*['\"]?.*['\"]?\s*IN\s*\([\"]?.*[\"]?\)",
            r"(\bOR\b|\bAND\b)\s*['\"]?.*['\"]?\s*BETWEEN\s*['\"]?.*['\"]?\s*AND\s*['\"]?.*['\"]?",
            r"(\bOR\b|\bAND\b)\s*['\"]?.*['\"]?\s*IS\s*NULL",
            r"(\bOR\b|\bAND\b)\s*['\"]?.*['\"]?\s*IS\s*NOT\s*NULL",
            r"(\bOR\b|\bAND\b)\s*['\"]?.*['\"]?\s*EXISTS\s*\([\"]?.*[\"]?\)",
            r"(\bOR\b|\bAND\b)\s*['\"]?.*['\"]?\s*NOT\s*EXISTS\s*\([\"]?.*[\"]?\)",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return False

        return True

    def _is_safe_path_param(self, value: str) -> bool:
        """Check if path parameter is safe."""
        # Allow alphanumeric, hyphens, underscores, and periods
        safe_pattern = r"^[a-zA-Z0-9._-]+$"
        return bool(re.match(safe_pattern, value))


class SecurityConfig:
    """Security configuration model."""

    def __init__(self):
        self.max_request_size = SECURITY_CONFIG["max_request_size_mb"]
        self.allowed_domains = SECURITY_CONFIG["allowed_domains"]
        self.allowed_origins = SECURITY_CONFIG["allowed_origins"]
        self.allowed_methods = SECURITY_CONFIG["allowed_methods"]
        self.allowed_headers = SECURITY_CONFIG["allowed_headers"]
        self.exposed_headers = SECURITY_CONFIG["exposed_headers"]


class SecurityValidationModels:
    """Pydantic models for security validation."""

    class APIKeyRequest(BaseModel):
        api_key: str = Field(..., min_length=32, max_length=64)

        @validator("api_key")
        def validate_api_key(cls, v):
            if not re.match(r"^[a-zA-Z0-9_-]+$", v):
                raise ValueError("API key contains invalid characters")
            return v

    class UserId(BaseModel):
        user_id: str = Field(
            ..., min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$"
        )

    class SessionId(BaseModel):
        session_id: str = Field(
            ..., min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$"
        )

    class SafeString(BaseModel):
        value: str = Field(..., max_length=1000)

        @validator("value")
        def sanitize_string(cls, v):
            # Remove null bytes and control characters
            v = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", v)
            # Remove potential XSS vectors
            v = re.sub(r"<script[^>]*>.*?</script>", "", v, flags=re.IGNORECASE)
            v = re.sub(r"javascript:", "", v, flags=re.IGNORECASE)
            v = re.sub(r"on\w+=", "", v, flags=re.IGNORECASE)
            return v.strip()


class SecurityManager:
    """Security manager for comprehensive protection."""

    def __init__(self):
        self.config = SecurityConfig()

    def setup_cors_middleware(self, app):
        """Setup CORS middleware with security policies."""
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.allowed_origins,
            allow_credentials=True,
            allow_methods=self.config.allowed_methods,
            allow_headers=self.config.allowed_headers,
            expose_headers=self.config.exposed_headers,
            max_age=3600,
        )

    def setup_trusted_hosts(self, app):
        """Setup trusted hosts middleware."""
        app.add_middleware(
            TrustedHostMiddleware, allowed_hosts=self.config.allowed_domains
        )

    def setup_security_middleware(self, app):
        """Setup all security middleware."""
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(
            RequestSizeMiddleware, max_size_mb=self.config.max_request_size
        )
        app.add_middleware(InputValidationMiddleware)

    def validate_url(self, url: str) -> bool:
        """Validate URL against security policies."""
        try:
            parsed = urlparse(url)

            # Check scheme
            if parsed.scheme not in ["http", "https"]:
                return False

            # Check for localhost or private IPs
            hostname = parsed.hostname
            if hostname in ["localhost", "127.0.0.1", "0.0.0.0"]:
                return False

            # Check for dangerous ports
            if parsed.port and parsed.port not in [80, 443, 8080, 8443]:
                return False

            # Check for dangerous patterns
            dangerous_patterns = [
                r"file://",
                r"ftp://",
                r"ldap://",
                r"gopher://",
                r"\\x00",
                r"admin",
                r"root",
                r"config",
                r"password",
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return False

            return True

        except Exception:
            return False

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent directory traversal."""
        # Remove path separators and dangerous characters
        safe_filename = re.sub(r'[\/:*?"<>|]', "_", filename)
        safe_filename = re.sub(r"\.+", ".", safe_filename)
        safe_filename = safe_filename.strip(".")

        # Ensure filename is not empty and not too long
        if not safe_filename or len(safe_filename) > 255:
            safe_filename = "safe_filename" + str(hash(filename))[:8]

        return safe_filename

    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key format."""
        return bool(re.match(r"^[a-zA-Z0-9_-]{32,64}$", api_key))

    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(email_pattern, email))

    def validate_phone(self, phone: str) -> bool:
        """Validate phone number format."""
        phone_pattern = r"^\+?[\d\s\-\(\)]+$"
        return (
            bool(re.match(phone_pattern, phone)) and len(re.sub(r"\D", "", phone)) >= 10
        )


# Global security manager
security_manager = SecurityManager()


# Security decorators
def secure_endpoint(max_length: int = 1000):
    """Decorator for secure endpoint validation."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Validate all string inputs
            for key, value in kwargs.items():
                if isinstance(value, str):
                    if len(value) > max_length:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Parameter {key} exceeds maximum length of {max_length}",
                        )

                    # Additional security validation
                    if not security_manager._is_safe_input(value):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Parameter {key} contains invalid characters",
                        )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
