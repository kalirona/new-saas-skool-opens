from typing import List, Optional, Union, Dict, Any
from uuid import uuid4
from datetime import datetime
from sqlmodel import select, func, update as sqlmodel_update
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, Request

from src.db.users import PublicUser, AnonymousUser, APITokenUser
from src.db.communities.communities import Community
from src.db.communities.membership_plans import (
    MembershipPlan,
    MembershipPlanCreate,
    MembershipPlanUpdate,
    MembershipPlanRead,
)
from src.db.communities.membership_benefits import (
    MembershipBenefit,
    MembershipBenefitCreate,
    MembershipBenefitRead,
    DEFAULT_BENEFITS,
    BENEFIT_TYPES,
)
from src.db.communities.community_members import (
    CommunityMember,
    CommunityMemberCreate,
    CommunityMemberRead,
    MEMBER_STATUSES,
)
from src.db.usergroups import UserGroup
from src.db.usergroup_user import UserGroupUser
from src.security.rbac import (
    check_resource_access,
    AccessAction,
    authorization_verify_if_user_is_anon,
    authorization_verify_based_on_org_admin_status,
)


async def _slugify(name: str) -> str:
    return name.lower().replace(" ", "-").replace("_", "-")[:64]


async def _ensure_benefits(
    plan_id: int,
    db_session: AsyncSession,
    is_free: bool = False,
) -> List[MembershipBenefit]:
    """Create default benefits for a plan if none exist."""
    existing = (
        await db_session.execute(
            select(MembershipBenefit).where(MembershipBenefit.plan_id == plan_id)
        )
    ).scalars().all()

    if existing:
        return existing

    benefits = []
    for btype, default_val in DEFAULT_BENEFITS.items():
        value = dict(default_val)
        if btype == "community_access":
            value["enabled"] = True
        elif btype == "space_access":
            value["enabled"] = True
        elif btype == "course_access":
            value["enabled"] = is_free
        elif btype == "resource_access":
            value["enabled"] = is_free
        elif btype == "event_access":
            value["enabled"] = is_free
        elif btype == "download_permissions":
            value["enabled"] = not is_free
        elif btype == "ai_credits":
            value["enabled"] = not is_free
            value["credits"] = 0 if is_free else 10

        benefit = MembershipBenefit(
            plan_id=plan_id,
            benefit_type=btype,
            benefit_value=value,
            creation_date=str(datetime.now()),
            update_date=str(datetime.now()),
        )
        db_session.add(benefit)
        benefits.append(benefit)

    await db_session.commit()
    for b in benefits:
        await db_session.refresh(b)

    return benefits


async def create_membership_plan(
    request: Request,
    community_uuid: str,
    plan_data: MembershipPlanCreate,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> MembershipPlanRead:
    await authorization_verify_if_user_is_anon(current_user.id)

    community_statement = select(Community).where(
        Community.community_uuid == community_uuid
    )
    community = (await db_session.execute(community_statement)).scalars().first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    await check_resource_access(
        request, db_session, current_user, community_uuid, AccessAction.UPDATE
    )

    if plan_data.usergroup_id:
        ug_statement = select(UserGroup).where(
            UserGroup.id == plan_data.usergroup_id,
            UserGroup.org_id == community.org_id,
        )
        ug = (await db_session.execute(ug_statement)).scalars().first()
        if not ug:
            raise HTTPException(
                status_code=404,
                detail="UserGroup not found or does not belong to this organization",
            )

    slug = plan_data.slug or await _slugify(plan_data.name)

    plan = MembershipPlan(
        name=plan_data.name,
        slug=slug,
        description=plan_data.description,
        price=plan_data.price,
        currency=plan_data.currency,
        interval=plan_data.interval,
        max_members=plan_data.max_members,
        is_free=plan_data.is_free,
        is_public=plan_data.is_public,
        trial_days=plan_data.trial_days,
        display_order=plan_data.display_order,
        features=plan_data.features,
        status=plan_data.status,
        community_id=community.id,
        org_id=community.org_id,
        usergroup_id=plan_data.usergroup_id,
        plan_uuid=f"plan_{uuid4()}",
        creation_date=str(datetime.now()),
        update_date=str(datetime.now()),
    )

    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)

    await _ensure_benefits(plan.id, db_session, is_free=plan_data.is_free)

    return MembershipPlanRead.model_validate(plan.model_dump())


