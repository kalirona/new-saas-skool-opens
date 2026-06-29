"""
Content Files Router

Serves static content files from S3/R2/MinIO storage via signed URLs.
After access control, redirects to a time-limited presigned URL so files
stream directly from the object store without proxying through the API.

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
from fastapi.responses import RedirectResponse, Response
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.events.database import get_db_session
from src.core.storage import get_storage_backend
from src.db.courses.courses import Course
from src.db.podcasts.podcasts import Podcast
from src.db.users import AnonymousUser, PublicUser, APITokenUser
from src.db.user_organizations import UserOrganization
from src.security.auth import get_current_user

router = APIRouter()


def _validate_content_path(file_path: str) -> str | None:
    decoded = unquote(unquote(file_path))
    if '..' in decoded or decoded.startswith('/') or '\x00' in decoded:
        return None
    normalized = decoded.replace('\\', '/')
    if '..' in normalized:
        return None
    base_real = os.path.realpath(str(Path("content")))
    full_real = os.path.realpath(os.path.join(base_real, normalized))
    if not full_real.startswith(base_real + os.sep):
        return None
    return os.path.relpath(full_real, base_real).replace("\\", "/")


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
    summary="Serve a content file via signed URL",
    description="After access control, redirects to a time-limited presigned URL for direct S3/R2/MinIO access.",
    responses={
        302: {"description": "Redirect to signed URL"},
        400: {"description": "Invalid file path"},
        401: {"description": "Authentication required"},
        403: {"description": "Access denied"},
        404: {"description": "File not found"},
    },
)
async def serve_content_file(
    request: Request,
    file_path: str,
    current_user: PublicUser | AnonymousUser | APITokenUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    safe_path = _validate_content_path(file_path)
    if safe_path is None:
        raise HTTPException(status_code=400, detail="Invalid path")

    await _check_content_access(safe_path, current_user, db_session)

    backend = get_storage_backend()
    s3_key = f"content/{safe_path}"
    signed_url = await backend.get_signed_url(s3_key, expires_in=3600)

    if signed_url is None:
        raise HTTPException(status_code=500, detail="Failed to generate signed URL")

    return RedirectResponse(url=signed_url, status_code=302)


@router.head(
    "/content/{file_path:path}",
    summary="Get content file metadata",
    description="Checks existence and returns metadata headers for a content file.",
)
async def head_content_file(
    file_path: str,
    current_user: PublicUser | AnonymousUser | APITokenUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    safe_path = _validate_content_path(file_path)
    if safe_path is None:
        raise HTTPException(status_code=400, detail="Invalid path")

    await _check_content_access(safe_path, current_user, db_session)

    backend = get_storage_backend()
    s3_key = f"content/{safe_path}"
    result = await backend.exists(s3_key)

    if not result.exists:
        raise HTTPException(status_code=404, detail="File not found")

    return Response(
        status_code=200,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(result.content_length or 0),
            "Content-Type": result.content_type or "application/octet-stream",
            "Cache-Control": "public, max-age=86400",
        },
    )
