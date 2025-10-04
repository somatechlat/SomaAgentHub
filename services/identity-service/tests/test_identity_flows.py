from __future__ import annotations

from datetime import datetime, timezone

from fastapi import status


def test_user_token_flow(client) -> None:
    user_payload = {
        "user_id": "alice",
        "name": "Alice",
        "email": "alice@example.com",
        "capabilities": ["session:start", "session:stop"],
        "active": True,
    }

    resp = client.put("/v1/users/alice", json=user_payload)
    assert resp.status_code == status.HTTP_200_OK

    enroll = client.post("/v1/users/alice/mfa/enroll")
    assert enroll.status_code == status.HTTP_200_OK
    secret = enroll.json()["secret"]

    verify = client.post("/v1/users/alice/mfa/verify", json={"user_id": "alice", "code": secret})
    assert verify.status_code == status.HTTP_200_OK
    assert verify.json()["mfa_enabled"] is True

    issue_payload = {
        "user_id": "alice",
        "tenant_id": "tenant-1",
        "capabilities": ["session:start"],
        "mfa_code": secret,
    }
    issued = client.post("/v1/tokens/issue", json=issue_payload)
    assert issued.status_code == status.HTTP_200_OK
    token_body = issued.json()
    token = token_body["token"]
    assert token_body["token_type"] == "bearer"

    verify_payload = {"token": token, "required_capabilities": ["session:start"]}
    token_verify = client.post("/v1/tokens/verify", json=verify_payload)
    assert token_verify.status_code == status.HTTP_200_OK
    body = token_verify.json()
    assert body["valid"] is True
    assert body["user_id"] == "alice"
    assert body["tenant_id"] == "tenant-1"
    assert "session:start" in body["capabilities"]
    assert datetime.fromisoformat(body["expires_at"]) > datetime.now(timezone.utc)

    revoke = client.post("/v1/tokens/revoke", json={"token": token})
    assert revoke.status_code == status.HTTP_200_OK
    assert revoke.json()["revoked"] is True

    revoked_verify = client.post("/v1/tokens/verify", json=verify_payload)
    assert revoked_verify.status_code == status.HTTP_401_UNAUTHORIZED


def test_training_lock_flow(client) -> None:
    start_payload = {"tenant_id": "tenant-2", "requested_by": "alice"}
    start = client.post("/v1/training/start", json=start_payload)
    assert start.status_code == status.HTTP_200_OK
    assert start.json()["locked"] is True

    status_resp = client.get("/v1/training/tenant-2")
    assert status_resp.status_code == status.HTTP_200_OK
    assert status_resp.json()["locked"] is True

    stop = client.post("/v1/training/stop", json=start_payload)
    assert stop.status_code == status.HTTP_200_OK
    assert stop.json()["locked"] is False

    final_status = client.get("/v1/training/tenant-2")
    assert final_status.status_code == status.HTTP_200_OK
    assert final_status.json()["locked"] is False
