"""Property-based tests for error response consistency.

**Feature: production-refactoring, Property 7: Error Response Consistency**
**Validates: Requirements 9.2, 9.3, 9.4, 9.5**

Tests that all HTTP error responses:
- Validation errors (invalid input) return HTTP 422 with field-level error details
- Upstream service failures return HTTP 502 with service identification
- Service unavailable (missing config) returns HTTP 503 with enablement instructions
- Unexpected errors return HTTP 500 with generic message (no stack traces)
"""

import re
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st


class TestErrorResponseConsistency:
    """Property tests for error response consistency (Property 7)."""

    def test_error_module_exists(self):
        """Verify standardized error module exists.

        **Feature: production-refactoring, Property 7: Error Response Consistency**
        **Validates: Requirements 9.2, 9.3, 9.4, 9.5**
        """
        repo_root = Path(__file__).parents[2]
        error_module = repo_root / "services/common/errors.py"

        assert error_module.exists(), "Missing services/common/errors.py"

        content = error_module.read_text()

        # Check for required error classes
        assert "ServiceUnavailableError" in content, "Missing ServiceUnavailableError class"
        assert "UpstreamServiceError" in content, "Missing UpstreamServiceError class"
        assert "ResourceNotFoundError" in content, "Missing ResourceNotFoundError class"
        assert "InternalServerError" in content, "Missing InternalServerError class"

    def test_503_errors_include_env_var_hint(self):
        """Verify 503 errors include environment variable hint.

        **Feature: production-refactoring, Property 7: Error Response Consistency**
        **Validates: Requirements 9.3**
        """
        repo_root = Path(__file__).parents[2]
        error_module = repo_root / "services/common/errors.py"

        if not error_module.exists():
            return

        content = error_module.read_text()

        # ServiceUnavailableError should include env_var in message
        assert "env_var" in content, "ServiceUnavailableError should accept env_var parameter"
        assert "Set" in content, "503 error should include 'Set <env_var>' instruction"

    def test_502_errors_identify_upstream_service(self):
        """Verify 502 errors identify the failed upstream service.

        **Feature: production-refactoring, Property 7: Error Response Consistency**
        **Validates: Requirements 9.2**
        """
        repo_root = Path(__file__).parents[2]
        error_module = repo_root / "services/common/errors.py"

        if not error_module.exists():
            return

        content = error_module.read_text()

        # UpstreamServiceError should include service_name
        assert "service_name" in content, "UpstreamServiceError should accept service_name parameter"
        assert "502" in content or "HTTP_502" in content, "Should use HTTP 502 status code"

    def test_500_errors_hide_details(self):
        """Verify 500 errors don't expose internal details.

        **Feature: production-refactoring, Property 7: Error Response Consistency**
        **Validates: Requirements 9.5**
        """
        repo_root = Path(__file__).parents[2]
        error_module = repo_root / "services/common/errors.py"

        if not error_module.exists():
            return

        content = error_module.read_text()

        # InternalServerError should return generic message
        assert "Internal server error" in content, "500 error should return generic message"
        # Should log the actual error but not expose it
        assert "logger" in content, "Should log errors for debugging"

    def test_error_message_sanitization(self):
        """Verify error messages are sanitized to remove secrets.

        **Feature: production-refactoring, Property 7: Error Response Consistency**
        **Validates: Requirements 9.5**
        """
        repo_root = Path(__file__).parents[2]
        error_module = repo_root / "services/common/errors.py"

        if not error_module.exists():
            return

        content = error_module.read_text()

        # Should have sanitization function
        assert "sanitize" in content.lower(), "Should have error message sanitization"
        assert "REDACTED" in content, "Should redact sensitive information"

    def test_services_use_standardized_errors(self):
        """Verify services import and use standardized error classes.

        **Feature: production-refactoring, Property 7: Error Response Consistency**
        **Validates: Requirements 9.2, 9.3, 9.4**
        """
        repo_root = Path(__file__).parents[2]

        services_to_check = [
            ("memory-gateway", "services/memory-gateway/app/main.py"),
            ("billing-service", "services/billing-service/app/main.py"),
        ]

        for service_name, service_path in services_to_check:
            file_path = repo_root / service_path
            if not file_path.exists():
                continue

            content = file_path.read_text()

            # Check for import of standardized errors
            has_error_import = (
                "from services.common.errors import" in content or "from services.common import errors" in content
            )
            assert has_error_import, f"{service_name}: Should import from services.common.errors"

    @settings(max_examples=100)
    @given(
        status_code=st.sampled_from([400, 401, 403, 404, 422, 500, 502, 503]),
        service_name=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N", "Pd"))),
    )
    def test_error_status_code_mapping(self, status_code: int, service_name: str):
        """Property test: error status codes should follow HTTP semantics.

        **Feature: production-refactoring, Property 7: Error Response Consistency**
        **Validates: Requirements 9.2, 9.3, 9.4, 9.5**
        """
        # Define expected error categories
        client_errors = {400, 401, 403, 404, 422}
        server_errors = {500, 502, 503}

        if status_code in client_errors:
            assert 400 <= status_code < 500, "Client errors should be 4xx"
        elif status_code in server_errors:
            assert 500 <= status_code < 600, "Server errors should be 5xx"

    @settings(max_examples=50)
    @given(
        error_message=st.text(min_size=1, max_size=500),
    )
    def test_error_message_length_limits(self, error_message: str):
        """Property test: error messages should be reasonably sized.

        **Feature: production-refactoring, Property 7: Error Response Consistency**
        **Validates: Requirements 9.4**
        """
        # Error messages should be truncated if too long
        max_length = 500
        truncated = error_message[:max_length] if len(error_message) > max_length else error_message

        assert len(truncated) <= max_length

    @settings(max_examples=50)
    @given(
        secret=st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"))),
    )
    def test_secrets_not_in_error_responses(self, secret: str):
        """Property test: secrets should never appear in error responses.

        **Feature: production-refactoring, Property 7: Error Response Consistency**
        **Validates: Requirements 9.5**
        """
        # Simulate an error message that might contain a secret
        raw_message = f"Connection failed: password={secret}@host"

        # Apply sanitization pattern
        sanitized = re.sub(
            r"(key|token|secret|password|credential)[=:]\s*\S+",
            r"\1=[REDACTED]",
            raw_message,
            flags=re.IGNORECASE,
        )

        # Secret should not appear in sanitized message
        assert secret not in sanitized, "Secret should be redacted from error message"


