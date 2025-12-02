import io

import pytest

# Import using the underscore‑based package name (the hyphenated package name
# is not a valid Python identifier). The repository provides an alias package
# ``services.object_store`` that re‑exports the client implementation.
from services.object_store.app.client import ObjectStoreClient, ObjectStoreSettings
from services.common.config.base_settings import resolve_env


class DummyMinio:
	def __init__(self, *a, **kw):
		self.objects = {}
		self.buckets = set()

	def bucket_exists(self, bucket):
		return bucket in self.buckets

	def make_bucket(self, bucket):
		self.buckets.add(bucket)

	def put_object(
		self,
		bucket_name,
		object_name,
		data,
		length,
		content_type="application/octet-stream",
	):
		# Store the raw bytes for verification if needed.
		self.objects[(bucket_name, object_name)] = data.read(length)

	def presigned_get_object(self, bucket, object_name, expires):
		return (
			f"http://example/{bucket}/{object_name}?exp={int(expires.total_seconds())}"
		)

	def remove_object(self, bucket, object_name):
		self.objects.pop((bucket, object_name), None)


  @pytest.fixture(autouse=True)
  def patch_minio(monkeypatch):
	monkeypatch.setenv("MINIO_ENDPOINT", "localhost:9000")
	monkeypatch.setenv("MINIO_ACCESS_KEY", "test")
	monkeypatch.setenv("MINIO_SECRET_KEY", "test")
	monkeypatch.setenv("MINIO_SECURE", "false")

	# Import the module using the underscore alias for the same reason.
	import services.object_store.app.client as mod

	monkeypatch.setattr(mod, "Minio", DummyMinio)
	yield


 def test_upload_and_presign():
	client = ObjectStoreClient(ObjectStoreSettings.from_env())
	data = io.BytesIO(b"hello world")
	s3_url = client.upload(
		"tenant/capsule/v1/out.txt", data, length=11, content_type="text/plain"
	)
	assert s3_url.startswith("s3://")
	presigned = client.presign_get("tenant/capsule/v1/out.txt")
	assert presigned.startswith("http://example/")
