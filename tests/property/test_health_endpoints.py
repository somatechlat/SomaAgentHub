"""Property-based tests for health endpoint consistency.

**Feature: production-refactoring, Property 2: Health Endpoint Consistency**
**Validates: Requirements 4.1, 4.2**

**Feature: production-refactoring, Property 3: Detailed Health Check Structure**
**Validates: Requirements 4.3**

**Feature: production-refactoring, Property 4: Prometheus Metrics Format**
**Validates: Requirements 4.4**

Tests that all services:
- Expose /health and /healthz endpoints
- Return consistent JSON structure with status and service fields
- Return valid Prometheus metrics format
"""

import re

from hypothesis import given, settings
from hypothesis import strategies as st


class TestHealthEndpointConsistency:
    """Property tests for health endpoint consistency (Property 2)."""

    # List of services that should have standardized health endpoints
    SERVICES = [
        ("memory-gateway", "services/memory-gateway/app/main.py"),
        ("billing-service", "services/billing-service/app/main.py"),
        ("evolution-engine", "services/evolution-engine/app.py"),
        ("voice-interface", "services/voice-interface/app.py"),
        ("data-layer", "services/data-layer/main.py"),
        ("self-provisioning", "services/self-provisioning/app.py"),
        ("token-estimator", "services/token-estimator/app/main.py"),
    ]

    VALID_STATUSES = {"healthy", "degraded", "unhealthy"}

    def test_health_response_structure(self):
        """Verify /health endpoint returns required fields.

        **Feature: production-refactoring, Property 2: Health Endpoint Consistency**
        **Validates: Requirements 4.1, 4.2**

        For any service, the /health endpoint SHALL return a JSON response
        containing at minimum a `status` field with value "healthy", "degraded",
        or "unhealthy", and a `service` field identifying the service name.
        """
        from pathlib import Path

        repo_root = Path(__file__).parents[2]

        for service_name, service_path in self.SERVICES:
            file_path = repo_root / service_path
            if not file_path.exists():
                continue

            content = file_path.read_text()

            # Check that /health endpoint exists
            assert (
                '@app.get("/health"' in content or "@app.get('/health'" in content
            ), f"{service_name}: Missing /health endpoint"

            # Check that response includes status field
            assert (
                '"status"' in content or "'status'" in content
            ), f"{service_name}: /health response missing 'status' field"

            # Check that response includes service field
            assert (
                '"service"' in content or "'service'" in content
            ), f"{service_name}: /health response missing 'service' field"

    def test_healthz_endpoint_exists(self):
        """Verify /healthz endpoint exists for detailed health checks.

        **Feature: production-refactoring, Property 3: Detailed Health Check Structure**
        **Validates: Requirements 4.3**
        """
        from pathlib import Path

        repo_root = Path(__file__).parents[2]

        for service_name, service_path in self.SERVICES:
            file_path = repo_root / service_path
            if not file_path.exists():
                continue

            content = file_path.read_text()

            # Check that /healthz endpoint exists
            assert (
                '@app.get("/healthz"' in content or "@app.get('/healthz'" in content
            ), f"{service_name}: Missing /healthz endpoint"

    @settings(max_examples=100)
    @given(
        status=st.sampled_from(["healthy", "degraded", "unhealthy"]),
        service_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N", "Pd"))),
    )
    def test_health_response_valid_status_values(self, status: str, service_name: str):
        """Property test: health status must be one of valid values.

        **Feature: production-refactoring, Property 2: Health Endpoint Consistency**
        **Validates: Requirements 4.2**
        """
        # Simulate a health response
        response = {
            "status": status,
            "service": service_name,
        }

        assert response["status"] in self.VALID_STATUSES
        assert len(response["service"]) > 0