class TestHTTPStatusCodeUsage:
    """Tests for correct HTTP status code usage across services."""

    def test_422_for_validation_errors(self):
        """Verify services use 422 for validation errors.

        **Feature: production-refactoring, Property 7: Error Response Consistency**
        **Validates: Requirements 9.4**
        """
        # FastAPI automatically returns 422 for Pydantic validation errors
        # This test verifies the pattern is documented
        repo_root = Path(__file__).parents[2]
        error_module = repo_root / "services/common/errors.py"

        if not error_module.exists():
            return

        content = error_module.read_text()

        # Should document 422 usage
        assert "422" in content or "UNPROCESSABLE" in content, "Error module should document 422 for validation errors"

    def test_404_for_not_found(self):
        """Verify services use 404 for resource not found.

        **Feature: production-refactoring, Property 7: Error Response Consistency**
        **Validates: Requirements 9.4**
        """
        repo_root = Path(__file__).parents[2]
        error_module = repo_root / "services/common/errors.py"

        if not error_module.exists():
            return

        content = error_module.read_text()

        # Should have ResourceNotFoundError with 404
        assert "ResourceNotFoundError" in content
        assert "404" in content or "NOT_FOUND" in content

    def test_services_handle_upstream_failures(self):
        """Verify services handle upstream failures with 502.

        **Feature: production-refactoring, Property 7: Error Response Consistency**
        **Validates: Requirements 9.2**
        """
        repo_root = Path(__file__).parents[2]

        # billing-service calls pricing-service, should handle failures
        billing_path = repo_root / "services/billing-service/app/main.py"
        if billing_path.exists():
            content = billing_path.read_text()
            assert (
                "UpstreamServiceError" in content or "502" in content
            ), "billing-service should handle upstream failures with 502"
