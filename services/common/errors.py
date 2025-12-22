"""Standardized Error Handling Utilities for SomaAgentHub SaaS Platform.

Provides consistent error response format across all services per Requirements 9.2-9.5.

Error Response Schema:
- detail: Human-readable error message
- error_code: Machine-readable error code (optional)
- field_errors: Field-level validation errors (optional)

HTTP Status Code Mapping:
- 422: Validation errors (invalid input)
- 404: Resource not found
- 503: Service unavailable (missing config)
- 502: Upstream service failure
- 401: Authentication required
- 403: Authorization denied
- 500: Unexpected error (no details exposed)

Usage:
    from services.common.errors import (
        ServiceUnavailableError,
        UpstreamServiceError,
        raise_service_unavailable,
        raise_upstream_error,
        create_error_response,
    )

    # Raise 503 when service is disabled
    raise_service_unavailable("voice-interface", "OPENAI_API_KEY")

    # Raise 502 when upstream fails
    raise_upstream_error("pricing-service", "Connection refused")
"""

import logging
from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """Standard error response format.

    Per Requirement 9.4: All error responses SHALL follow consistent format.
    """

    detail: str = Field(..., description="Human-readable error message")
    error_code: str | None = Field(None, description="Machine-readable error code")
    field_errors: list[dict[str, Any]] | None = Field(None, description="Field-level validation errors")


class ServiceUnavailableError(HTTPException):
    """HTTP 503 Service Unavailable error.

    Per Requirement 9.3: Service unavailable SHALL return HTTP 503 with enablement instructions.
    """

    def __init__(self, service_name: str, env_var: str, additional_info: str | None = None):
        detail = f"Service '{service_name}' is disabled. Set {env_var} to enable."
        if additional_info:
            detail = f"{detail} {additional_info}"

        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )
        logger.warning(f"Service unavailable: {service_name} (missing {env_var})")


class UpstreamServiceError(HTTPException):
    """HTTP 502 Bad Gateway error for upstream service failures.

    Per Requirement 9.2: Upstream service failures SHALL return HTTP 502.
    """

    def __init__(self, service_name: str, error_message: str):
        # Sanitize error message to avoid leaking sensitive info
        safe_message = _sanitize_error_message(error_message)
        detail = f"Upstream service '{service_name}' unavailable: {safe_message}"

        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        )
        logger.error(f"Upstream service error: {service_name} - {error_message}")


class ResourceNotFoundError(HTTPException):
    """HTTP 404 Not Found error.

    Per Requirement 9.4: Resource not found SHALL return HTTP 404.
    """

    def __init__(self, resource_type: str, resource_id: str):
        detail = f"Resource '{resource_type}' not found: {resource_id}"

        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class InternalServerError(HTTPException):
    """HTTP 500 Internal Server Error.

    Per Requirement 9.5: Unexpected errors SHALL return HTTP 500 with generic message.
    No stack traces or sensitive information exposed.
    """

    def __init__(self, error: Exception | None = None):
        # Log the actual error for debugging, but don't expose it
        if error:
            logger.exception(f"Internal server error: {error}")

        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


def _sanitize_error_message(message: str) -> str:
    """Sanitize error message to avoid leaking sensitive information.

    Removes potential secrets, credentials, and stack traces.
    """
    # Truncate long messages
    if len(message) > 200:
        message = message[:200] + "..."

    # Remove potential secrets (basic patterns)
    import re

    # Remove anything that looks like a key/token
    message = re.sub(
        r"(key|token|secret|password|credential)[=:]\s*\S+", r"\1=[REDACTED]", message, flags=re.IGNORECASE
    )

    # Remove URLs with credentials
    message = re.sub(r"://[^@]+@", "://[REDACTED]@", message)

    return message


def raise_service_unavailable(service_name: str, env_var: str, additional_info: str | None = None) -> None:
    """Raise HTTP 503 Service Unavailable error.

    Args:
        service_name: Name of the disabled service
        env_var: Environment variable needed to enable the service
        additional_info: Optional additional context

    Raises:
        ServiceUnavailableError: Always raises this exception
    """
    raise ServiceUnavailableError(service_name, env_var, additional_info)


def raise_upstream_error(service_name: str, error_message: str) -> None:
    """Raise HTTP 502 Bad Gateway error for upstream failures.

    Args:
        service_name: Name of the failed upstream service
        error_message: Error message from the upstream service

    Raises:
        UpstreamServiceError: Always raises this exception
    """
    raise UpstreamServiceError(service_name, error_message)


def raise_not_found(resource_type: str, resource_id: str) -> None:
    """Raise HTTP 404 Not Found error.

    Args:
        resource_type: Type of resource (e.g., "memory", "capsule")
        resource_id: ID of the resource

    Raises:
        ResourceNotFoundError: Always raises this exception
    """
    raise ResourceNotFoundError(resource_type, resource_id)


def raise_internal_error(error: Exception | None = None) -> None:
    """Raise HTTP 500 Internal Server Error.

    Args:
        error: Optional exception to log (not exposed to client)

    Raises:
        InternalServerError: Always raises this exception
    """
    raise InternalServerError(error)


def create_error_response(
    status_code: int,
    detail: str,
    error_code: str | None = None,
    field_errors: list[dict[str, Any]] | None = None,
) -> ErrorResponse:
    """Create a standardized error response.

    Args:
        status_code: HTTP status code
        detail: Human-readable error message
        error_code: Optional machine-readable error code
        field_errors: Optional field-level validation errors

    Returns:
        ErrorResponse with consistent format
    """
    return ErrorResponse(
        detail=detail,
        error_code=error_code,
        field_errors=field_errors,
    )


def handle_exception(error: Exception, service_name: str) -> HTTPException:
    """Convert an exception to an appropriate HTTPException.

    Args:
        error: The exception to handle
        service_name: Name of the service for logging

    Returns:
        HTTPException with appropriate status code and message
    """
    # Already an HTTPException, return as-is
    if isinstance(error, HTTPException):
        return error

    # Connection errors -> 502
    if isinstance(error, ConnectionError | TimeoutError):
        return UpstreamServiceError(service_name, str(error))

    # Value/Type errors -> 422
    if isinstance(error, ValueError | TypeError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        )

    # Everything else -> 500
    return InternalServerError(error)
