import asyncio
from typing import List, Optional, Union
from uuid import uuid4
from datetime import datetime
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, Request
from sqlalchemy import func

from src.core.cache import cache_get, cache_set, cache_delete_pattern

from src.db.users import PublicUser, AnonymousUser, APITokenUser
from src.db.resources.resources import (
    Resource,
    ResourceCreate,
    ResourceUpdate,
    ResourceRead,
    ResourceDetailRead,
    RESOURCE_TYPES,
)
from src.db.resources.tags import ResourceTag
from src.db.organizations import Organization
from src.db.users import User
from src.db.communities.communities import Community
from src.db.communities.membership_plans import MembershipPlan
from src.db.communities.community_members import CommunityMember
from src.db.communities.membership_benefits import MembershipBenefit
from src.db.communities.plan_resources import PlanResource
from src.db.resource_authors import (
    ResourceAuthor,
    ResourceAuthorshipEnum,
    ResourceAuthorshipStatusEnum,
)
from src.security.rbac import (
    check_resource_access,
    AccessAction,
    authorization_verify_if_user_is_anon,
    authorization_verify_based_on_org_admin_status,
)
from src.db.folders.folders import Folder as FolderModel
from src.db.folders.folder_content import FolderContent
from src.services.folders.folders import add_folder_content


