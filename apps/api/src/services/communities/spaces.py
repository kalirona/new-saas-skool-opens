from typing import List, Optional, Union
from uuid import uuid4
from datetime import datetime
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, Request

from src.db.users import PublicUser, AnonymousUser, APITokenUser
from src.db.communities.spaces import Space, SpaceCreate, SpaceUpdate, SpaceRead
from src.db.communities.communities import Community
from src.db.communities.community_members import CommunityMember
from src.security.rbac import (
    check_resource_access,
    AccessAction,
    authorization_verify_if_user_is_anon,
    authorization_verify_based_on_org_admin_status,
)
from src.core.cache import cache_get, cache_set, cache_delete_pattern


async def _user_is_community_member(
    user_id: int, community_id: int, db_session: AsyncSession
) -> bool:
    """Check if a user is an active member of a community."""
    cache_key = f"member_check:{user_id}:{community_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    statement = select(CommunityMember).where(
        CommunityMember.community_id == community_id,
        CommunityMember.user_id == user_id,
        CommunityMember.status == "active",
    )
    member = (await db_session.execute(statement)).scalars().first()
    result = member is not None
    cache_set(cache_key, result, ttl=60)
    return result


async def _user_is_org_admin(
    request: Request,
    org_id: int,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
) -> bool:
    """Check if a user is an org admin or maintainer."""
    try:
        return await authorization_verify_based_on_org_admin_status(
            request, current_user.id, org_id
        )
    except HTTPException:
        return False


def _can_access_space(
    visibility: str,
    is_member: bool,
    is_admin: bool,
) -> bool:
    """Determine if a user can access a space based on its visibility setting."""
    if visibility == "public":
        return True
    if visibility == "members":
        return is_member or is_admin
    if visibility == "moderators":
        return is_admin
    return False


