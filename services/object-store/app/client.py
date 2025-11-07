from __future__ import annotations

import os
import datetime as dt
from dataclasses import dataclass
from typing import BinaryIO, Optional

from minio import Minio
from minio.error import S3Error


@dataclass
class ObjectStoreSettings:
    endpoint: str
    access_key: str
    secret_key: str
    secure: bool = False
    default_bucket: str = "somagent-artifacts"

    @classmethod
    def from_env(cls) -> "ObjectStoreSettings":
        endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        secure = os.getenv("MINIO_SECURE", "false").lower() in {"1", "true", "yes"}
        default_bucket = os.getenv("MINIO_DEFAULT_BUCKET", "somagent-artifacts")
        return cls(endpoint, access_key, secret_key, secure, default_bucket)


class ObjectStoreClient:
    def __init__(self, settings: Optional[ObjectStoreSettings] = None) -> None:
        self.settings = settings or ObjectStoreSettings.from_env()
        self._client = Minio(
            endpoint=self.settings.endpoint,
            access_key=self.settings.access_key,
            secret_key=self.settings.secret_key,
            secure=self.settings.secure,
        )

    def ensure_bucket(self, bucket: Optional[str] = None) -> str:
        bucket = bucket or self.settings.default_bucket
        if not self._client.bucket_exists(bucket):
            self._client.make_bucket(bucket)
        return bucket

    def upload(self, object_name: str, data: BinaryIO, length: int, bucket: Optional[str] = None, content_type: str = "application/octet-stream") -> str:
        bucket = self.ensure_bucket(bucket)
        self._client.put_object(
            bucket_name=bucket,
            object_name=object_name,
            data=data,
            length=length,
            content_type=content_type,
        )
        return f"s3://{bucket}/{object_name}"

    def presign_get(self, object_name: str, bucket: Optional[str] = None, expires_seconds: int = 3600) -> str:
        bucket = bucket or self.settings.default_bucket
        return self._client.presigned_get_object(
            bucket,
            object_name,
            expires=dt.timedelta(seconds=expires_seconds),
        )

    def delete(self, object_name: str, bucket: Optional[str] = None) -> None:
        bucket = bucket or self.settings.default_bucket
        try:
            self._client.remove_object(bucket, object_name)
        except S3Error as exc:  # ignore not found
            if exc.code != "NoSuchKey":
                raise