async def create_resource(
    request: Request,
    org_id: int,
    resource_data: ResourceCreate,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> ResourceRead:
    await authorization_verify_if_user_is_anon(current_user.id)

    org_statement = select(Organization).where(Organization.id == org_id)
    org = (await db_session.execute(org_statement)).scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    is_admin = await authorization_verify_based_on_org_admin_status(
        request, current_user.id, "create", org.org_uuid, db_session
    )
    if not is_admin and current_user.id == 0:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    resource = Resource(
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
        resource_uuid=f"res_{uuid4()}",
        creation_date=str(datetime.now()),
        update_date=str(datetime.now()),
    )

    db_session.add(resource)
    await db_session.commit()
    await db_session.refresh(resource)

    author = ResourceAuthor(
        resource_uuid=resource.resource_uuid,
        user_id=current_user.id,
        authorship=ResourceAuthorshipEnum.CREATOR,
        authorship_status=ResourceAuthorshipStatusEnum.ACTIVE,
        creation_date=str(datetime.now()),
    )
    db_session.add(author)
    await db_session.commit()

    if resource_data.folder_id:
        folder_statement = select(FolderModel).where(FolderModel.id == resource_data.folder_id)
        folder = (await db_session.execute(folder_statement)).scalars().first()
        if folder:
            await add_folder_content(
                db_session, folder.folder_uuid, resource.resource_uuid, current_user, request
            )

    cache_delete_pattern("resources:*")

    return ResourceRead.model_validate(resource.model_dump())


async def get_resource(
    request: Request,
    resource_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> ResourceDetailRead:
    statement = select(Resource).where(Resource.resource_uuid == resource_uuid)
    resource = (await db_session.execute(statement)).scalars().first()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    await check_resource_access(
        request, db_session, current_user, resource_uuid, AccessAction.READ
    )

    base = ResourceRead.model_validate(resource.model_dump())
    detail = ResourceDetailRead(**base.model_dump())

    futures = [
        db_session.execute(select(Organization).where(Organization.id == resource.org_id)),
        db_session.execute(select(User).where(User.id == resource.author_id)),
    ]
    if resource.community_id:
        futures.append(
            db_session.execute(select(Community).where(Community.id == resource.community_id))
        )
    if resource.community_id and not isinstance(current_user, AnonymousUser):
        futures.append(
            db_session.execute(
                select(CommunityMember).where(
                    CommunityMember.community_id == resource.community_id,
                    CommunityMember.user_id == current_user.id,
                    CommunityMember.status == "active",
                )
            )
        )

    results = await asyncio.gather(*futures)

    org = results[0].scalars().first()
    if org:
        detail.org_uuid = org.org_uuid

    author = results[1].scalars().first()
    if author:
        detail.author_username = author.username
        detail.author_avatar = author.avatar_image
        detail.author_first_name = author.first_name
        detail.author_last_name = author.last_name

    ri = 2
    if resource.community_id:
        community = results[ri].scalars().first()
        ri += 1
        if community:
            detail.community_name = community.name
            detail.community_uuid = community.community_uuid
            detail.community_thumbnail = community.thumbnail_image

    if resource.community_id and not isinstance(current_user, AnonymousUser):
        member = results[ri].scalars().first()
        detail.user_has_access = member is not None

        if not member:
            plan_link = (
                await db_session.execute(
                    select(PlanResource).where(PlanResource.resource_id == resource.id)
                )
            ).scalars().first()
            if plan_link:
                plan = (
                    await db_session.execute(
                        select(MembershipPlan).where(MembershipPlan.id == plan_link.plan_id)
                    )
                ).scalars().first()
                if plan:
                    detail.required_plan_name = plan.name
                    detail.required_plan_uuid = plan.plan_uuid

    return detail


async def get_resources_by_org(
    request: Request,
    org_id: int,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
    page: int = 1,
    limit: int = 20,
    resource_type: Optional[str] = None,
    folder_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    search: Optional[str] = None,
    sort_by: str = "newest",
    category: Optional[str] = None,
    featured: Optional[bool] = None,
    pinned: Optional[bool] = None,
    community_id: Optional[int] = None,
    space_id: Optional[int] = None,
) -> tuple[List[ResourceRead], int]:
    cache_key = (
        f"resources:{org_id}:{page}:{limit}:{resource_type}:{folder_id}:{tag_id}:"
        f"{search}:{sort_by}:{category}:{featured}:{pinned}:{community_id}:{space_id}"
    )
    cached = cache_get(cache_key)
    if cached is not None:
        return ([ResourceRead(**r) for r in cached["items"]], cached["total"])

    org_statement = select(Organization).where(Organization.id == org_id)
    org = (await db_session.execute(org_statement)).scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    statement = select(Resource).where(Resource.org_id == org_id)

    if resource_type and resource_type in RESOURCE_TYPES:
        statement = statement.where(Resource.resource_type == resource_type)

    if folder_id is not None:
        statement = statement.where(Resource.folder_id == folder_id)

    if category is not None:
        statement = statement.where(Resource.category == category)

    if featured is not None:
        statement = statement.where(Resource.featured == featured)

    if pinned is not None:
        statement = statement.where(Resource.pinned == pinned)

    if community_id is not None:
        statement = statement.where(Resource.community_id == community_id)

    if space_id is not None:
        statement = statement.where(Resource.space_id == space_id)

    if search:
        search_pattern = f"%{search}%"
        statement = statement.where(
            or_(
                Resource.title.ilike(search_pattern),
                Resource.description.ilike(search_pattern),
                Resource.content.ilike(search_pattern),
            )
        )

    if tag_id is not None:
        resource_ids_subq = (
            select(ResourceTag.resource_id)
            .where(ResourceTag.tag_id == tag_id)
            .subquery()
        )
        statement = statement.where(Resource.id.in_(resource_ids_subq))  # type: ignore

    pin_sort = Resource.pinned.desc().nullslast()  # pinned items first
    if sort_by == "oldest":
        order = Resource.creation_date.asc()
    elif sort_by == "title":
        order = Resource.title.asc()
    else:
        order = Resource.creation_date.desc()
    statement = statement.order_by(pin_sort, order)

    count_statement = statement
    total = (
        await db_session.execute(
            select(func.count()).select_from(count_statement.subquery())
        )
    ).scalar() or 0

    offset = (page - 1) * limit
    statement = statement.offset(offset).limit(limit)
    resources = (await db_session.execute(statement)).scalars().all()

    items = [ResourceRead.model_validate(r.model_dump()) for r in resources]
    cache_set(cache_key, {"items": [i.model_dump() for i in items], "total": total}, ttl=30)

    return (items, total)


async def update_resource(
    request: Request,
    resource_uuid: str,
    resource_data: ResourceUpdate,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> ResourceRead:
    acting_user_id = current_user.id
    await authorization_verify_if_user_is_anon(acting_user_id)

    statement = select(Resource).where(Resource.resource_uuid == resource_uuid)
    resource = (await db_session.execute(statement)).scalars().first()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    await check_resource_access(
        request, db_session, current_user, resource_uuid, AccessAction.UPDATE
    )

    if resource_data.title is not None:
        resource.title = resource_data.title
    if resource_data.description is not None:
        resource.description = resource_data.description
    if resource_data.resource_type is not None:
        resource.resource_type = resource_data.resource_type
    if resource_data.url is not None:
        resource.url = resource_data.url
    if resource_data.file_id is not None:
        resource.file_id = resource_data.file_id
    if resource_data.file_size is not None:
        resource.file_size = resource_data.file_size
    if resource_data.file_mime is not None:
        resource.file_mime = resource_data.file_mime
    if resource_data.file_format is not None:
        resource.file_format = resource_data.file_format
    if resource_data.thumbnail_image is not None:
        resource.thumbnail_image = resource_data.thumbnail_image
    if resource_data.visibility is not None:
        resource.visibility = resource_data.visibility
    if resource_data.folder_id is not None:
        resource.folder_id = resource_data.folder_id
    if resource_data.locked is not None:
        resource.locked = resource_data.locked
    if resource_data.content is not None:
        resource.content = resource_data.content
    if resource_data.metadata is not None:
        resource.metadata = resource_data.metadata
    if resource_data.embed_url is not None:
        resource.embed_url = resource_data.embed_url
    if resource_data.category is not None:
        resource.category = resource_data.category
    if resource_data.featured is not None:
        resource.featured = resource_data.featured
    if resource_data.pinned is not None:
        resource.pinned = resource_data.pinned
    if resource_data.community_id is not None:
        resource.community_id = resource_data.community_id
    if resource_data.space_id is not None:
        resource.space_id = resource_data.space_id

    resource.update_date = str(datetime.now())

    db_session.add(resource)
    await db_session.commit()
    await db_session.refresh(resource)

    cache_delete_pattern("resources:*")

    return ResourceRead.model_validate(resource.model_dump())


async def delete_resource(
    request: Request,
    resource_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> dict:
    acting_user_id = current_user.id
    await authorization_verify_if_user_is_anon(acting_user_id)

    statement = select(Resource).where(Resource.resource_uuid == resource_uuid)
    resource = (await db_session.execute(statement)).scalars().first()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    await check_resource_access(
        request, db_session, current_user, resource_uuid, AccessAction.DELETE
    )

    delete_fc = select(FolderContent).where(
        FolderContent.resource_uuid == resource_uuid
    )
    fc_rows = (await db_session.execute(delete_fc)).scalars().all()
    for row in fc_rows:
        await db_session.delete(row)

    await db_session.delete(resource)
    await db_session.commit()

    cache_delete_pattern("resources:*")

    return {"detail": "Resource deleted"}


async def upload_resource_thumbnail(
    request: Request,
    resource_uuid: str,
    thumbnail_file,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    org_uuid: str,
    db_session: AsyncSession,
) -> ResourceRead:
    await authorization_verify_if_user_is_anon(current_user.id)

    statement = select(Resource).where(Resource.resource_uuid == resource_uuid)
    resource = (await db_session.execute(statement)).scalars().first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    await check_resource_access(
        request, db_session, current_user, resource_uuid, AccessAction.UPDATE
    )

    from src.services.utils.upload_content import upload_file

    filename = await upload_file(
        file=thumbnail_file,
        directory=f"resources/{resource_uuid}/thumbnails",
        type_of_dir="orgs",
        uuid=org_uuid,
        allowed_types=["image"],
        filename_prefix="thumbnail",
    )

    resource.thumbnail_image = filename
    resource.update_date = str(datetime.now())

    db_session.add(resource)
    await db_session.commit()
    await db_session.refresh(resource)

    cache_delete_pattern("resources:*")

    return ResourceRead.model_validate(resource.model_dump())
