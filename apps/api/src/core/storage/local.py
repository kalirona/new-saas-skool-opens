"""Local filesystem storage backend."""

import logging
import os
from typing import Optional

from src.core.storage.backend import StorageBackend, StorageExistsResult, StorageObject

logger = logging.getLogger(__name__)


class LocalStorage(StorageBackend):
    def __init__(self, root: str = "content"):
        self._root = os.path.realpath(root)
        os.makedirs(self._root, exist_ok=True)

    def _resolve(self, path: str) -> Optional[str]:
        safe = path.replace("\\", "/")
        if safe.startswith("/") or os.path.isabs(safe):
            return None
        if ".." in safe.split("/"):
            return None
        resolved = os.path.realpath(os.path.join(self._root, safe))
        if os.path.commonpath([self._root, resolved]) != self._root:
            return None
        return resolved

    async def write(self, path: str, data: bytes, content_type: str) -> str:
        resolved = self._resolve(path)
        if resolved is None:
            raise ValueError(f"Invalid path: {path}")
        os.makedirs(os.path.dirname(resolved), exist_ok=True)
        with open(resolved, "wb") as f:
            f.write(data)
        return path

    async def read(self, path: str) -> Optional[StorageObject]:
        resolved = self._resolve(path)
        if resolved is None or not os.path.isfile(resolved):
            return None
        import mimetypes
        mime, _ = mimetypes.guess_type(resolved)
        with open(resolved, "rb") as f:
            data = f.read()
        return StorageObject(data=data, content_type=mime or "application/octet-stream", content_length=len(data))

    async def exists(self, path: str) -> StorageExistsResult:
        resolved = self._resolve(path)
        if resolved is None or not os.path.isfile(resolved):
            return StorageExistsResult(exists=False)
        import mimetypes
        mime, _ = mimetypes.guess_type(resolved)
        stat = os.stat(resolved)
        return StorageExistsResult(exists=True, content_type=mime, content_length=stat.st_size)

    async def delete(self, path: str) -> bool:
        resolved = self._resolve(path)
        if resolved is None or not os.path.isfile(resolved):
            return False
        os.remove(resolved)
        return True

    async def list(self, prefix: str) -> list[str]:
        resolved = self._resolve(prefix)
        if resolved is None or not os.path.isdir(resolved):
            return []
        result = []
        for root, _dirs, files in os.walk(resolved):
            for name in files:
                full = os.path.join(root, name)
                rel = os.path.relpath(full, self._root)
                result.append(rel.replace("\\", "/"))
        return result

    async def get_signed_url(self, path: str, expires_in: int = 3600) -> Optional[str]:
        return None

    async def upload_from_local(self, local_path: str, remote_path: str) -> str:
        resolved = self._resolve(remote_path)
        if resolved is None:
            raise ValueError(f"Invalid remote path: {remote_path}")
        os.makedirs(os.path.dirname(resolved), exist_ok=True)
        import shutil
        shutil.copy2(local_path, resolved)
        return remote_path
