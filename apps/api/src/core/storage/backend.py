"""Abstract storage backend interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class StorageObject:
    data: bytes
    content_type: str
    content_length: int


@dataclass
class StorageExistsResult:
    exists: bool
    content_type: Optional[str] = None
    content_length: Optional[int] = None


class StorageBackend(ABC):
    @abstractmethod
    async def write(self, path: str, data: bytes, content_type: str) -> str:
        ...

    @abstractmethod
    async def read(self, path: str) -> Optional[StorageObject]:
        ...

    @abstractmethod
    async def exists(self, path: str) -> StorageExistsResult:
        ...

    @abstractmethod
    async def delete(self, path: str) -> bool:
        ...

    @abstractmethod
    async def list(self, prefix: str) -> list[str]:
        ...

    @abstractmethod
    async def get_signed_url(self, path: str, expires_in: int = 3600) -> Optional[str]:
        ...

    @abstractmethod
    async def upload_from_local(self, local_path: str, remote_path: str) -> str:
        ...
