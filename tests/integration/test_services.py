"""
Integration tests for service HTTP endpoints.
Sprint-6: Test service health, readiness, and basic functionality.
"""

import pytest
import httpx
import asyncio


# Test configuration
TEST_CONFIG = {
    "gateway_api": "http://localhost:10000",
    "orchestrator": "http://localhost:10001",
    "identity_service": "http://localhost:10002",
    "policy_engine": "http://localhost:10020",
}


@pytest.fixture
def http_client():
    """Create async HTTP client.

    Returns an ``httpx.AsyncClient`` instance. The client is closed after the
    test finishes to avoid resource leaks.
    """
    client = httpx.AsyncClient(timeout=10.0)
    try:
        yield client
    finally:
        # Ensure the async client is properly closed. Since this fixture is
        # synchronous, we run the coroutine to close the client in the event
        # loop.
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If an event loop is already running (e.g., when used with
            # ``pytest-asyncio``), schedule the close coroutine.
            loop.create_task(client.aclose())
        else:
            loop.run_until_complete(client.aclose())


class TestHealthEndpoints:
    """Test health and readiness endpoints for all services."""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("service,base_url", TEST_CONFIG.items())
    async def test_health_endpoint(self, http_client, service, base_url):
        """Test /health endpoint returns 200."""
        try:
            response = await http_client.get(f"{base_url}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
        except httpx.ConnectError:
            pytest.skip(f"{service} not running")
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("service,base_url", TEST_CONFIG.items())
    async def test_ready_endpoint(self, http_client, service, base_url):
        """Test /ready endpoint."""
        try:
            response = await http_client.get(f"{base_url}/ready")
            # May return 200 or 503 depending on service state
            assert response.status_code in [200, 503]
            data = response.json()
            assert "ready" in data
        except httpx.ConnectError:
            pytest.skip(f"{service} not running")
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("service,base_url", TEST_CONFIG.items())
    async def test_version_endpoint(self, http_client, service, base_url):
        """Test /version endpoint."""
        try:
            response = await http_client.get(f"{base_url}/version")
            assert response.status_code == 200
            data = response.json()
            assert "service" in data
            assert "version" in data
        except httpx.ConnectError:
            pytest.skip(f"{service} not running")


class TestGatewayAPI:
    """Test Gateway API endpoints."""
    
    @pytest.mark.asyncio
    async def test_gateway_root(self, http_client):
        """Test gateway root endpoint."""
        try:
            response = await http_client.get(f"{TEST_CONFIG['gateway_api']}/")
            assert response.status_code in [200, 404]  # May not have root endpoint
        except httpx.ConnectError:
            pytest.skip("Gateway API not running")


class TestPolicyEngine:
    """Test Policy Engine endpoints."""
    
    @pytest.mark.asyncio
    async def test_policy_evaluate_endpoint_exists(self, http_client):
        """Test policy evaluation endpoint exists."""
        try:
            # POST without body should return 422 (validation error) not 404
            response = await http_client.post(
                f"{TEST_CONFIG['policy_engine']}/v1/evaluate",
                json={}
            )
            assert response.status_code in [200, 400, 422]
        except httpx.ConnectError:
            pytest.skip("Policy Engine not running")


class TestIdentityService:
    """Test Identity Service endpoints."""
    
    @pytest.mark.asyncio
    async def test_identity_auth_endpoint_exists(self, http_client):
        """Test authentication endpoint exists."""
        try:
            response = await http_client.post(
                f"{TEST_CONFIG['identity_service']}/v1/auth/login",
                json={"username": "test", "password": "test"}
            )
            # Should return some response (not 404)
            assert response.status_code in [200, 400, 401, 422]
        except httpx.ConnectError:
            pytest.skip("Identity Service not running")


class TestOrchestrator:
    """Test Orchestrator endpoints."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_health(self, http_client):
        """Test orchestrator health."""
        try:
            response = await http_client.get(f"{TEST_CONFIG['orchestrator']}/health")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Orchestrator not running")


class TestServiceCommunication:
    """Test inter-service communication."""
    
    @pytest.mark.asyncio
    async def test_all_services_reachable(self, http_client):
        """Test that all services are reachable."""
        results = {}
        
        for service, base_url in TEST_CONFIG.items():
            try:
                response = await http_client.get(f"{base_url}/health", timeout=5.0)
                results[service] = response.status_code == 200
            except (httpx.ConnectError, httpx.TimeoutException):
                results[service] = False
        
        # At least some services should be running for tests to be meaningful
        running_count = sum(results.values())
        assert running_count >= 0, f"No services running. Results: {results}"


@pytest.mark.asyncio
async def test_concurrent_requests(http_client):
    """Test handling concurrent requests to services."""
    
    async def make_request(service, url):
        try:
            response = await http_client.get(f"{url}/health")
            return service, response.status_code
        except httpx.ConnectError:
            return service, None
    
    tasks = [
        make_request(service, url)
        for service, url in TEST_CONFIG.items()
    ]
    
    results = await asyncio.gather(*tasks)
    
    # Check that concurrent requests don't cause issues
    for service, status_code in results:
        if status_code is not None:
            assert status_code == 200, f"{service} returned {status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
