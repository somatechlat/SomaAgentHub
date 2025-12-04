import pytest
from unittest.mock import MagicMock, patch
from somaagent.client import SomaAgentClient
from somaagent.models import TenantRef, TaskRecord, RoleDefinition

# Since Docker is unavailable, we mock the requests library to verify client logic
# This ensures the SDK code is correct even if we can't hit the backend.

@pytest.fixture
def mock_client():
    with patch("requests.Session") as mock_session:
        client = SomaAgentClient(api_key="test-key", base_url="http://test-api")
        client.session = mock_session.return_value
        yield client

def test_create_tenant(mock_client):
    mock_client.session.request.return_value.json.return_value = {
        "id": "tenant-123",
        "name": "Test Tenant",
        "tier": "free",
        "status": "active"
    }
    mock_client.session.request.return_value.status_code = 200

    result = mock_client.create_tenant("Test Tenant")
    
    assert result["id"] == "tenant-123"
    assert result["name"] == "Test Tenant"
    mock_client.session.request.assert_called_with(
        "POST", "http://test-api/v1/tenants", 
        timeout=30, 
        json={"name": "Test Tenant", "tier": "free"}
    )

def test_create_task(mock_client):
    mock_client.session.request.return_value.json.return_value = {
        "id": "task-123",
        "name": "Test Task",
        "workflow_instance_id": "wf-123",
        "priority": "high"
    }
    mock_client.session.request.return_value.status_code = 200

    result = mock_client.create_task("Test Task", "wf-123", "high")
    
    assert result["id"] == "task-123"
    mock_client.session.request.assert_called_with(
        "POST", "http://test-api/v1/tasks", 
        timeout=30, 
        json={"name": "Test Task", "workflow_instance_id": "wf-123", "priority": "high"}
    )

def test_create_role(mock_client):
    mock_client.session.request.return_value.json.return_value = {
        "id": "role-123",
        "name": "Developer",
        "description": "Writes code",
        "capabilities": ["code.write"]
    }
    mock_client.session.request.return_value.status_code = 200

    result = mock_client.create_role("Developer", "Writes code", ["code.write"])
    
    assert result["name"] == "Developer"
    mock_client.session.request.assert_called_with(
        "POST", "http://test-api/v1/roles", 
        timeout=30, 
        json={"name": "Developer", "description": "Writes code", "capabilities": ["code.write"]}
    )
