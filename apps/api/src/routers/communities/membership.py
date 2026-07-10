from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Request, Query
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.events.database import get_db_session
from src.db.users import PublicUser
from src.db.communities.membership_plans import MembershipPlanRead
from src.db.communities.membership_benefits import MembershipBenefitRead
from src.db.communities.community_members import CommunityMemberRead
from src.security.auth import get_current_user
from src.services.communities.membership import (
    create_membership_plan,
    get_membership_plans,
    get_all_membership_plans_admin,
    update_membership_plan,
    delete_membership_plan,
    duplicate_membership_plan,
    reorder_membership_plans,
    get_plan_benefits,
    update_plan_benefits,
    join_community,
    leave_community,
    get_community_members,
    get_user_membership,
)


router = APIRouter()


class MembershipPlanCreateRequest(BaseModel):
    name: str
    slug: str | None = None
    description: str | None = None
    price: float = 0.0
    currency: str = "usd"
    interval: str = "monthly"
    max_members: int = 0
    is_free: bool = False
    is_public: bool = True
    trial_days: int = 0
    display_order: int = 0
    features: dict | None = None
    status: str = "draft"
    usergroup_id: int | None = None
    billing_provider: str | None = None
    billing_provider_plan_id: str | None = None


class MembershipPlanUpdateRequest(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    price: float | None = None
    currency: str | None = None
    interval: str | None = None
    max_members: int | None = None
    is_free: bool | None = None
    is_public: bool | None = None
    trial_days: int | None = None
    display_order: int | None = None
    features: dict | None = None
    status: str | None = None
    usergroup_id: int | None = None
    billing_provider: str | None = None
    billing_provider_plan_id: str | None = None


class JoinRequest(BaseModel):
    plan_uuid: str | None = None


class BenefitData(BaseModel):
    benefit_type: str
    benefit_value: Dict[str, Any] | None = None


class BenefitsUpdateRequest(BaseModel):
    benefits: List[BenefitData]


class ReorderPlansRequest(BaseModel):
    plan_uuids: List[str]


@router.get(
    "/communities/{community_uuid}/plans",
    response_model=List[MembershipPlanRead],
    summary="List active membership plans for a community",
)
async def api_get_membership_plans(
    request: Request,
    community_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> List[MembershipPlanRead]:
    return await get_membership_plans(request, community_uuid, current_user, db_session)


@router.get(
    "/communities/{community_uuid}/plans/admin",
    response_model=List[MembershipPlanRead],
    summary="List all membership plans (admin view)",
)
async def api_get_all_membership_plans_admin(
    request: Request,
    community_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> List[MembershipPlanRead]:
    return await get_all_membership_plans_admin(request, community_uuid, current_user, db_session)


@router.post(
    "/communities/{community_uuid}/plans",
    response_model=MembershipPlanRead,
    summary="Create a membership plan",
)
async def api_create_membership_plan(
    request: Request,
    community_uuid: str,
    plan_data: MembershipPlanCreateRequest,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> MembershipPlanRead:
    from src.db.communities.membership_plans import MembershipPlanCreate
    from src.db.communities.communities import Community
    from sqlmodel import select

    community = (await db_session.execute(
        select(Community).where(Community.community_uuid == community_uuid)
    )).scalars().first()

    if not community:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Community not found")

    pc = MembershipPlanCreate(
        name=plan_data.name,
        slug=plan_data.slug or "",
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
        usergroup_id=plan_data.usergroup_id,
        community_id=community.id,
        org_id=community.org_id,
    )
    return await create_membership_plan(request, community_uuid, pc, current_user, db_session)


@router.put(
    "/plans/{plan_uuid}",
    response_model=MembershipPlanRead,
    summary="Update a membership plan",
)
async def api_update_membership_plan(
    request: Request,
    plan_uuid: str,
    plan_data: MembershipPlanUpdateRequest,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> MembershipPlanRead:
    from src.db.communities.membership_plans import MembershipPlanUpdate

    pu = MembershipPlanUpdate(**plan_data.model_dump(exclude_none=True))
    return await update_membership_plan(request, plan_uuid, pu, current_user, db_session)


@router.delete(
    "/plans/{plan_uuid}",
    summary="Delete a membership plan",
)
async def api_delete_membership_plan(
    request: Request,
    plan_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await delete_membership_plan(request, plan_uuid, current_user, db_session)


@router.get(
    "/plans/{plan_uuid}/benefits",
    response_model=List[MembershipBenefitRead],
    summary="Get plan benefits",
)
async def api_get_plan_benefits(
    request: Request,
    plan_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> List[MembershipBenefitRead]:
    benefits = await get_plan_benefits(plan_uuid, current_user, db_session)
    return [MembershipBenefitRead.model_validate(b.model_dump()) for b in benefits]


@router.put(
    "/plans/{plan_uuid}/benefits",
    response_model=List[MembershipBenefitRead],
    summary="Update plan benefits",
)
async def api_update_plan_benefits(
    request: Request,
    plan_uuid: str,
    benefits_data: BenefitsUpdateRequest,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> List[MembershipBenefitRead]:
    from src.db.communities.membership_benefits import MembershipBenefit

    raw = [b.model_dump() for b in benefits_data.benefits]
    updated = await update_plan_benefits(plan_uuid, raw, current_user, db_session)
    return [MembershipBenefitRead.model_validate(b.model_dump()) for b in updated]


@router.post(
    "/plans/{plan_uuid}/duplicate",
    response_model=MembershipPlanRead,
    summary="Duplicate a membership plan",
)
async def api_duplicate_membership_plan(
    request: Request,
    plan_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> MembershipPlanRead:
    return await duplicate_membership_plan(request, plan_uuid, current_user, db_session)


@router.put(
    "/communities/{community_uuid}/plans/reorder",
    response_model=List[MembershipPlanRead],
    summary="Reorder membership plans",
)
async def api_reorder_membership_plans(
    request: Request,
    community_uuid: str,
    reorder_data: ReorderPlansRequest,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> List[MembershipPlanRead]:
    return await reorder_membership_plans(request, community_uuid, reorder_data.plan_uuids, current_user, db_session)


@router.post(
    "/communities/{community_uuid}/join",
    response_model=CommunityMemberRead,
    summary="Join a community",
)
async def api_join_community(
    request: Request,
    community_uuid: str,
    join_data: JoinRequest,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> CommunityMemberRead:
    return await join_community(request, community_uuid, join_data.plan_uuid, current_user, db_session)


@router.post(
    "/communities/{community_uuid}/leave",
    summary="Leave a community",
)
async def api_leave_community(
    request: Request,
    community_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await leave_community(request, community_uuid, current_user, db_session)


@router.get(
    "/communities/{community_uuid}/members",
    response_model=List[CommunityMemberRead],
    summary="List community members",
)
async def api_get_community_members(
    request: Request,
    community_uuid: str,
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> List[CommunityMemberRead]:
    return await get_community_members(request, community_uuid, current_user, db_session, status, page, limit)


@router.get(
    "/communities/{community_uuid}/my-membership",
    response_model=Optional[CommunityMemberRead],
    summary="Get current user's membership",
)
async def api_get_user_membership(
    request: Request,
    community_uuid: str,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> Optional[CommunityMemberRead]:
    return await get_user_membership(request, community_uuid, current_user, db_session)
