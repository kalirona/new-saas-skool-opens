from typing import List, Optional, Union
from uuid import uuid4
from datetime import datetime
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, Request

from src.db.users import PublicUser, AnonymousUser, APITokenUser
from src.db.notifications.notifications import (
    Notification,
    NotificationCreate,
    NotificationRead,
    NOTIFICATION_TYPES,
)
from src.security.rbac import authorization_verify_if_user_is_anon


async def create_notification(
    notification_object: NotificationCreate,
    db_session: AsyncSession,
) -> NotificationRead:
    notification = Notification(
        notification_type=notification_object.notification_type,
        title=notification_object.title,
        message=notification_object.message,
        is_read=False,
        user_id=notification_object.user_id,
        org_id=notification_object.org_id,
        actor_id=notification_object.actor_id,
        resource_uuid=notification_object.resource_uuid,
        parent_resource_uuid=notification_object.parent_resource_uuid,
        link=notification_object.link,
        notification_uuid=f"notif_{uuid4()}",
        creation_date=str(datetime.now()),
    )

    db_session.add(notification)
    await db_session.commit()
    await db_session.refresh(notification)

    return NotificationRead.model_validate(notification.model_dump())


async def create_notifications_batch(
    notification_objects: list[NotificationCreate],
    db_session: AsyncSession,
) -> None:
    for obj in notification_objects:
        notification = Notification(
            notification_type=obj.notification_type,
            title=obj.title,
            message=obj.message,
            is_read=False,
            user_id=obj.user_id,
            org_id=obj.org_id,
            actor_id=obj.actor_id,
            resource_uuid=obj.resource_uuid,
            parent_resource_uuid=obj.parent_resource_uuid,
            link=obj.link,
            notification_uuid=f"notif_{uuid4()}",
            creation_date=str(datetime.now()),
        )
        db_session.add(notification)
    await db_session.commit()


async def get_user_notifications(
    request: Request,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
    page: int = 1,
    limit: int = 20,
    unread_only: bool = False,
) -> tuple[List[NotificationRead], int]:
    await authorization_verify_if_user_is_anon(current_user.id)

    limit = min(limit, 50)
    offset = (page - 1) * limit

    statement = select(Notification).where(Notification.user_id == current_user.id)

    if unread_only:
        statement = statement.where(Notification.is_read == False)

    count_statement = select(func.count()).select_from(statement.subquery())
    total = (await db_session.execute(count_statement)).scalar() or 0

    statement = statement.order_by(Notification.creation_date.desc(), Notification.id.desc()).offset(offset).limit(limit)
    notifications = (await db_session.execute(statement)).scalars().all()

    return [NotificationRead.model_validate(n.model_dump()) for n in notifications], total


async def get_unread_count(
    request: Request,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> int:
    await authorization_verify_if_user_is_anon(current_user.id)

    statement = select(func.count(Notification.id)).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False,
    )
    count = (await db_session.execute(statement)).scalar() or 0
    return count


async def mark_as_read(
    request: Request,
    notification_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> NotificationRead:
    await authorization_verify_if_user_is_anon(current_user.id)

    statement = select(Notification).where(
        Notification.notification_uuid == notification_uuid,
        Notification.user_id == current_user.id,
    )
    notification = (await db_session.execute(statement)).scalars().first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db_session.add(notification)
    await db_session.commit()
    await db_session.refresh(notification)

    return NotificationRead.model_validate(notification.model_dump())


async def mark_all_as_read(
    request: Request,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> dict:
    await authorization_verify_if_user_is_anon(current_user.id)

    statement = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False,
    )
    notifications = (await db_session.execute(statement)).scalars().all()

    for n in notifications:
        n.is_read = True
        db_session.add(n)

    await db_session.commit()

    return {"detail": "All notifications marked as read"}
