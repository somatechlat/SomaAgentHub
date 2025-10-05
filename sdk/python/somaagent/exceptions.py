"""
Exceptions for SomaAgent SDK.
"""


class SomaAgentError(Exception):
    """Base exception for SomaAgent SDK."""
    pass


class APIError(SomaAgentError):
    """API request failed."""
    
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}


class AuthenticationError(SomaAgentError):
    """Authentication failed."""
    pass


class RateLimitError(APIError):
    """Rate limit exceeded."""
    pass


class ValidationError(SomaAgentError):
    """Input validation failed."""
    pass
