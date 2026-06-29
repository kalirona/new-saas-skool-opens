from typing import List, Optional, Union
from uuid import uuid4
from datetime import datetime
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, Request

from src.db.users import PublicUser, AnonymousUser, APITokenUser
from src.db.resources.tags import Tag, TagCreate, TagRead, ResourceTag
from src.db.resources.resources import Resource
from src.security.rbac import (
    authorization_verify_if_user_is_anon,
)


async def create_tag(
    request: Request,
    org_id: int,
    tag_data: TagCreate,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> TagRead:
    await authorization_verify_if_user_is_anon(current_user.id)

    existing = await db_session.execute(
        select(Tag).where(Tag.org_id == org_id, Tag.name == tag_data.name)
    )
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Tag with this name already exists")

    tag = Tag(
        name=tag_data.name,
        color=tag_data.color,
        org_id=org_id,
        tag_uuid=f"tag_{uuid4()}",
        creation_date=str(datetime.now()),
    )

    db_session.add(tag)
    await db_session.commit()
    await db_session.refresh(tag)

    return TagRead.model_validate(tag.model_dump())


async def get_tags_by_org(
    request: Request,
    org_id: int,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> List[TagRead]:
    statement = select(Tag).where(Tag.org_id == org_id).order_by(Tag.name)
    tags = (await db_session.execute(statement)).scalars().all()
    return [TagRead.model_validate(t.model_dump()) for t in tags]


async def delete_tag(
    request: Request,
    tag_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> dict:
    await authorization_verify_if_user_is_anon(current_user.id)

    statement = select(Tag).where(Tag.tag_uuid == tag_uuid)
    tag = (await db_session.execute(statement)).scalars().first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    await db_session.delete(tag)
    await db_session.commit()

    return {"detail": "Tag deleted"}


async def add_tag_to_resource(
    request: Request,
    resource_uuid: str,
    tag_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> dict:
    await authorization_verify_if_user_is_anon(current_user.id)

    resource = (
        await db_session.execute(
            select(Resource).where(Resource.resource_uuid == resource_uuid)
        )
    ).scalars().first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    tag = (
        await db_session.execute(select(Tag).where(Tag.tag_uuid == tag_uuid))
    ).scalars().first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    existing = await db_session.execute(
        select(ResourceTag).where(
            ResourceTag.resource_id == resource.id,
            ResourceTag.tag_id == tag.id,
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Resource already has this tag")

    rt = ResourceTag(resource_id=resource.id, tag_id=tag.id)
    db_session.add(rt)
    await db_session.commit()

    return {"detail": "Tag added to resource"}


async def remove_tag_from_resource(
    request: Request,
    resource_uuid: str,
    tag_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> dict:
    await authorization_verify_if_user_is_anon(current_user.id)

    resource = (
        await db_session.execute(
            select(Resource).where(Resource.resource_uuid == resource_uuid)
        )
    ).scalars().first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    tag = (
        await db_session.execute(select(Tag).where(Tag.tag_uuid == tag_uuid))
    ).scalars().first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    rt = (
        await db_session.execute(
            select(ResourceTag).where(
                ResourceTag.resource_id == resource.id,
                ResourceTag.tag_id == tag.id,
            )
        )
    ).scalars().first()
    if not rt:
        raise HTTPException(status_code=404, detail="Resource does not have this tag")

    await db_session.delete(rt)
    await db_session.commit()

    return {"detail": "Tag removed from resource"}


async def get_tags_for_resource(
    request: Request,
    resource_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> List[TagRead]:
    resource = (
        await db_session.execute(
            select(Resource).where(Resource.resource_uuid == resource_uuid)
        )
    ).scalars().first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    rts = (
        await db_session.execute(
            select(ResourceTag).where(ResourceTag.resource_id == resource.id)
        )
    ).scalars().all()

    if not rts:
        return []

    tag_ids = [rt.tag_id for rt in rts]
    tags = (
        await db_session.execute(select(Tag).where(Tag.id.in_(tag_ids)))  # type: ignore
    ).scalars().all()

    return [TagRead.model_validate(t.model_dump()) for t in tags]
