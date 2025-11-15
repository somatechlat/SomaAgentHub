"""
Test configuration for governance service.

Provides common fixtures and setup for all test suites.
"""

import asyncio
import pytest
import sys
from pathlib import Path

# Add the services directory to the Python path
services_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(services_dir))

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

# Add the parent directory to the Python path for imports
parent_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(parent_dir))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def anyio_backend():
    """Backend for anyio pytest plugin."""
    return "asyncio"


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment for each test."""
    # Reset any global state here if needed
    yield
    # Clean up after each test


@pytest.fixture
def test_service_account_data():
    """Sample service account data for testing."""
    return {
        "service_name": "test-service",
        "namespace": "test-namespace",
        "roles": ["test-role"],
        "permissions": ["read", "write"],
        "metadata": {"env": "test", "version": "1.0.0"},
    }


@pytest.fixture
def test_token_data():
    """Sample token data for testing."""
    return {
        "token_type": "access",
        "scopes": ["read", "write"],
        "metadata": {"purpose": "testing"},
    }