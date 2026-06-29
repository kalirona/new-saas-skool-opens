from typing import List
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.events.database import get_db_session
from src.db.users import PublicUser
from src.db.communities.spaces import SpaceRead, SpaceUpdate
from src.security.auth import get_current_user
from src.services.communities.spaces import (
    create_space,
    get_spaces_by_community,
    get_space,
    update_space,
    delete_space,
    reorder_spaces,
)
from src.services.communities.communities import get_community


router = APIRouter()


class SpaceReorderRequest(BaseModel):
    space_uuids: List[str]


class SpaceCreateRequest(BaseModel):
    name: str
    icon: str | None = None
    description: str | None = None
    ordering: int = 0
    visibility: str = "public"


@router.get(
    "/communities/{community_uuid}/spaces",
    response_model=List[SpaceRead],
    summary="List spaces in a community",
    description="Retrieve all spaces for a community, ordered by the ordering field.",
)
async def api_get_spaces_by_community(
    request: Request,
    community_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> List[SpaceRead]:
    return await get_spaces_by_community(request, community_uuid, current_user, db_session)


@router.post(
    "/communities/{community_uuid}/spaces",
    response_model=SpaceRead,
    summary="Create a space",
    description="Create a new space inside a community. Requires admin/maintainer role.",
)
async def api_create_space(
    request: Request,
    community_uuid: str,
    space_data: SpaceCreateRequest,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> SpaceRead:
    from src.db.communities.spaces import SpaceCreate

    community = await get_community(request, community_uuid, current_user, db_session)
    space_create = SpaceCreate(
        name=space_data.name,
        icon=space_data.icon,
        description=space_data.description,
        ordering=space_data.ordering,
        visibility=space_data.visibility,
        community_id=community.id,
        org_id=community.org_id,
    )
    return await create_space(request, community_uuid, space_create, current_user, db_session)


@router.get(
    "/spaces/{space_uuid}",
    response_model=SpaceRead,
    summary="Get a space",
    description="Retrieve a single space by its UUID.",
)
async def api_get_space(
    request: Request,
    space_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> SpaceRead:
    return await get_space(request, space_uuid, current_user, db_session)


@router.put(
    "/spaces/{space_uuid}",
    response_model=SpaceRead,
    summary="Update a space",
    description="Update a space's attributes. Requires admin/maintainer role.",
)
async def api_update_space(
    request: Request,
    space_uuid: str,
    space_data: SpaceUpdate,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> SpaceRead:
    return await update_space(request, space_uuid, space_data, current_user, db_session)


@router.delete(
    "/spaces/{space_uuid}",
    summary="Delete a space",
    description="Delete a space. Sets space_id to null on associated discussions. Requires admin/maintainer role.",
)
async def api_delete_space(
    request: Request,
    space_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await delete_space(request, space_uuid, current_user, db_session)


@router.put(
    "/communities/{community_uuid}/spaces/reorder",
    response_model=List[SpaceRead],
    summary="Reorder spaces",
    description="Batch reorder spaces by providing their UUIDs in the desired order. Requires admin/maintainer role.",
)
async def api_reorder_spaces(
    request: Request,
    community_uuid: str,
    reorder_data: SpaceReorderRequest,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> List[SpaceRead]:
    return await reorder_spaces(
        request, community_uuid, reorder_data.space_uuids, current_user, db_session
    )
