"""
Local Content Files Router

Serves static content files from the local filesystem with access control.
For S3/R2/MinIO deployments, see content_files.py which uses signed URLs.

SECURITY:
- Activity content for non-public courses requires auth
- Course-level metadata (thumbnails) is always public
- Org-level content (logos, branding) is always public
- Podcast episode content for non-public podcasts requires auth
"""

import os
from pathlib import Path
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.events.database import get_db_session
from src.db.courses.courses import Course
from src.db.podcasts.podcasts import Podcast
from src.db.users import AnonymousUser, PublicUser, APITokenUser
from src.db.user_organizations import UserOrganization
from src.security.auth import get_current_user

router = APIRouter()

CONTENT_DIR = Path("content")


def _validate_content_path(file_path: str) -> Path | None:
    decoded = unquote(unquote(file_path))
    if '..' in decoded or decoded.startswith('/') or '\x00' in decoded:
        return None
    normalized = decoded.replace('\\', '/')
    if '..' in normalized:
        return None

    try:
        base_real = os.path.realpath(str(CONTENT_DIR))
        full_real = os.path.realpath(os.path.join(base_real, normalized))
        if os.path.commonpath([base_real, full_real]) != base_real:
            return None
        return Path(full_real)
    except (ValueError, OSError):
        return None


async def _check_content_access(
    file_path: str,
    current_user: PublicUser | AnonymousUser | APITokenUser,
    db_session: AsyncSession,
) -> None:
    parts = file_path.split('/')

    if (
        len(parts) >= 6
        and parts[0] == 'orgs'
        and parts[2] == 'courses'
        and parts[4] == 'activities'
    ):
        course_uuid = parts[3]
        course = (await db_session.execute(
            select(Course).where(Course.course_uuid == course_uuid)
        )).scalars().first()
        if not course:
            raise HTTPException(status_code=403, detail="Access denied")
        if course.public:
            return
        if isinstance(current_user, AnonymousUser):
            raise HTTPException(status_code=401, detail="Authentication required")
        if isinstance(current_user, APITokenUser):
            if current_user.org_id != course.org_id:
                raise HTTPException(status_code=403, detail="Access denied")
            return
        membership = (await db_session.execute(
            select(UserOrganization).where(
                UserOrganization.user_id == current_user.id,
                UserOrganization.org_id == course.org_id,
            )
        )).scalars().first()
        if not membership:
            raise HTTPException(status_code=403, detail="Access denied")
        return

    if (
        len(parts) >= 6
        and parts[0] == 'orgs'
        and parts[2] == 'podcasts'
        and parts[4] == 'episodes'
    ):
        podcast_uuid = parts[3]
        podcast = (await db_session.execute(
            select(Podcast).where(Podcast.podcast_uuid == podcast_uuid)
        )).scalars().first()
        if not podcast:
            raise HTTPException(status_code=403, detail="Access denied")
        if podcast.public:
            return
        if isinstance(current_user, AnonymousUser):
            raise HTTPException(status_code=401, detail="Authentication required")
        if isinstance(current_user, APITokenUser):
            if current_user.org_id != podcast.org_id:
                raise HTTPException(status_code=403, detail="Access denied")
            return
        membership = (await db_session.execute(
            select(UserOrganization).where(
                UserOrganization.user_id == current_user.id,
                UserOrganization.org_id == podcast.org_id,
            )
        )).scalars().first()
        if not membership:
            raise HTTPException(status_code=403, detail="Access denied")
        return

    if len(parts) >= 2 and parts[0] in ('orgs', 'users'):
        return

    if isinstance(current_user, AnonymousUser):
        raise HTTPException(status_code=401, detail="Authentication required")
    raise HTTPException(status_code=403, detail="Access denied")


@router.get(
    "/content/{file_path:path}",
    summary="Serve a content file",
    description="Streams a content file from the local filesystem with access control.",
)
async def serve_content_file(
    request: Request,
    file_path: str,
    current_user: PublicUser | AnonymousUser | APITokenUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    file_path_resolved = _validate_content_path(file_path)
    if file_path_resolved is None:
        raise HTTPException(status_code=400, detail="Invalid path")

    await _check_content_access(file_path, current_user, db_session)

    if not file_path_resolved.exists() or not file_path_resolved.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(file_path_resolved),
        headers={
            "Cache-Control": "public, max-age=86400",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.head(
    "/content/{file_path:path}",
    summary="Get content file metadata",
    description="Returns metadata for a content file without the body for local storage.",
)
async def head_content_file(
    file_path: str,
    current_user: PublicUser | AnonymousUser | APITokenUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    file_path_resolved = _validate_content_path(file_path)
    if file_path_resolved is None:
        raise HTTPException(status_code=400, detail="Invalid path")

    await _check_content_access(file_path, current_user, db_session)

    if not file_path_resolved.exists() or not file_path_resolved.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    stat = file_path_resolved.stat()
    import mimetypes
    mime, _ = mimetypes.guess_type(str(file_path_resolved))

    return FileResponse(
        path=str(file_path_resolved),
        status_code=200,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(stat.st_size),
            "Content-Type": mime or "application/octet-stream",
            "Cache-Control": "public, max-age=86400",
        },
    )
