"""Storage backend abstraction — local filesystem and S3-compatible (AWS, MinIO, R2)."""

from src.core.storage.backend import (
    StorageBackend,
    StorageObject,
    StorageExistsResult,
)
from src.core.storage.factory import get_storage_backend, get_storage_config
from src.core.storage.local import LocalStorage
from src.core.storage.s3 import S3Storage

__all__ = [
    "StorageBackend",
    "StorageObject",
    "StorageExistsResult",
    "LocalStorage",
    "S3Storage",
    "get_storage_backend",
    "get_storage_config",
]
