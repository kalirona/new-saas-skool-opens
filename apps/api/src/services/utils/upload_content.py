import logging
from typing import Literal, Optional

from fastapi import HTTPException, UploadFile

from src.core.storage import get_storage_backend
from src.security.file_validation import validate_upload, validate_upload_streaming

logger = logging.getLogger(__name__)

# Files larger than this use the streaming write path to avoid loading into RAM
_STREAMING_THRESHOLD = 100 * 1024 * 1024  # 100 MB


async def upload_file(
    file: UploadFile,
    directory: str,
    type_of_dir: Literal["orgs", "users"],
    uuid: str,
    allowed_types: list[str],
    filename_prefix: str,
    max_size: Optional[int] = None,
) -> str:
    from uuid import uuid4
    from src.security.file_validation import get_safe_filename

    filename = get_safe_filename(
        file.filename, f"{uuid4()}_{filename_prefix}", content_type=None
    )

    # Peek at size via seek/tell to decide streaming vs memory path
    file.file.seek(0, 2)  # SEEK_END
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > _STREAMING_THRESHOLD:
        await _upload_file_streaming(
            file, directory, type_of_dir, uuid, filename, allowed_types, max_size,
        )
    else:
        _content_type, content = validate_upload(file, allowed_types, max_size)
        await upload_content(
            directory=directory,
            type_of_dir=type_of_dir,
            uuid=uuid,
            file_binary=content,
            file_and_format=filename,
            content_type=_content_type,
            allowed_formats=None,
        )

    return filename


async def _upload_file_streaming(
    file: UploadFile,
    directory: str,
    type_of_dir: Literal["orgs", "users"],
    uuid: str,
    filename: str,
    allowed_types: list[str],
    max_size: Optional[int] = None,
) -> str:
    """Upload a large file using the streaming validate+write path."""
    content_type, content_length = validate_upload_streaming(file, allowed_types, max_size)
    path = f"{type_of_dir}/{uuid}/{directory}/{filename}"
    backend = get_storage_backend()
    await backend.write_stream(path, file.file, content_type, content_length)
    return content_type


async def upload_content(
    directory: str,
    type_of_dir: Literal["orgs", "users"],
    uuid: str,
    file_binary: bytes,
    file_and_format: str,
    content_type: str = "application/octet-stream",
    allowed_formats: Optional[list[str]] = None,
):
    file_format = file_and_format.split(".")[-1].strip().lower()

    if allowed_formats and file_format not in allowed_formats:
        raise HTTPException(
            status_code=400,
            detail=f"File format {file_format} not allowed",
        )

    path = f"{type_of_dir}/{uuid}/{directory}/{file_and_format}"
    backend = get_storage_backend()
    await backend.write(path, file_binary, content_type)