async def get_membership_plans(
    request: Request,
    community_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> List[MembershipPlanRead]:
    community_statement = select(Community).where(
        Community.community_uuid == community_uuid
    )
    community = (await db_session.execute(community_statement)).scalars().first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    await check_resource_access(
        request, db_session, current_user, community_uuid, AccessAction.READ
    )

    statement = (
        select(MembershipPlan)
        .where(
            MembershipPlan.community_id == community.id,
            MembershipPlan.status == "active",
            MembershipPlan.is_public == True,
        )
        .order_by(MembershipPlan.display_order, MembershipPlan.price)
    )
    plans = (await db_session.execute(statement)).scalars().all()

    return [MembershipPlanRead.model_validate(p.model_dump()) for p in plans]


async def get_all_membership_plans_admin(
    request: Request,
    community_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> List[MembershipPlanRead]:
    await authorization_verify_if_user_is_anon(current_user.id)

    community_statement = select(Community).where(
        Community.community_uuid == community_uuid
    )
    community = (await db_session.execute(community_statement)).scalars().first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    await check_resource_access(
        request, db_session, current_user, community_uuid, AccessAction.UPDATE
    )

    statement = (
        select(MembershipPlan)
        .where(MembershipPlan.community_id == community.id)
        .order_by(MembershipPlan.display_order, MembershipPlan.price)
    )
    plans = (await db_session.execute(statement)).scalars().all()

    return [MembershipPlanRead.model_validate(p.model_dump()) for p in plans]


async def update_membership_plan(
    request: Request,
    plan_uuid: str,
    plan_data: MembershipPlanUpdate,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> MembershipPlanRead:
    await authorization_verify_if_user_is_anon(current_user.id)

    statement = select(MembershipPlan).where(MembershipPlan.plan_uuid == plan_uuid)
    plan = (await db_session.execute(statement)).scalars().first()
    if not plan:
        raise HTTPException(status_code=404, detail="Membership plan not found")

    community_statement = select(Community).where(Community.id == plan.community_id)
    community = (await db_session.execute(community_statement)).scalars().first()
    community_uuid = community.community_uuid if community else None

    if community_uuid:
        await check_resource_access(
            request, db_session, current_user, community_uuid, AccessAction.UPDATE
        )

    if plan_data.name is not None:
        plan.name = plan_data.name
    if plan_data.slug is not None:
        plan.slug = plan_data.slug
    if plan_data.description is not None:
        plan.description = plan_data.description
    if plan_data.price is not None:
        plan.price = plan_data.price
    if plan_data.currency is not None:
        plan.currency = plan_data.currency
    if plan_data.interval is not None:
        plan.interval = plan_data.interval
    if plan_data.max_members is not None:
        plan.max_members = plan_data.max_members
    if plan_data.is_free is not None:
        plan.is_free = plan_data.is_free
    if plan_data.is_public is not None:
        plan.is_public = plan_data.is_public
    if plan_data.trial_days is not None:
        plan.trial_days = plan_data.trial_days
    if plan_data.display_order is not None:
        plan.display_order = plan_data.display_order
    if plan_data.features is not None:
        plan.features = plan_data.features
    if plan_data.status is not None:
        plan.status = plan_data.status
    if plan_data.usergroup_id is not None:
        plan.usergroup_id = plan_data.usergroup_id
    if plan_data.billing_provider is not None:
        plan.billing_provider = plan_data.billing_provider
    if plan_data.billing_provider_plan_id is not None:
        plan.billing_provider_plan_id = plan_data.billing_provider_plan_id

    plan.update_date = str(datetime.now())

    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)

    return MembershipPlanRead.model_validate(plan.model_dump())


async def delete_membership_plan(
    request: Request,
    plan_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> dict:
    await authorization_verify_if_user_is_anon(current_user.id)

    statement = select(MembershipPlan).where(MembershipPlan.plan_uuid == plan_uuid)
    plan = (await db_session.execute(statement)).scalars().first()
    if not plan:
        raise HTTPException(status_code=404, detail="Membership plan not found")

    community_statement = select(Community).where(Community.id == plan.community_id)
    community = (await db_session.execute(community_statement)).scalars().first()
    community_uuid = community.community_uuid if community else None

    if community_uuid:
        await check_resource_access(
            request, db_session, current_user, community_uuid, AccessAction.DELETE
        )

    await db_session.delete(plan)
    await db_session.commit()

    return {"detail": "Membership plan deleted"}


async def get_plan_benefits(
    plan_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> List[MembershipBenefit]:
    plan = (
        await db_session.execute(
            select(MembershipPlan).where(MembershipPlan.plan_uuid == plan_uuid)
        )
    ).scalars().first()
    if not plan:
        raise HTTPException(status_code=404, detail="Membership plan not found")

    benefits = (
        await db_session.execute(
            select(MembershipBenefit).where(MembershipBenefit.plan_id == plan.id)
        )
    ).scalars().all()

    return benefits


async def update_plan_benefits(
    plan_uuid: str,
    benefits_data: List[Dict[str, Any]],
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> List[MembershipBenefit]:
    plan = (
        await db_session.execute(
            select(MembershipPlan).where(MembershipPlan.plan_uuid == plan_uuid)
        )
    ).scalars().first()
    if not plan:
        raise HTTPException(status_code=404, detail="Membership plan not found")

    existing = (
        await db_session.execute(
            select(MembershipBenefit).where(MembershipBenefit.plan_id == plan.id)
        )
    ).scalars().all()
    for b in existing:
        await db_session.delete(b)

    updated = []
    for bdata in benefits_data:
        benefit = MembershipBenefit(
            plan_id=plan.id,
            benefit_type=bdata["benefit_type"],
            benefit_value=bdata.get("benefit_value"),
            creation_date=str(datetime.now()),
            update_date=str(datetime.now()),
        )
        db_session.add(benefit)
        updated.append(benefit)

    await db_session.commit()
    for b in updated:
        await db_session.refresh(b)

    return updated


async def join_community(
    request: Request,
    community_uuid: str,
    plan_uuid: str | None,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> CommunityMemberRead:
    await authorization_verify_if_user_is_anon(current_user.id)

    community = (
        await db_session.execute(
            select(Community).where(Community.community_uuid == community_uuid)
        )
    ).scalars().first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    # When no plan_uuid is provided, only allow joining open communities
    if plan_uuid is None:
        if community.community_type == "paid":
            raise HTTPException(status_code=400, detail="A membership plan is required to join this community")
        plan = None
    else:
        plan = (
            await db_session.execute(
                select(MembershipPlan).where(
                    MembershipPlan.plan_uuid == plan_uuid,
                    MembershipPlan.community_id == community.id,
                    MembershipPlan.status == "active",
                )
            )
        ).scalars().first()
        if not plan:
            raise HTTPException(status_code=404, detail="Membership plan not found")

        # Check max members limit
        if plan.max_members > 0:
            await db_session.execute(
                select(MembershipPlan).where(MembershipPlan.id == plan.id).with_for_update()
            )
            count_stmt = select(func.count(CommunityMember.id)).where(
                CommunityMember.plan_id == plan.id,
                CommunityMember.status == "active",
            )
            member_count = (await db_session.execute(count_stmt)).scalar() or 0
            if member_count >= plan.max_members:
                raise HTTPException(status_code=403, detail="Membership plan is full")

        # For paid plans, billing integration is prepared but not enforced yet
        if plan.price > 0:
            pass  # Billing integration point — validate payment here in the future

    existing = (
        await db_session.execute(
            select(CommunityMember).where(
                CommunityMember.community_id == community.id,
                CommunityMember.user_id == current_user.id,
                CommunityMember.status == "active",
            )
        )
    ).scalars().first()
    if existing:
        raise HTTPException(status_code=409, detail="Already a member of this community")

    member = CommunityMember(
        community_id=community.id,
        user_id=current_user.id,
        org_id=community.org_id,
        plan_id=plan.id if plan else None,
        status="active",
        joined_date=str(datetime.now()),
        creation_date=str(datetime.now()),
        update_date=str(datetime.now()),
    )

    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    # Add user to the plan's UserGroup for access control (only if a plan was selected)
    if plan and plan.usergroup_id:
        ug_user_check = await db_session.execute(
            select(UserGroupUser).where(
                UserGroupUser.usergroup_id == plan.usergroup_id,
                UserGroupUser.user_id == current_user.id,
            )
        )
        if not ug_user_check.scalars().first():
            ug_user = UserGroupUser(
                usergroup_id=plan.usergroup_id,
                user_id=current_user.id,
                org_id=community.org_id,
                creation_date=str(datetime.now()),
                update_date=str(datetime.now()),
            )
            db_session.add(ug_user)
            await db_session.commit()

    return CommunityMemberRead.model_validate(member.model_dump())


async def leave_community(
    request: Request,
    community_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> dict:
    await authorization_verify_if_user_is_anon(current_user.id)

    community = (
        await db_session.execute(
            select(Community).where(Community.community_uuid == community_uuid)
        )
    ).scalars().first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    member = (
        await db_session.execute(
            select(CommunityMember).where(
                CommunityMember.community_id == community.id,
                CommunityMember.user_id == current_user.id,
                CommunityMember.status == "active",
            )
        )
    ).scalars().first()
    if not member:
        raise HTTPException(status_code=404, detail="Not a member of this community")

    member.status = "cancelled"
    member.update_date = str(datetime.now())
    db_session.add(member)
    await db_session.commit()

    # Remove from plan's UserGroup
    plan = (
        await db_session.execute(
            select(MembershipPlan).where(MembershipPlan.id == member.plan_id)
        )
    ).scalars().first()
    if plan and plan.usergroup_id:
        ug_user = (
            await db_session.execute(
                select(UserGroupUser).where(
                    UserGroupUser.usergroup_id == plan.usergroup_id,
                    UserGroupUser.user_id == current_user.id,
                )
            )
        ).scalars().first()
        if ug_user:
            await db_session.delete(ug_user)
            await db_session.commit()

    return {"detail": "Left community"}


async def get_community_members(
    request: Request,
    community_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> List[CommunityMemberRead]:
    community = (
        await db_session.execute(
            select(Community).where(Community.community_uuid == community_uuid)
        )
    ).scalars().first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    await check_resource_access(
        request, db_session, current_user, community_uuid, AccessAction.READ
    )

    statement = select(CommunityMember).where(
        CommunityMember.community_id == community.id,
    )
    if status and status in MEMBER_STATUSES:
        statement = statement.where(CommunityMember.status == status)

    offset_val = (page - 1) * limit
    members = (await db_session.execute(
        statement.order_by(CommunityMember.joined_date.desc()).offset(offset_val).limit(limit)
    )).scalars().all()

    return [CommunityMemberRead.model_validate(m.model_dump()) for m in members]


async def get_user_membership(
    request: Request,
    community_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> Optional[CommunityMemberRead]:
    community = (
        await db_session.execute(
            select(Community).where(Community.community_uuid == community_uuid)
        )
    ).scalars().first()
    if not community:
        return None

    member = (
        await db_session.execute(
            select(CommunityMember).where(
                CommunityMember.community_id == community.id,
                CommunityMember.user_id == current_user.id,
                CommunityMember.status == "active",
            )
        )
    ).scalars().first()

    if not member:
        return None

    return CommunityMemberRead.model_validate(member.model_dump())


async def duplicate_membership_plan(
    request: Request,
    plan_uuid: str,
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> MembershipPlanRead:
    """Duplicate a plan including its benefits."""
    await authorization_verify_if_user_is_anon(current_user.id)

    source = (
        await db_session.execute(
            select(MembershipPlan).where(MembershipPlan.plan_uuid == plan_uuid)
        )
    ).scalars().first()
    if not source:
        raise HTTPException(status_code=404, detail="Membership plan not found")

    community = (
        await db_session.execute(
            select(Community).where(Community.id == source.community_id)
        )
    ).scalars().first()
    community_uuid = community.community_uuid if community else None

    if community_uuid:
        await check_resource_access(
            request, db_session, current_user, community_uuid, AccessAction.UPDATE
        )

    new_plan = MembershipPlan(
        name=f"{source.name} (copy)",
        slug=f"{source.slug}-copy-{uuid4().hex[:6]}",
        description=source.description,
        price=source.price,
        currency=source.currency,
        interval=source.interval,
        max_members=source.max_members,
        is_free=source.is_free,
        is_public=source.is_public,
        trial_days=source.trial_days,
        display_order=source.display_order + 1,
        features=source.features,
        status="draft",
        community_id=source.community_id,
        org_id=source.org_id,
        usergroup_id=source.usergroup_id,
        plan_uuid=f"plan_{uuid4()}",
        creation_date=str(datetime.now()),
        update_date=str(datetime.now()),
    )
    db_session.add(new_plan)
    await db_session.commit()
    await db_session.refresh(new_plan)

    # Copy benefits
    source_benefits = (
        await db_session.execute(
            select(MembershipBenefit).where(MembershipBenefit.plan_id == source.id)
        )
    ).scalars().all()

    for b in source_benefits:
        benefit = MembershipBenefit(
            plan_id=new_plan.id,
            benefit_type=b.benefit_type,
            benefit_value=b.benefit_value,
            creation_date=str(datetime.now()),
            update_date=str(datetime.now()),
        )
        db_session.add(benefit)
    await db_session.commit()

    return MembershipPlanRead.model_validate(new_plan.model_dump())


async def reorder_membership_plans(
    request: Request,
    community_uuid: str,
    plan_uuids: List[str],
    current_user: Union[PublicUser, AnonymousUser, APITokenUser],
    db_session: AsyncSession,
) -> List[MembershipPlanRead]:
    """Batch reorder plans by providing plan UUIDs in display order."""
    await authorization_verify_if_user_is_anon(current_user.id)

    community = (
        await db_session.execute(
            select(Community).where(Community.community_uuid == community_uuid)
        )
    ).scalars().first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    await check_resource_access(
        request, db_session, current_user, community_uuid, AccessAction.UPDATE
    )

    updated = []
    plans = (await db_session.execute(
        select(MembershipPlan).where(
            MembershipPlan.plan_uuid.in_(plan_uuids),
            MembershipPlan.community_id == community.id,
        )
    )).scalars().all()
    plan_map = {p.plan_uuid: p for p in plans}
    for i, puuid in enumerate(plan_uuids):
        plan = plan_map.get(puuid)
        if not plan:
            raise HTTPException(
                status_code=404,
                detail=f"Plan {puuid} not found in this community",
            )
        plan.display_order = i
        plan.update_date = str(datetime.now())
        db_session.add(plan)
        updated.append(plan)

    await db_session.commit()

    return [MembershipPlanRead.model_validate(p.model_dump()) for p in updated]


async def check_benefit_access(
    user_id: int,
    community_id: int,
    benefit_type: str,
    db_session: AsyncSession,
) -> bool:
    """Check if a user's active membership grants a specific benefit type."""
    member = (
        await db_session.execute(
            select(CommunityMember).where(
                CommunityMember.community_id == community_id,
                CommunityMember.user_id == user_id,
                CommunityMember.status == "active",
            )
        )
    ).scalars().first()
    if not member:
        return False

    benefit = (
        await db_session.execute(
            select(MembershipBenefit).where(
                MembershipBenefit.plan_id == member.plan_id,
                MembershipBenefit.benefit_type == benefit_type,
            )
        )
    ).scalars().first()
    if not benefit or not benefit.benefit_value:
        return False

    return benefit.benefit_value.get("enabled", False) if isinstance(benefit.benefit_value, dict) else True