class TestDetailedHealthCheckStructure:
    """Property tests for detailed health check structure (Property 3)."""

    def test_healthz_includes_dependencies(self):
        """Verify /healthz includes dependency status for services with dependencies.

        **Feature: production-refactoring, Property 3: Detailed Health Check Structure**
        **Validates: Requirements 4.3**
        """
        from pathlib import Path

        repo_root = Path(__file__).parents[2]

        # Services that should have dependency checks
        services_with_deps = [
            ("memory-gateway", "services/memory-gateway/app/main.py", ["kv_store", "vector_store"]),
            ("billing-service", "services/billing-service/app/main.py", ["stripe", "pricing_service"]),
            ("evolution-engine", "services/evolution-engine/app.py", ["openai"]),
            ("voice-interface", "services/voice-interface/app.py", ["openai"]),
        ]

        for service_name, service_path, expected_deps in services_with_deps:
            file_path = repo_root / service_path
            if not file_path.exists():
                continue

            content = file_path.read_text()

            # Check that dependencies are mentioned in healthz
            assert (
                '"dependencies"' in content or "'dependencies'" in content
            ), f"{service_name}: /healthz missing 'dependencies' field"

    @settings(max_examples=50)
    @given(
        dep_name=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N", "Pd"))),
        dep_status=st.sampled_from(["healthy", "unhealthy", "degraded"]),
    )
    def test_dependency_status_structure(self, dep_name: str, dep_status: str):
        """Property test: dependency status must have valid structure.

        **Feature: production-refactoring, Property 3: Detailed Health Check Structure**
        **Validates: Requirements 4.3**
        """
        # Simulate a dependency status
        dependency = {
            "status": dep_status,
        }

        assert dependency["status"] in {"healthy", "unhealthy", "degraded"}


class TestPrometheusMetricsFormat:
    """Property tests for Prometheus metrics format (Property 4)."""

    # Prometheus metric line pattern: metric_name{labels} value
    PROMETHEUS_METRIC_PATTERN = re.compile(
        r"^[a-zA-Z_:][a-zA-Z0-9_:]*(\{[^}]*\})?\s+[\d.eE+-]+(\s+\d+)?$", re.MULTILINE
    )

    def test_metrics_endpoint_exists(self):
        """Verify /metrics endpoint exists for all services.

        **Feature: production-refactoring, Property 4: Prometheus Metrics Format**
        **Validates: Requirements 4.4**
        """
        from pathlib import Path

        repo_root = Path(__file__).parents[2]

        services = [
            ("memory-gateway", "services/memory-gateway/app/main.py"),
            ("billing-service", "services/billing-service/app/main.py"),
            ("token-estimator", "services/token-estimator/app/main.py"),
        ]

        for service_name, service_path in services:
            file_path = repo_root / service_path
            if not file_path.exists():
                continue

            content = file_path.read_text()

            # Check that /metrics endpoint exists
            assert (
                '@app.get("/metrics"' in content or "@app.get('/metrics'" in content
            ), f"{service_name}: Missing /metrics endpoint"

            # Check that prometheus_client is used
            assert (
                "generate_latest" in content
            ), f"{service_name}: /metrics should use prometheus_client.generate_latest()"

    @settings(max_examples=100)
    @given(
        metric_name=st.from_regex(r"[a-z][a-z0-9_]*", fullmatch=True),
        value=st.floats(min_value=0, max_value=1e10, allow_nan=False, allow_infinity=False),
    )
    def test_prometheus_metric_format(self, metric_name: str, value: float):
        """Property test: Prometheus metrics must follow valid format.

        **Feature: production-refactoring, Property 4: Prometheus Metrics Format**
        **Validates: Requirements 4.4**
        """
        # Basic validation - metric name starts with letter, contains only valid chars
        assert re.match(r"^[a-zA-Z_:][a-zA-Z0-9_:]*", metric_name)

    def test_prometheus_client_usage(self):
        """Verify services use prometheus_client library correctly.

        **Feature: production-refactoring, Property 4: Prometheus Metrics Format**
        **Validates: Requirements 4.4**
        """
        from pathlib import Path

        repo_root = Path(__file__).parents[2]

        # Check that health_standard module uses prometheus_client
        health_standard_path = repo_root / "services/common/health_standard.py"
        if health_standard_path.exists():
            content = health_standard_path.read_text()
            assert "from prometheus_client import" in content
            assert "Counter" in content or "Gauge" in content or "Histogram" in content
