import json
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.constitution import verify_bundle
from app.core.models import ConstitutionBundle
from app.main import create_app


@pytest.fixture()
def client():
	app = create_app()
	with TestClient(app) as test_client:
		yield test_client


def _load_bundle_from_disk() -> dict:
	return json.loads(settings.bundle_path.read_text(encoding="utf-8"))


def test_constitution_summary_matches_bundle(client):
	response = client.get("/v1/constitution")
	assert response.status_code == 200
	data = response.json()
	bundle = _load_bundle_from_disk()
	assert data["version"] == bundle["version"]
	assert data["hash"] == bundle["hash"]


def test_constitution_endpoint_returns_verified_document(client):
	response = client.get("/v1/constitution/tenantA")
	assert response.status_code == 200
	payload = response.json()
	bundle = ConstitutionBundle.model_validate(payload)
	verify_bundle(bundle, settings.public_key_path)


def test_hash_endpoint(client):
	response = client.get("/v1/constitution/tenantA/hash")
	assert response.status_code == 200
	hash_payload = response.json()
	bundle = _load_bundle_from_disk()
	assert hash_payload["hash"] == bundle["hash"]


def test_validation_endpoint_detects_tampering(client):
	bundle = _load_bundle_from_disk()
	valid_resp = client.post("/v1/constitution/validate", json=bundle)
	assert valid_resp.status_code == 200
	assert valid_resp.json()["valid"] is True

	tampered = deepcopy(bundle)
	tampered["document"]["preamble"] = "Tampered preamble"
	tampered_resp = client.post("/v1/constitution/validate", json=tampered)
	assert tampered_resp.status_code == 200
	body = tampered_resp.json()
	assert body["valid"] is False
	assert body["issues"]
