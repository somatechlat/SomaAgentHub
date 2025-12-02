from services.common.config.base_settings import resolve_env

"""
Exceptions for SomaAgent SDK.
"""


class SomaAgentError(Exception):
    """Base exception for SomaAgent SDK."""

    ...


class APIError(SomaAgentError):
    """API request failed."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}


class AuthenticationError(SomaAgentError):
    """Authentication failed."""

    ...


class RateLimitError(APIError):
    """Rate limit exceeded."""

    ...


class ValidationError(SomaAgentError):
    """Input validation failed."""

    ...
