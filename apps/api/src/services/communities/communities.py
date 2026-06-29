from typing import List, Optional, Union
from uuid import uuid4
from datetime import datetime
from sqlmodel import select, and_, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, Request

from src.db.users import PublicUser, AnonymousUser, APITokenUser
from src.security.auth import resolve_acting_user_id
from src.db.organizations import Organization
from src.db.courses.courses import Course
from src.security.superadmin import is_user_superadmin
from src.db.communities.communities import (
    Community,
    CommunityCreate,
    CommunityRead,
    CommunityUpdate,
)
from src.db.communities.membership_plans import MembershipPlan
from src.db.communities.community_members import CommunityMember
from src.db.communities.spaces import Space
from src.db.usergroup_resources import UserGroupResource
from src.db.usergroup_user import UserGroupUser
from src.security.rbac import (
    check_resource_access,
    AccessAction,
    authorization_verify_if_user_is_anon,
    authorization_verify_based_on_org_admin_status,
    authorization_verify_based_on_roles,
)
from src.core.cache import cache_get, cache_set, cache_delete_pattern


async def create_community(
    request: Request,
    org_id: int,
    community_object: CommunityCreate,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> CommunityRead:
    """
    Create a new community in an organization.

    Requires admin/maintainer role in the organization.
    """
    # Verify user is not anonymous
    await authorization_verify_if_user_is_anon(current_user.id)

    # Verify org exists
    org_statement = select(Organization).where(Organization.id == org_id)
    org = (await db_session.execute(org_statement)).scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Check if user has permission to create communities using role-based permissions
    # This checks the actual database permissions (communities.action_create) instead of hardcoded role IDs
    has_create_permission = await authorization_verify_based_on_roles(
        request, current_user.id, "create", f"community_{org.org_uuid}", db_session
    )

    if not has_create_permission:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to create communities. Check your role permissions.",
        )

    # Create community
    community = Community(
        name=community_object.name,
        description=community_object.description,
        public=community_object.public,
        org_id=org_id,
        course_id=community_object.course_id,
        community_uuid=f"community_{uuid4()}",
        creation_date=str(datetime.now()),
        update_date=str(datetime.now()),
    )
 
    db_session.add(community)
    await db_session.commit()
    await db_session.refresh(community)
 
    # Auto-create default spaces
    default_spaces = [
        {"name": "General", "icon": "💬", "description": "General discussions", "ordering": 0, "visibility": "public"},
        {"name": "Announcements", "icon": "📢", "description": "Official announcements", "ordering": 1, "visibility": "public"},
        {"name": "Questions", "icon": "❓", "description": "Q&A and support", "ordering": 2, "visibility": "public"},
    ]
    now = str(datetime.now())
    for sp in default_spaces:
        space = Space(
            name=sp["name"],
            icon=sp["icon"],
            description=sp["description"],
            ordering=sp["ordering"],
            visibility=sp["visibility"],
            community_id=community.id,
            org_id=community.org_id,
            space_uuid=f"space_{community.community_uuid}_{sp['name'].lower()}",
            creation_date=now,
            update_date=now,
        )
        db_session.add(space)
    await db_session.commit()
 
    return CommunityRead.model_validate(community.model_dump())
 
 
