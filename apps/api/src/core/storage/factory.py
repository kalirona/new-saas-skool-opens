"""Storage backend factory — returns the configured backend."""

from config.config import get_learnhouse_config
from src.core.storage.backend import StorageBackend
from src.core.storage.local import LocalStorage
from src.core.storage.s3 import S3Storage

_backend: StorageBackend | None = None


def get_storage_config():
    return get_learnhouse_config().hosting_config.content_delivery


def get_storage_backend() -> StorageBackend:
    global _backend
    if _backend is not None:
        return _backend

    cfg = get_storage_config()
    if cfg.type == "s3api":
        s3 = cfg.s3api
        _backend = S3Storage(
            bucket_name=s3.bucket_name or "learnhouse-media",
            endpoint_url=s3.endpoint_url,
            region_name=s3.region_name,
            access_key_id=s3.access_key_id,
            secret_access_key=s3.secret_access_key,
        )
    else:
        _backend = LocalStorage(root="content")

    return _backend


def reset_storage_backend() -> None:
    global _backend
    _backend = None
