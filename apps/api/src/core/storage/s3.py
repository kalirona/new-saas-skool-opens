"""S3-compatible storage backend (AWS S3, MinIO, Cloudflare R2)."""

import logging
import os
import threading
from typing import Optional

import boto3
import botocore.config
from botocore.exceptions import ClientError

from src.core.storage.backend import StorageBackend, StorageExistsResult, StorageObject

logger = logging.getLogger(__name__)


class S3Storage(StorageBackend):
    def __init__(
        self,
        bucket_name: str = "learnhouse-media",
        endpoint_url: Optional[str] = None,
        region_name: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        connect_timeout: int = 10,
        read_timeout: int = 60,
        max_retries: int = 2,
    ):
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url
        self._client = None
        self._lock = threading.Lock()
        self._client_kwargs = {
            "service_name": "s3",
            "config": botocore.config.Config(
                connect_timeout=connect_timeout,
                read_timeout=read_timeout,
                retries={"max_attempts": max_retries},
            ),
        }
        if endpoint_url:
            self._client_kwargs["endpoint_url"] = endpoint_url
        if region_name:
            self._client_kwargs["region_name"] = region_name
        if access_key_id and secret_access_key:
            self._client_kwargs["aws_access_key_id"] = access_key_id
            self._client_kwargs["aws_secret_access_key"] = secret_access_key

    def _get_client(self):
        if self._client is not None:
            return self._client
        with self._lock:
            if self._client is not None:
                return self._client
            self._client = boto3.client(**self._client_kwargs)
        return self._client

    async def write(self, path: str, data: bytes, content_type: str) -> str:
        import mimetypes
        mime = content_type or mimetypes.guess_type(path)[0] or "application/octet-stream"
        client = self._get_client()
        try:
            client.put_object(Bucket=self.bucket_name, Key=path, Body=data, ContentType=mime)
            return path
        except ClientError as e:
            logger.error("S3 write failed for %s: %s", path, e)
            raise

    async def read(self, path: str) -> Optional[StorageObject]:
        client = self._get_client()
        try:
            resp = client.get_object(Bucket=self.bucket_name, Key=path)
            data = resp["Body"].read()
            ct = resp.get("ContentType", "application/octet-stream")
            return StorageObject(data=data, content_type=ct, content_length=len(data))
        except ClientError as e:
            if e.response["Error"]["Code"] in ("NoSuchKey", "NotFound"):
                return None
            logger.error("S3 read failed for %s: %s", path, e)
            raise

    async def exists(self, path: str) -> StorageExistsResult:
        client = self._get_client()
        try:
            resp = client.head_object(Bucket=self.bucket_name, Key=path)
            ct = resp.get("ContentType", "application/octet-stream")
            return StorageExistsResult(exists=True, content_type=ct, content_length=resp.get("ContentLength"))
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
                return StorageExistsResult(exists=False)
            logger.error("S3 exists check failed for %s: %s", path, e)
            raise

    async def delete(self, path: str) -> bool:
        client = self._get_client()
        try:
            client.delete_object(Bucket=self.bucket_name, Key=path)
            return True
        except ClientError as e:
            logger.error("S3 delete failed for %s: %s", path, e)
            return False

    async def list(self, prefix: str) -> list[str]:
        client = self._get_client()
        keys = []
        try:
            paginator = client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                for obj in page.get("Contents", []):
                    keys.append(obj["Key"])
        except ClientError as e:
            logger.error("S3 list failed for prefix %s: %s", prefix, e)
        return keys

    async def get_signed_url(self, path: str, expires_in: int = 3600) -> Optional[str]:
        client = self._get_client()
        try:
            url = client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": path},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            logger.error("S3 signed URL generation failed for %s: %s", path, e)
            return None

    async def upload_from_local(self, local_path: str, remote_path: str) -> str:
        client = self._get_client()
        import mimetypes
        content_type = mimetypes.guess_type(local_path)[0] or "application/octet-stream"
        try:
            client.upload_file(local_path, self.bucket_name, remote_path, ExtraArgs={"ContentType": content_type})
            return remote_path
        except ClientError as e:
            logger.error("S3 upload from local failed %s -> %s: %s", local_path, remote_path, e)
            raise
