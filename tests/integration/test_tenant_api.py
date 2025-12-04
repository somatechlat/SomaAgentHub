import pytest
import uuid
from httpx import AsyncClient
from services.common.models.identity import TenantStatus

# Mark as integration tests
pytestmark = pytest.mark.integration

@pytest.mark.asyncio
class TestTenantAPI:
    async def test_tenant_lifecycle(self, async_client: AsyncClient):
        """Test full tenant lifecycle via API"""
        
        # 1. Create Tenant
        tenant_name = f"API Tenant {uuid.uuid4()}"
        response = await async_client.post(
            "/v1/tenants/",
            json={"name": tenant_name}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == tenant_name
        assert data["status"] == TenantStatus.ACTIVE
        tenant_id = data["id"]

        # 2. Get Tenant
        response = await async_client.get(f"/v1/tenants/{tenant_id}")
        assert response.status_code == 200
        assert response.json()["id"] == tenant_id

        # 3. List Tenants
        response = await async_client.get("/v1/tenants/")
        assert response.status_code == 200
        tenants = response.json()
        assert any(t["id"] == tenant_id for t in tenants)

        # 4. Update Status
        response = await async_client.patch(
            f"/v1/tenants/{tenant_id}/status",
            params={"status": TenantStatus.SUSPENDED}
        )
        assert response.status_code == 200
        assert response.json()["status"] == TenantStatus.SUSPENDED

        # 5. Delete Tenant
        response = await async_client.delete(f"/v1/tenants/{tenant_id}")
        assert response.status_code == 204

        # Verify Deletion (Soft Delete)
        response = await async_client.get(f"/v1/tenants/{tenant_id}")
        assert response.status_code == 200
        assert response.json()["status"] == TenantStatus.DELETED

    async def test_create_duplicate_tenant(self, async_client: AsyncClient):
        """Test creating a tenant with a duplicate name"""
        tenant_name = f"Duplicate Tenant {uuid.uuid4()}"
        
        # First creation
        response = await async_client.post(
            "/v1/tenants/",
            json={"name": tenant_name}
        )
        assert response.status_code == 201

        # Second creation (should fail)
        response = await async_client.post(
            "/v1/tenants/",
            json={"name": tenant_name}
        )
        assert response.status_code == 409
