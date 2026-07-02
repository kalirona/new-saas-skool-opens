"""Abstract storage backend interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import BinaryIO, Optional


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

    async def write_stream(
        self,
        path: str,
        stream: BinaryIO,
        content_type: str,
        content_length: int,
        chunk_size: int = 8 * 1024 * 1024,
    ) -> str:
        """Stream a file-like object to storage in chunks.
        
        Default implementation reads chunks and calls ``write()``.
        Subclasses may override for direct streaming (e.g. S3 ``upload_fileobj``).
        """
        chunks = []
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            chunks.append(chunk)
        return await self.write(path, b"".join(chunks), content_type)

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
