import pytest
from httpx import AsyncClient
from fastapi import status

from services.marketplace.app.main import app

@pytest.mark.asyncio
async def test_capsule_crud():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # health
        health = await client.get("/health")
        assert health.status_code == status.HTTP_200_OK
        # create a capsule
        payload = {"name": "demo", "description": "demo capsule", "version": "1.0"}
        resp = await client.post("/v1/marketplace", json=payload)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        capsule_id = data["id"]
        # list capsules
        list_resp = await client.get("/v1/marketplace")
        assert list_resp.status_code == status.HTTP_200_OK
        ids = [c["id"] for c in list_resp.json()]
        assert capsule_id in ids
        # get capsule
        get_resp = await client.get(f"/v1/marketplace/{capsule_id}")
        assert get_resp.status_code == status.HTTP_200_OK
        assert get_resp.json()["name"] == "demo"
        # delete capsule
        del_resp = await client.delete(f"/v1/marketplace/{capsule_id}")
        assert del_resp.status_code == status.HTTP_200_OK
        # ensure it is gone
        not_found = await client.get(f"/v1/marketplace/{capsule_id}")
        assert not_found.status_code == status.HTTP_404_NOT_FOUND
