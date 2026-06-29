from fastapi import APIRouter, Depends, Request, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.events.database import get_db_session
from src.db.users import PublicUser
from src.db.notifications.notifications import NotificationRead
from src.security.auth import get_current_user
from src.services.notifications.notifications import (
    get_user_notifications,
    get_unread_count,
    mark_as_read,
    mark_all_as_read,
)


router = APIRouter()


@router.get(
    "/notifications",
    response_model=dict,
    summary="List notifications for the current user",
)
async def api_get_notifications(
    request: Request,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
    unread_only: bool = Query(default=False),
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    notifications, total = await get_user_notifications(
        request, current_user, db_session,
        page=page, limit=limit, unread_only=unread_only,
    )
    return {"notifications": notifications, "total": total, "page": page, "limit": limit}


@router.get(
    "/notifications/unread-count",
    summary="Get unread notification count",
)
async def api_get_unread_count(
    request: Request,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    count = await get_unread_count(request, current_user, db_session)
    return {"count": count}


@router.put(
    "/notifications/{notification_uuid}/read",
    response_model=NotificationRead,
    summary="Mark a single notification as read",
)
async def api_mark_as_read(
    request: Request,
    notification_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> NotificationRead:
    return await mark_as_read(request, notification_uuid, current_user, db_session)


@router.put(
    "/notifications/read-all",
    summary="Mark all notifications as read",
)
async def api_mark_all_as_read(
    request: Request,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await mark_all_as_read(request, current_user, db_session)
