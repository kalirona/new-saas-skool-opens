from typing import List
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.events.database import get_db_session
from src.db.users import PublicUser
from src.db.resources.tags import TagRead
from src.security.auth import get_current_user
from src.services.resources.tags import (
    create_tag,
    get_tags_by_org,
    delete_tag,
    add_tag_to_resource,
    remove_tag_from_resource,
    get_tags_for_resource,
)


router = APIRouter()


class TagCreateRequest(BaseModel):
    name: str
    color: str | None = None


@router.get(
    "/resources/org/{org_id}/tags",
    response_model=List[TagRead],
    summary="List tags in an organization",
)
async def api_get_tags_by_org(
    request: Request,
    org_id: int,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> List[TagRead]:
    return await get_tags_by_org(request, org_id, current_user, db_session)


@router.post(
    "/resources/org/{org_id}/tags",
    response_model=TagRead,
    summary="Create a tag",
)
async def api_create_tag(
    request: Request,
    org_id: int,
    tag_data: TagCreateRequest,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> TagRead:
    from src.db.resources.tags import TagCreate

    tc = TagCreate(name=tag_data.name, color=tag_data.color, org_id=org_id)
    return await create_tag(request, org_id, tc, current_user, db_session)


@router.delete(
    "/resources/tags/{tag_uuid}",
    summary="Delete a tag",
)
async def api_delete_tag(
    request: Request,
    tag_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await delete_tag(request, tag_uuid, current_user, db_session)


@router.get(
    "/resources/{resource_uuid}/tags",
    response_model=List[TagRead],
    summary="List tags for a resource",
)
async def api_get_tags_for_resource(
    request: Request,
    resource_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> List[TagRead]:
    return await get_tags_for_resource(request, resource_uuid, current_user, db_session)


@router.post(
    "/resources/{resource_uuid}/tags/{tag_uuid}",
    summary="Add a tag to a resource",
)
async def api_add_tag_to_resource(
    request: Request,
    resource_uuid: str,
    tag_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await add_tag_to_resource(request, resource_uuid, tag_uuid, current_user, db_session)


@router.delete(
    "/resources/{resource_uuid}/tags/{tag_uuid}",
    summary="Remove a tag from a resource",
)
async def api_remove_tag_from_resource(
    request: Request,
    resource_uuid: str,
    tag_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await remove_tag_from_resource(request, resource_uuid, tag_uuid, current_user, db_session)
