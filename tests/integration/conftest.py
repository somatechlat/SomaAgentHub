"""
⚠️ WE DO NOT MOCK - We test against REAL APIs with sandbox/test accounts.
We use REAL data, REAL servers, and validate ACTUAL behavior.

Integration Test Fixtures and Configuration
Provides reusable fixtures for testing tool adapters with real API endpoints.
"""

import os
import pytest
import asyncio
from typing import Dict, Any
from datetime import datetime

# Tool adapter imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services/tool-service'))

from tool_registry import tool_registry


# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================

@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Load test configuration from environment variables."""
    return {
        # Plane.so test account
        "plane_api_url": os.getenv("PLANE_TEST_API_URL", "https://api.plane.so"),
        "plane_api_key": os.getenv("PLANE_TEST_API_KEY"),
        "plane_workspace_slug": os.getenv("PLANE_TEST_WORKSPACE", "test-workspace"),
        
        # GitHub test account
        "github_token": os.getenv("GITHUB_TEST_TOKEN"),
        "github_org": os.getenv("GITHUB_TEST_ORG", "somagent-test"),
        
        # Notion test workspace
        "notion_token": os.getenv("NOTION_TEST_TOKEN"),
        "notion_database_id": os.getenv("NOTION_TEST_DATABASE_ID"),
        
        # Slack test workspace
        "slack_token": os.getenv("SLACK_TEST_BOT_TOKEN"),
        "slack_test_channel": os.getenv("SLACK_TEST_CHANNEL", "test-automation"),
        
        # Terraform (local state for testing)
        "terraform_working_dir": os.getenv("TERRAFORM_TEST_DIR", "/tmp/terraform-test"),
        
        # AWS test account (isolated test environment)
        "aws_access_key": os.getenv("AWS_TEST_ACCESS_KEY_ID"),
        "aws_secret_key": os.getenv("AWS_TEST_SECRET_ACCESS_KEY"),
        "aws_region": os.getenv("AWS_TEST_REGION", "us-east-1"),
        
        # Kubernetes (kind/minikube for testing)
        "kubeconfig_path": os.getenv("KUBECONFIG_TEST_PATH", "~/.kube/config-test"),
        
        # Jira test instance
        "jira_url": os.getenv("JIRA_TEST_URL"),
        "jira_email": os.getenv("JIRA_TEST_EMAIL"),
        "jira_api_token": os.getenv("JIRA_TEST_API_TOKEN"),
        "jira_project_key": os.getenv("JIRA_TEST_PROJECT", "TEST"),
        
        # Test timeouts
        "api_timeout": int(os.getenv("TEST_API_TIMEOUT", "30")),
        "long_timeout": int(os.getenv("TEST_LONG_TIMEOUT", "120")),
    }


@pytest.fixture(scope="session")
def check_test_credentials(test_config):
    """Verify that required test credentials are available."""
    missing = []
    
    # Critical credentials
    if not test_config["github_token"]:
        missing.append("GITHUB_TEST_TOKEN")
    if not test_config["slack_token"]:
        missing.append("SLACK_TEST_BOT_TOKEN")
    
    if missing:
        pytest.skip(f"Missing test credentials: {', '.join(missing)}. Set environment variables to run integration tests.")
    
    return True


# ============================================================================
# TOOL ADAPTER FIXTURES
# ============================================================================

@pytest.fixture
def plane_adapter(test_config, check_test_credentials):
    """Plane.so adapter configured for test workspace."""
    if not test_config["plane_api_key"]:
        pytest.skip("Plane.so test credentials not configured")
    
    from adapters.plane_adapter import PlaneAdapter
    return PlaneAdapter(
        api_url=test_config["plane_api_url"],
        api_key=test_config["plane_api_key"],
        workspace_slug=test_config["plane_workspace_slug"]
    )


@pytest.fixture
def github_adapter(test_config, check_test_credentials):
    """GitHub adapter configured for test organization."""
    from adapters.github_adapter import GitHubAdapter
    return GitHubAdapter(token=test_config["github_token"])


@pytest.fixture
def notion_adapter(test_config):
    """Notion adapter configured for test workspace."""
    if not test_config["notion_token"]:
        pytest.skip("Notion test credentials not configured")
    
    from adapters.notion_adapter import NotionAdapter
    return NotionAdapter(token=test_config["notion_token"])


@pytest.fixture
def slack_adapter(test_config, check_test_credentials):
    """Slack adapter configured for test workspace."""
    from adapters.slack_adapter import SlackAdapter
    return SlackAdapter(bot_token=test_config["slack_token"])


@pytest.fixture
def terraform_adapter(test_config, tmp_path):
    """Terraform adapter with temporary working directory."""
    working_dir = tmp_path / "terraform"
    working_dir.mkdir()
    from adapters.terraform_adapter import TerraformAdapter
    return TerraformAdapter(working_dir=str(working_dir))


@pytest.fixture
def aws_adapter(test_config):
    """AWS adapter configured for test account (real boto3)."""
    if not test_config["aws_access_key"]:
        pytest.skip("AWS test credentials not configured")
    from adapters.aws_adapter import AWSAdapter
    return AWSAdapter(
        aws_access_key_id=test_config["aws_access_key"],
        aws_secret_access_key=test_config["aws_secret_key"],
        region_name=test_config["aws_region"],
    )


@pytest.fixture
def kubernetes_adapter(test_config):
    """Kubernetes adapter configured for test cluster."""
    kubeconfig = os.path.expanduser(test_config["kubeconfig_path"])
    if not os.path.exists(kubeconfig):
        pytest.skip("Kubernetes test cluster not configured")
    from adapters.kubernetes_adapter import KubernetesAdapter
    return KubernetesAdapter(kubeconfig_path=kubeconfig)


@pytest.fixture
def jira_adapter(test_config):
    """Jira adapter configured for test instance."""
    if not test_config["jira_url"] or not test_config["jira_api_token"]:
        pytest.skip("Jira test credentials not configured")
    
    from adapters.jira_adapter import JiraAdapter
    return JiraAdapter(
        url=test_config["jira_url"],
        email=test_config["jira_email"],
        api_token=test_config["jira_api_token"]
    )


@pytest.fixture
async def playwright_adapter():
    """Playwright adapter for browser automation tests."""
    from adapters.playwright_adapter import PlaywrightAdapter
    adapter = PlaywrightAdapter()
    yield adapter
    # Cleanup is handled by adapter's context manager


# ============================================================================
# TOOL REGISTRY FIXTURE
# ============================================================================

@pytest.fixture
def configured_tool_registry(test_config):
    """Tool registry with all adapters configured with test credentials."""
    credentials = {
        "plane": {
            "api_url": test_config["plane_api_url"],
            "api_key": test_config["plane_api_key"],
            "workspace_slug": test_config["plane_workspace_slug"]
        },
        "github": {"token": test_config["github_token"]},
        "notion": {"token": test_config["notion_token"]},
        "slack": {"bot_token": test_config["slack_token"]},
        "aws": {
            "access_key_id": test_config["aws_access_key"],
            "secret_access_key": test_config["aws_secret_key"],
            "region": test_config["aws_region"]
        },
        "kubernetes": {"kubeconfig_path": test_config["kubeconfig_path"]},
        "jira": {
            "url": test_config["jira_url"],
            "email": test_config["jira_email"],
            "api_token": test_config["jira_api_token"]
        }
    }
    
    # Pre-configure registry with test credentials
    for tool_name, creds in credentials.items():
        if all(creds.values()):  # Only configure if all credentials present
            tool_registry.get_adapter(tool_name, credentials=creds)
    
    return tool_registry


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture
def test_resource_tracker():
    """Track created resources for cleanup after tests."""
    resources = {
        "github_repos": [],
        "slack_channels": [],
        "plane_projects": [],
        "jira_projects": [],
        "aws_instances": [],
        "k8s_namespaces": [],
        "notion_pages": []
    }
    
    yield resources
    
    # Cleanup happens in individual test teardown


@pytest.fixture(autouse=True)
def test_isolation(request):
    """Ensure test isolation with unique identifiers."""
    test_id = f"test-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{request.node.name[:20]}"
    request.node.test_id = test_id
    return test_id


# ============================================================================
# ASSERTION HELPERS
# ============================================================================

@pytest.fixture
def assert_api_success():
    """Helper to assert API call succeeded."""
    def _assert(response, message="API call failed"):
        assert response is not None, f"{message}: response is None"
        if isinstance(response, dict):
            assert "error" not in response, f"{message}: {response.get('error')}"
        return response
    return _assert


@pytest.fixture
def assert_within_timeout():
    """Helper to assert operation completed within timeout."""
    def _assert(duration_seconds, max_seconds, operation_name):
        assert duration_seconds <= max_seconds, \
            f"{operation_name} took {duration_seconds}s, expected <{max_seconds}s"
    return _assert


# ============================================================================
# ASYNC HELPERS
# ============================================================================

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# PERFORMANCE METRICS
# ============================================================================

@pytest.fixture
def performance_tracker():
    """Track performance metrics during tests."""
    metrics = {
        "api_calls": [],
        "latencies": [],
        "errors": []
    }
    
    def record_call(tool_name, method, latency_ms, success):
        metrics["api_calls"].append({
            "tool": tool_name,
            "method": method,
            "latency_ms": latency_ms,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        })
        metrics["latencies"].append(latency_ms)
        if not success:
            metrics["errors"].append({"tool": tool_name, "method": method})
    
    metrics["record"] = record_call
    
    yield metrics
    
    # Calculate P95 latency
    if metrics["latencies"]:
        sorted_latencies = sorted(metrics["latencies"])
        p95_index = int(len(sorted_latencies) * 0.95)
        metrics["p95_latency"] = sorted_latencies[p95_index]
        metrics["avg_latency"] = sum(sorted_latencies) / len(sorted_latencies)
        metrics["max_latency"] = max(sorted_latencies)
        metrics["success_rate"] = (len(metrics["api_calls"]) - len(metrics["errors"])) / len(metrics["api_calls"])

        print("\n=== Performance Metrics ===")
        print(f"Total API calls: {len(metrics['api_calls'])}")
        print(f"Success rate: {metrics['success_rate']*100:.2f}%")
        print(f"Avg latency: {metrics['avg_latency']:.2f}ms")
        print(f"P95 latency: {metrics['p95_latency']:.2f}ms")
        print(f"Max latency: {metrics['max_latency']:.2f}ms")