async def get_community(
    request: Request,
    community_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> CommunityRead:
    """
    Get a community by UUID.
    """
    cached = cache_get(f"community:{community_uuid}")
    if cached is not None:
        community_data = cached
    else:
        statement = select(Community).where(Community.community_uuid == community_uuid)
        community = (await db_session.execute(statement)).scalars().first()

        if not community:
            raise HTTPException(status_code=404, detail="Community not found")

        community_data = CommunityRead.model_validate(community.model_dump()).model_dump()
        cache_set(f"community:{community_uuid}", community_data, ttl=120)

    # RBAC check (always performed regardless of cache)
    await check_resource_access(request, db_session, current_user, community_uuid, AccessAction.READ)

    return CommunityRead(**community_data)


async def get_communities_by_org(
    request: Request,
    org_id: int,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
    page: int = 1,
    limit: int = 10,
) -> List[CommunityRead]:
    """
    Get paginated list of communities for an organization.

    SECURITY: Maximum limit enforced to prevent data dumping.
    """
    # SECURITY: Enforce maximum limit
    limit = min(limit, 50)
    page = max(page, 1)
    offset = (page - 1) * limit

    # Resolve to the token's creator for API-token callers so ownership /
    # admin / membership checks run against a real user_id.
    acting_user_id = resolve_acting_user_id(current_user)

    # For anonymous users, only show public communities
    if isinstance(current_user, AnonymousUser) or acting_user_id == 0:
        query = select(Community).where(
            Community.org_id == org_id,
            Community.public == True
        )
        query = query.order_by(Community.creation_date.desc()).offset(offset).limit(limit)  # type: ignore
        communities = (await db_session.execute(query)).scalars().all()
        return [CommunityRead.model_validate(c.model_dump()) for c in communities]

    # Superadmins bypass admin check — they can see all communities
    if await is_user_superadmin(acting_user_id, db_session):
        query = select(Community).where(Community.org_id == org_id)
        query = query.order_by(Community.creation_date.desc()).offset(offset).limit(limit)  # type: ignore
        communities = (await db_session.execute(query)).scalars().all()
        return [CommunityRead.model_validate(c.model_dump()) for c in communities]

    # Check if user has admin-level permissions (can read all communities)
    # First check role-based permissions, then fall back to org admin status
    has_admin_read = await authorization_verify_based_on_roles(
        request, acting_user_id, "update", f"community_{org_id}", db_session
    )
    is_admin_or_maintainer = has_admin_read or await authorization_verify_based_on_org_admin_status(
        request, acting_user_id, "read", f"org_{org_id}", db_session
    )

    if is_admin_or_maintainer:
        # Admins see all communities
        query = select(Community).where(Community.org_id == org_id)
        query = query.order_by(Community.creation_date.desc()).offset(offset).limit(limit)  # type: ignore
        communities = (await db_session.execute(query)).scalars().all()
        return [CommunityRead.model_validate(c.model_dump()) for c in communities]

    # For regular users, use a subquery approach to avoid DISTINCT with JSON columns
    # Get IDs of communities the user has access to
    accessible_community_ids_query = (
        select(Community.id)
        .where(Community.org_id == org_id)
        .outerjoin(UserGroupResource, UserGroupResource.resource_uuid == Community.community_uuid)
        .outerjoin(UserGroupUser, and_(
            UserGroupUser.usergroup_id == UserGroupResource.usergroup_id,
            UserGroupUser.user_id == acting_user_id
        ))
        .where(or_(
            Community.public == True,
            UserGroupResource.resource_uuid.is_(None),  # Not in any UserGroup
            UserGroupUser.user_id == acting_user_id,  # User in linked UserGroup
        ))
        .distinct()
    )

    # Now select full communities using the IDs
    query = (
        select(Community)
        .where(Community.id.in_(accessible_community_ids_query))
        .order_by(Community.creation_date.desc(), Community.id.desc())
        .offset(offset)
        .limit(limit)
    )

    communities = (await db_session.execute(query)).scalars().all()
    return [CommunityRead.model_validate(c.model_dump()) for c in communities]


async def get_community_by_course(
    request: Request,
    course_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> CommunityRead | None:
    """
    Get the community linked to a specific course.
    """
    # Get the course first
    course_statement = select(Course).where(Course.course_uuid == course_uuid)
    course = (await db_session.execute(course_statement)).scalars().first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Find community linked to this course
    community_statement = select(Community).where(Community.course_id == course.id)
    community = (await db_session.execute(community_statement)).scalars().first()

    if not community:
        return None

    # Check if user can read the community
    await check_resource_access(
        request, db_session, current_user, community.community_uuid, AccessAction.READ
    )

    return CommunityRead.model_validate(community.model_dump())


async def update_community(
    request: Request,
    community_uuid: str,
    community_object: CommunityUpdate,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> CommunityRead:
    """
    Update a community.

    Requires admin/maintainer role.
    """
    # Get community
    statement = select(Community).where(Community.community_uuid == community_uuid)
    community = (await db_session.execute(statement)).scalars().first()

    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    # RBAC check
    await check_resource_access(request, db_session, current_user, community_uuid, AccessAction.UPDATE)

    # Update fields
    if community_object.name is not None:
        community.name = community_object.name
    if community_object.description is not None:
        community.description = community_object.description
    if community_object.public is not None:
        community.public = community_object.public
    if community_object.moderation_words is not None:
        community.moderation_words = community_object.moderation_words
    if community_object.moderation_settings is not None:
        community.moderation_settings = community_object.moderation_settings

    community.update_date = str(datetime.now())

    db_session.add(community)
    await db_session.commit()
    await db_session.refresh(community)

    cache_delete_pattern(f"community:{community_uuid}")

    return CommunityRead.model_validate(community.model_dump())


async def delete_community(
    request: Request,
    community_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> dict:
    """
    Delete a community.

    Requires admin/maintainer role.
    """
    # Get community
    statement = select(Community).where(Community.community_uuid == community_uuid)
    community = (await db_session.execute(statement)).scalars().first()

    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    # RBAC check
    await check_resource_access(request, db_session, current_user, community_uuid, AccessAction.DELETE)

    await db_session.delete(community)
    await db_session.commit()

    cache_delete_pattern(f"community:{community_uuid}")
    cache_delete_pattern(f"member_check:*:{community.id}")

    return {"detail": "Community deleted"}


async def link_community_to_course(
    request: Request,
    community_uuid: str,
    course_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> CommunityRead:
    """
    Link a community to a course.

    Requires admin/maintainer role.
    """
    # Get community
    statement = select(Community).where(Community.community_uuid == community_uuid)
    community = (await db_session.execute(statement)).scalars().first()

    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    # RBAC check
    await check_resource_access(request, db_session, current_user, community_uuid, AccessAction.UPDATE)

    # Get the course
    course_statement = select(Course).where(Course.course_uuid == course_uuid)
    course = (await db_session.execute(course_statement)).scalars().first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Check if course belongs to same org
    if course.org_id != community.org_id:
        raise HTTPException(
            status_code=400,
            detail="Course must belong to the same organization as the community",
        )

    # Check if another community is already linked to this course
    existing_statement = select(Community).where(
        Community.course_id == course.id,
        Community.id != community.id
    )
    existing = (await db_session.execute(existing_statement)).scalars().first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="This course already has a linked community",
        )

    community.course_id = course.id
    community.update_date = str(datetime.now())

    db_session.add(community)
    await db_session.commit()
    await db_session.refresh(community)

    cache_delete_pattern(f"community:{community_uuid}")

    return CommunityRead.model_validate(community.model_dump())


async def unlink_community_from_course(
    request: Request,
    community_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> CommunityRead:
    """
    Unlink a community from its course.

    Requires admin/maintainer role.
    """
    # Get community
    statement = select(Community).where(Community.community_uuid == community_uuid)
    community = (await db_session.execute(statement)).scalars().first()

    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    # RBAC check
    await check_resource_access(request, db_session, current_user, community_uuid, AccessAction.UPDATE)

    community.course_id = None
    community.update_date = str(datetime.now())

    db_session.add(community)
    await db_session.commit()
    await db_session.refresh(community)

    cache_delete_pattern(f"community:{community_uuid}")

    return CommunityRead.model_validate(community.model_dump())


async def get_community_user_rights(
    request: Request,
    community_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> dict:
    """
    Get detailed user rights for a specific community.

    Returns comprehensive rights information for UI feature toggling.
    """
    # Check if community exists
    statement = select(Community).where(Community.community_uuid == community_uuid)
    community = (await db_session.execute(statement)).scalars().first()

    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    # API tokens report rights under their creator's identity.
    acting_user_id = resolve_acting_user_id(current_user)

    # Initialize rights object
    rights = {
        "community_uuid": community_uuid,
        "user_id": acting_user_id,
        "is_anonymous": acting_user_id == 0,
        "permissions": {
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
            "create_discussion": False,
        },
        "ownership": {
            "is_admin": False,
            "is_maintainer_role": False,
        },
        "access": {
            "via_public": False,
            "via_usergroups": [],
            "has_usergroup_restriction": False,
        },
    }

    # Handle anonymous users
    if acting_user_id == 0:
        if community.public:
            rights["permissions"]["read"] = True
            rights["access"]["via_public"] = True
        return rights

    # Check community access method
    rights["access"]["via_public"] = community.public

    # Check UserGroups access
    usergroup_stmt = select(UserGroupResource).where(
        UserGroupResource.resource_uuid == community_uuid
    )
    usergroup_resources = (await db_session.execute(usergroup_stmt)).scalars().all()

    if usergroup_resources:
        rights["access"]["has_usergroup_restriction"] = True
        usergroup_ids = [ugr.usergroup_id for ugr in usergroup_resources]

        membership_stmt = select(UserGroupUser).where(
            UserGroupUser.usergroup_id.in_(usergroup_ids),
            UserGroupUser.user_id == acting_user_id
        )
        user_memberships = (await db_session.execute(membership_stmt)).scalars().all()
        rights["access"]["via_usergroups"] = [m.usergroup_id for m in user_memberships]

    # Check membership plans availability
    plans_stmt = select(MembershipPlan).where(
        MembershipPlan.community_id == community.id,
        MembershipPlan.status == "active",
        MembershipPlan.is_public == True,
    )
    available_plans = (await db_session.execute(plans_stmt)).scalars().all()
    rights["membership"] = {
        "has_plans": len(available_plans) > 0,
        "available_plans": [
            {
                "plan_uuid": p.plan_uuid,
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "currency": p.currency,
                "interval": p.interval,
                "max_members": p.max_members,
                "features": p.features,
            }
            for p in available_plans
        ],
        "user_membership": None,
    }

    # Check if user has an active membership
    member_stmt = select(CommunityMember).where(
        CommunityMember.community_id == community.id,
        CommunityMember.user_id == acting_user_id,
        CommunityMember.status == "active",
    )
    user_member = (await db_session.execute(member_stmt)).scalars().first()
    if user_member:
        rights["membership"]["user_membership"] = {
            "plan_id": user_member.plan_id,
            "status": user_member.status,
            "joined_date": user_member.joined_date,
        }

    # Check admin/maintainer role using role-based permissions
    has_update_permission = await authorization_verify_based_on_roles(
        request, acting_user_id, "update", community_uuid, db_session
    )
    is_admin_or_maintainer = has_update_permission or await authorization_verify_based_on_org_admin_status(
        request, acting_user_id, "update", community_uuid, db_session
    )

    # Check if user has access via public, UserGroups, membership, or admin status
    is_member = user_member is not None
    has_access = (
        community.public or
        not rights["access"]["has_usergroup_restriction"] or
        len(rights["access"]["via_usergroups"]) > 0 or
        is_member or
        is_admin_or_maintainer
    )

    if has_access:
        rights["permissions"]["read"] = True
        rights["permissions"]["create_discussion"] = True

    if is_admin_or_maintainer:
        rights["ownership"]["is_admin"] = True
        rights["ownership"]["is_maintainer_role"] = True
        rights["permissions"]["create"] = True
        rights["permissions"]["update"] = True
        rights["permissions"]["delete"] = True

    return rights
