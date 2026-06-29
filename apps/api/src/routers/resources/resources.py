from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Depends, Request, Query, UploadFile
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.events.database import get_db_session
from src.db.users import PublicUser
from src.db.resources.resources import ResourceRead, ResourceDetailRead, RESOURCE_TYPES
from src.security.auth import get_current_user
from src.services.resources.resources import (
    create_resource,
    get_resource,
    get_resources_by_org,
    update_resource,
    delete_resource,
    upload_resource_thumbnail,
)


router = APIRouter()


class ResourceCreateRequest(BaseModel):
    title: str
    description: str | None = None
    resource_type: str = "link"
    url: str | None = None
    file_id: str | None = None
    file_size: int | None = None
    file_mime: str | None = None
    file_format: str | None = None
    thumbnail_image: str | None = None
    visibility: str = "private"
    locked: bool = False
    content: str | None = None
    metadata: Dict[str, Any] | None = None
    embed_url: str | None = None
    category: str | None = None
    featured: bool = False
    pinned: bool = False
    folder_id: int | None = None
    community_id: int | None = None
    space_id: int | None = None


class ResourceUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    resource_type: str | None = None
    url: str | None = None
    file_id: str | None = None
    file_size: int | None = None
    file_mime: str | None = None
    file_format: str | None = None
    thumbnail_image: str | None = None
    visibility: str | None = None
    locked: bool | None = None
    content: str | None = None
    metadata: Dict[str, Any] | None = None
    embed_url: str | None = None
    category: str | None = None
    featured: bool | None = None
    pinned: bool | None = None
    folder_id: int | None = None
    community_id: int | None = None
    space_id: int | None = None


@router.get(
    "/resources/org/{org_id}",
    response_model=Dict[str, object],
    summary="List resources in an organization",
)
async def api_get_resources_by_org(
    request: Request,
    org_id: int,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    resource_type: str | None = Query(default=None),
    folder_id: int | None = Query(default=None),
    tag_id: int | None = Query(default=None),
    search: str | None = Query(default=None),
    sort_by: str = Query(default="newest"),
    category: str | None = Query(default=None),
    featured: bool | None = Query(default=None),
    pinned: bool | None = Query(default=None),
    community_id: int | None = Query(default=None),
    space_id: int | None = Query(default=None),
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    resources, total = await get_resources_by_org(
        request, org_id, current_user, db_session,
        page=page, limit=limit, resource_type=resource_type,
        folder_id=folder_id, tag_id=tag_id, search=search, sort_by=sort_by,
        category=category, featured=featured, pinned=pinned,
        community_id=community_id, space_id=space_id,
    )
    return {"resources": resources, "total": total, "page": page, "limit": limit}


@router.post(
    "/resources/org/{org_id}",
    response_model=ResourceRead,
    summary="Create a resource",
)
async def api_create_resource(
    request: Request,
    org_id: int,
    resource_data: ResourceCreateRequest,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> ResourceRead:
    from src.db.resources.resources import ResourceCreate

    rc = ResourceCreate(
        title=resource_data.title,
        description=resource_data.description,
        resource_type=resource_data.resource_type,
        url=resource_data.url,
        file_id=resource_data.file_id,
        file_size=resource_data.file_size,
        file_mime=resource_data.file_mime,
        file_format=resource_data.file_format,
        thumbnail_image=resource_data.thumbnail_image,
        visibility=resource_data.visibility,
        locked=resource_data.locked,
        content=resource_data.content,
        metadata=resource_data.metadata,
        embed_url=resource_data.embed_url,
        category=resource_data.category,
        featured=resource_data.featured,
        pinned=resource_data.pinned,
        org_id=org_id,
        author_id=current_user.id,
        folder_id=resource_data.folder_id,
        community_id=resource_data.community_id,
        space_id=resource_data.space_id,
    )
    return await create_resource(request, org_id, rc, current_user, db_session)


@router.get(
    "/resources/{resource_uuid}",
    response_model=ResourceDetailRead,
    summary="Get a resource",
)
async def api_get_resource(
    request: Request,
    resource_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> ResourceDetailRead:
    return await get_resource(request, resource_uuid, current_user, db_session)


@router.put(
    "/resources/{resource_uuid}",
    response_model=ResourceRead,
    summary="Update a resource",
)
async def api_update_resource(
    request: Request,
    resource_uuid: str,
    resource_data: ResourceUpdateRequest,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> ResourceRead:
    from src.db.resources.resources import ResourceUpdate

    ru = ResourceUpdate(**resource_data.model_dump(exclude_none=True))
    return await update_resource(request, resource_uuid, ru, current_user, db_session)


@router.delete(
    "/resources/{resource_uuid}",
    summary="Delete a resource",
)
async def api_delete_resource(
    request: Request,
    resource_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await delete_resource(request, resource_uuid, current_user, db_session)


@router.put(
    "/resources/{resource_uuid}/thumbnail",
    response_model=ResourceRead,
    summary="Upload a resource thumbnail",
)
async def api_upload_resource_thumbnail(
    request: Request,
    resource_uuid: str,
    thumbnail: UploadFile | None = None,
    org_uuid: str | None = Query(default=None),
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> ResourceRead:
    if not thumbnail or not org_uuid:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Thumbnail file and org_uuid are required")

    return await upload_resource_thumbnail(
        request, resource_uuid, thumbnail, current_user, org_uuid, db_session
    )