async def create_space(
    request: Request,
    community_uuid: str,
    space_data: SpaceCreate,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> SpaceRead:
    """Create a new space in a community."""
    await authorization_verify_if_user_is_anon(current_user.id)

    await check_resource_access(
        request, db_session, current_user, community_uuid, AccessAction.UPDATE
    )

    community_statement = select(Community).where(
        Community.community_uuid == community_uuid
    )
    community = (await db_session.execute(community_statement)).scalars().first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    space = Space(
        name=space_data.name,
        icon=space_data.icon,
        description=space_data.description,
        ordering=space_data.ordering,
        visibility=space_data.visibility,
        community_id=community.id,
        org_id=community.org_id,
        space_uuid=f"space_{uuid4()}",
        creation_date=str(datetime.now()),
        update_date=str(datetime.now()),
    )

    db_session.add(space)
    await db_session.commit()
    await db_session.refresh(space)

    cache_delete_pattern(f"spaces:{space.community_id}")

    return SpaceRead.model_validate(space.model_dump())


async def get_spaces_by_community(
    request: Request,
    community_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> List[SpaceRead]:
    """Get all spaces for a community, filtered by visibility for the current user."""
    await check_resource_access(
        request, db_session, current_user, community_uuid, AccessAction.READ
    )

    community_statement = select(Community).where(
        Community.community_uuid == community_uuid
    )
    community = (await db_session.execute(community_statement)).scalars().first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    is_admin = await _user_is_org_admin(
        request, community.org_id, current_user
    ) if not isinstance(current_user, AnonymousUser) else False
    is_member = await _user_is_community_member(
        current_user.id, community.id, db_session
    ) if not isinstance(current_user, AnonymousUser) else False

    raw_spaces = cache_get(f"spaces:{community.id}")
    if raw_spaces is None:
        statement = (
            select(Space)
            .where(Space.community_id == community.id)
            .order_by(Space.ordering)
        )
        spaces = (await db_session.execute(statement)).scalars().all()
        raw_spaces = [s.model_dump() for s in spaces]
        cache_set(f"spaces:{community.id}", raw_spaces, ttl=120)

    filtered = [
        SpaceRead.model_validate(s)
        for s in raw_spaces
        if _can_access_space(s["visibility"], is_member, is_admin)
    ]

    return filtered


async def get_space(
    request: Request,
    space_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> SpaceRead:
    """Get a single space by UUID, respecting visibility."""
    space = cache_get(f"space:{space_uuid}")
    if space is not None:
        return SpaceRead(**space)

    statement = select(Space).where(Space.space_uuid == space_uuid)
    space = (await db_session.execute(statement)).scalars().first()

    if not space:
        raise HTTPException(status_code=404, detail="Space not found")

    community_statement = select(Community).where(Community.id == space.community_id)
    community = (await db_session.execute(community_statement)).scalars().first()
    if community:
        await check_resource_access(
            request, db_session, current_user, community.community_uuid, AccessAction.READ
        )

        is_admin = await _user_is_org_admin(
            request, community.org_id, current_user
        ) if not isinstance(current_user, AnonymousUser) else False
        is_member = await _user_is_community_member(
            current_user.id, community.id, db_session
        ) if not isinstance(current_user, AnonymousUser) else False

        if not _can_access_space(space.visibility, is_member, is_admin):
            raise HTTPException(status_code=403, detail="You do not have access to this space")

    result = SpaceRead.model_validate(space.model_dump())
    cache_set(f"space:{space_uuid}", result.model_dump(), ttl=120)
    return result


async def update_space(
    request: Request,
    space_uuid: str,
    space_data: SpaceUpdate,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> SpaceRead:
    """Update a space."""
    await authorization_verify_if_user_is_anon(current_user.id)

    statement = select(Space).where(Space.space_uuid == space_uuid)
    space = (await db_session.execute(statement)).scalars().first()

    if not space:
        raise HTTPException(status_code=404, detail="Space not found")

    community_statement = select(Community).where(Community.id == space.community_id)
    community = (await db_session.execute(community_statement)).scalars().first()
    community_uuid = community.community_uuid if community else None

    if community_uuid:
        await check_resource_access(
            request, db_session, current_user, community_uuid, AccessAction.UPDATE
        )

    if space_data.name is not None:
        space.name = space_data.name
    if space_data.icon is not None:
        space.icon = space_data.icon
    if space_data.description is not None:
        space.description = space_data.description
    if space_data.ordering is not None:
        space.ordering = space_data.ordering
    if space_data.visibility is not None:
        space.visibility = space_data.visibility

    space.update_date = str(datetime.now())

    db_session.add(space)
    await db_session.commit()
    await db_session.refresh(space)

    cache_delete_pattern(f"space:{space_uuid}")
    cache_delete_pattern(f"spaces:{space.community_id}")

    return SpaceRead.model_validate(space.model_dump())


async def delete_space(
    request: Request,
    space_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> dict:
    """Delete a space. Sets space_id to null on associated discussions."""
    await authorization_verify_if_user_is_anon(current_user.id)

    statement = select(Space).where(Space.space_uuid == space_uuid)
    space = (await db_session.execute(statement)).scalars().first()

    if not space:
        raise HTTPException(status_code=404, detail="Space not found")

    community_statement = select(Community).where(Community.id == space.community_id)
    community = (await db_session.execute(community_statement)).scalars().first()
    community_uuid = community.community_uuid if community else None

    if community_uuid:
        await check_resource_access(
            request, db_session, current_user, community_uuid, AccessAction.DELETE
        )

    await db_session.delete(space)
    await db_session.commit()

    cache_delete_pattern(f"space:{space_uuid}")
    cache_delete_pattern(f"spaces:{space.community_id}")

    return {"detail": "Space deleted"}


async def reorder_spaces(
    request: Request,
    community_uuid: str,
    space_uuids: List[str],
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> List[SpaceRead]:
    """Batch reorder spaces by providing space UUIDs in the desired order."""
    await authorization_verify_if_user_is_anon(current_user.id)

    await check_resource_access(
        request, db_session, current_user, community_uuid, AccessAction.UPDATE
    )

    community_statement = select(Community).where(
        Community.community_uuid == community_uuid
    )
    community = (await db_session.execute(community_statement)).scalars().first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    updated = []
    spaces = (await db_session.execute(
        select(Space).where(
            Space.space_uuid.in_(space_uuids),
            Space.community_id == community.id,
        )
    )).scalars().all()
    space_map = {s.space_uuid: s for s in spaces}
    for i, suuid in enumerate(space_uuids):
        space = space_map.get(suuid)
        if not space:
            raise HTTPException(
                status_code=404,
                detail=f"Space {suuid} not found in this community",
            )
        space.ordering = i
        space.update_date = str(datetime.now())
        db_session.add(space)
        updated.append(space)

    await db_session.commit()

    cache_delete_pattern(f"spaces:{community.id}")

    return [SpaceRead.model_validate(s.model_dump()) for s in sorted(updated, key=lambda x: x.ordering)]
