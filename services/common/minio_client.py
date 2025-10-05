"""MinIO S3-compatible object storage client for SomaGent platform.

Provides artifact storage for task capsules, workspace files, and generated outputs.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional
from functools import lru_cache
from io import BytesIO

try:
    from minio import Minio
    from minio.error import S3Error
    from urllib3.response import HTTPResponse
except ImportError:
    Minio = None
    S3Error = Exception
    HTTPResponse = None


class MinIOClient:
    """Client for MinIO S3-compatible object storage."""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool = True,
        region: str = "us-east-1",
    ):
        """Initialize MinIO client.
        
        Args:
            endpoint: MinIO server endpoint (e.g., "minio:9000")
            access_key: Access key ID
            secret_key: Secret access key
            secure: Use HTTPS (default: True)
            region: S3 region name
        """
        if Minio is None:
            raise ImportError(
                "minio package not installed. Install with: pip install minio"
            )
        
        self.endpoint = endpoint
        self.region = region
        
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region=region,
        )

    def create_bucket(self, bucket_name: str) -> None:
        """Create a bucket if it doesn't exist.
        
        Args:
            bucket_name: Name of the bucket to create
        """
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name, location=self.region)
        except S3Error as exc:
            raise RuntimeError(f"Failed to create bucket {bucket_name}: {exc}") from exc

    def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """Upload a file to MinIO.
        
        Args:
            bucket_name: Target bucket name
            object_name: Object name (key) in bucket
            file_path: Path to local file
            content_type: MIME type (auto-detected if not provided)
            metadata: Optional metadata tags
            
        Returns:
            Object ETag
        """
        try:
            result = self.client.fput_object(
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=file_path,
                content_type=content_type,
                metadata=metadata,
            )
            return result.etag
        except S3Error as exc:
            raise RuntimeError(
                f"Failed to upload {file_path} to {bucket_name}/{object_name}: {exc}"
            ) from exc

    def upload_bytes(
        self,
        bucket_name: str,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """Upload bytes to MinIO.
        
        Args:
            bucket_name: Target bucket name
            object_name: Object name (key) in bucket
            data: Bytes to upload
            content_type: MIME type
            metadata: Optional metadata tags
            
        Returns:
            Object ETag
        """
        try:
            result = self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=BytesIO(data),
                length=len(data),
                content_type=content_type,
                metadata=metadata,
            )
            return result.etag
        except S3Error as exc:
            raise RuntimeError(
                f"Failed to upload bytes to {bucket_name}/{object_name}: {exc}"
            ) from exc

    def download_file(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str,
    ) -> None:
        """Download a file from MinIO.
        
        Args:
            bucket_name: Source bucket name
            object_name: Object name (key) in bucket
            file_path: Path to save downloaded file
        """
        try:
            self.client.fget_object(
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=file_path,
            )
        except S3Error as exc:
            raise RuntimeError(
                f"Failed to download {bucket_name}/{object_name}: {exc}"
            ) from exc

    def download_bytes(
        self,
        bucket_name: str,
        object_name: str,
    ) -> bytes:
        """Download object as bytes from MinIO.
        
        Args:
            bucket_name: Source bucket name
            object_name: Object name (key) in bucket
            
        Returns:
            Object data as bytes
        """
        try:
            response = self.client.get_object(
                bucket_name=bucket_name,
                object_name=object_name,
            )
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as exc:
            raise RuntimeError(
                f"Failed to download {bucket_name}/{object_name}: {exc}"
            ) from exc

    def delete_object(
        self,
        bucket_name: str,
        object_name: str,
    ) -> None:
        """Delete an object from MinIO.
        
        Args:
            bucket_name: Bucket name
            object_name: Object name (key) to delete
        """
        try:
            self.client.remove_object(
                bucket_name=bucket_name,
                object_name=object_name,
            )
        except S3Error as exc:
            raise RuntimeError(
                f"Failed to delete {bucket_name}/{object_name}: {exc}"
            ) from exc

    def delete_objects(
        self,
        bucket_name: str,
        object_names: List[str],
    ) -> None:
        """Delete multiple objects from MinIO.
        
        Args:
            bucket_name: Bucket name
            object_names: List of object names to delete
        """
        try:
            errors = self.client.remove_objects(
                bucket_name=bucket_name,
                delete_object_list=object_names,
            )
            # Check if any deletions failed
            error_list = list(errors)
            if error_list:
                raise RuntimeError(f"Failed to delete some objects: {error_list}")
        except S3Error as exc:
            raise RuntimeError(
                f"Failed to delete objects from {bucket_name}: {exc}"
            ) from exc

    def list_objects(
        self,
        bucket_name: str,
        prefix: Optional[str] = None,
        recursive: bool = True,
    ) -> List[str]:
        """List objects in a bucket.
        
        Args:
            bucket_name: Bucket name
            prefix: Filter by prefix (optional)
            recursive: List recursively (default: True)
            
        Returns:
            List of object names
        """
        try:
            objects = self.client.list_objects(
                bucket_name=bucket_name,
                prefix=prefix,
                recursive=recursive,
            )
            return [obj.object_name for obj in objects]
        except S3Error as exc:
            raise RuntimeError(
                f"Failed to list objects in {bucket_name}: {exc}"
            ) from exc

    def get_object_metadata(
        self,
        bucket_name: str,
        object_name: str,
    ) -> Dict[str, any]:
        """Get object metadata.
        
        Args:
            bucket_name: Bucket name
            object_name: Object name
            
        Returns:
            Object metadata dictionary
        """
        try:
            stat = self.client.stat_object(
                bucket_name=bucket_name,
                object_name=object_name,
            )
            return {
                "size": stat.size,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "last_modified": stat.last_modified,
                "metadata": stat.metadata,
            }
        except S3Error as exc:
            raise RuntimeError(
                f"Failed to get metadata for {bucket_name}/{object_name}: {exc}"
            ) from exc

    def generate_presigned_url(
        self,
        bucket_name: str,
        object_name: str,
        expires_seconds: int = 3600,
    ) -> str:
        """Generate a presigned URL for temporary object access.
        
        Args:
            bucket_name: Bucket name
            object_name: Object name
            expires_seconds: URL expiry time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL string
        """
        try:
            from datetime import timedelta
            
            url = self.client.presigned_get_object(
                bucket_name=bucket_name,
                object_name=object_name,
                expires=timedelta(seconds=expires_seconds),
            )
            return url
        except S3Error as exc:
            raise RuntimeError(
                f"Failed to generate presigned URL for {bucket_name}/{object_name}: {exc}"
            ) from exc

    def health_check(self) -> bool:
        """Check if MinIO is accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try to list buckets as a health check
            list(self.client.list_buckets())
            return True
        except Exception:
            return False


# Singleton instance
_minio_client: Optional[MinIOClient] = None


@lru_cache
def get_minio_client() -> MinIOClient:
    """Get or create singleton MinIO client instance.
    
    Reads configuration from environment variables:
    - MINIO_ENDPOINT: MinIO server endpoint (default: "minio:9000")
    - MINIO_ACCESS_KEY: Access key ID (default: "minioadmin")
    - MINIO_SECRET_KEY: Secret access key (default: "minioadmin")
    - MINIO_SECURE: Use HTTPS (default: "false")
    - MINIO_REGION: S3 region (default: "us-east-1")
    
    Returns:
        MinIOClient instance
    """
    global _minio_client
    
    if _minio_client is None:
        endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
        access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        region = os.getenv("MINIO_REGION", "us-east-1")
        
        _minio_client = MinIOClient(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region=region,
        )
    
    return _minio_client
