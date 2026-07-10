"""
Subscription lifecycle service — shared between all billing providers.

Handles:
- CommunityMember creation / status transitions
- UserGroup membership (add/remove on subscribe/cancel)
- Per-request status sync from provider
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
from src.db.communities.community_members import CommunityMember, CommunityMemberCreate
from src.db.communities.membership_plans import MembershipPlan
from src.db.communities.communities import Community
from src.db.organizations import Organization
from src.db.usergroup_user import UserGroupUser
from src.db.users import PublicUser
from src.billing.base import BillingProvider, BillingSubscription


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Usergroup helpers ─────────────────────────────────────────────────────


async def add_member_to_usergroup(
    db_session: AsyncSession,
    plan: MembershipPlan,
    user_id: int,
    org_id: int,
) -> None:
    if not plan.usergroup_id:
        return
    existing = (
        await db_session.execute(
            select(UserGroupUser).where(
                UserGroupUser.usergroup_id == plan.usergroup_id,
                UserGroupUser.user_id == user_id,
            )
        )
    ).scalars().first()
    if existing:
        return
    link = UserGroupUser(
        usergroup_id=plan.usergroup_id,
        user_id=user_id,
        org_id=org_id,
        creation_date=_now_iso(),
        update_date=_now_iso(),
    )
    db_session.add(link)
    await db_session.commit()


async def remove_member_from_usergroup(
    db_session: AsyncSession,
    plan: MembershipPlan,
    user_id: int,
) -> None:
    if not plan.usergroup_id:
        return
    existing = (
        await db_session.execute(
            select(UserGroupUser).where(
                UserGroupUser.usergroup_id == plan.usergroup_id,
                UserGroupUser.user_id == user_id,
            )
        )
    ).scalars().first()
    if existing:
        await db_session.delete(existing)
        await db_session.commit()


# ── CommunityMember upsert ────────────────────────────────────────────────


async def find_member_by_subscription(
    db_session: AsyncSession,
    subscription_id: str,
) -> Optional[CommunityMember]:
    return (
        await db_session.execute(
            select(CommunityMember).where(
                CommunityMember.billing_provider_subscription_id == subscription_id
            )
        )
    ).scalars().first()


async def create_member(
    db_session: AsyncSession,
    plan: MembershipPlan,
    community: Community,
    org: Organization,
    user_id: int,
    status: str = "active",
    subscription_id: Optional[str] = None,
    provider: Optional[str] = None,
    expires_date: Optional[str] = None,
    trial_end_date: Optional[str] = None,
) -> CommunityMember:
    now = _now_iso()
    member = CommunityMember(
        community_id=community.id,
        user_id=user_id,
        org_id=org.id,
        plan_id=plan.id,
        status=status,
        billing_provider_subscription_id=subscription_id,
        billing_provider=provider,
        joined_date=now,
        expires_date=expires_date,
        trial_end_date=trial_end_date,
        creation_date=now,
        update_date=now,
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)
    return member


async def upsert_member(
    db_session: AsyncSession,
    plan: MembershipPlan,
    community: Community,
    org: Organization,
    user_id: int,
    status: str,
    subscription_id: str,
    provider: str,
    expires_date: Optional[str] = None,
    trial_end_date: Optional[str] = None,
) -> CommunityMember:
    # TOCTOU note: Two concurrent webhooks for the same subscription_id
    # can race between the find and the create. The IntegrityError catch
    # below handles the loser of the race.
    member = await find_member_by_subscription(db_session, subscription_id)
    now = _now_iso()
    if member:
        member.status = status
        member.expires_date = expires_date or member.expires_date
        member.trial_end_date = trial_end_date or member.trial_end_date
        member.update_date = now
        db_session.add(member)
        await db_session.commit()
        await db_session.refresh(member)
    else:
        try:
            member = await create_member(
                db_session=db_session,
                plan=plan,
                community=community,
                org=org,
                user_id=user_id,
                status=status,
                subscription_id=subscription_id,
                provider=provider,
                expires_date=expires_date,
                trial_end_date=trial_end_date,
            )
        except IntegrityError:
            await db_session.rollback()
            member = await find_member_by_subscription(db_session, subscription_id)
            if member:
                member.status = status
                member.expires_date = expires_date or member.expires_date
                member.trial_end_date = trial_end_date or member.trial_end_date
                member.update_date = now
                db_session.add(member)
                await db_session.commit()
                await db_session.refresh(member)
            else:
                raise
    return member


async def find_or_create_pending_member(
    db_session: AsyncSession,
    plan: MembershipPlan,
    community: Community,
    org: Organization,
    user_id: int,
    provider: str,
) -> CommunityMember:
    existing = (
        await db_session.execute(
            select(CommunityMember).where(
                CommunityMember.community_id == community.id,
                CommunityMember.user_id == user_id,
                CommunityMember.plan_id == plan.id,
                CommunityMember.status == "pending",
            )
        )
    ).scalars().first()
    if existing:
        return existing
    return await create_member(
        db_session=db_session,
        plan=plan,
        community=community,
        org=org,
        user_id=user_id,
        status="pending",
        provider=provider,
    )


# ── Status transitions ────────────────────────────────────────────────────


MAP_STRIPE_SUB_STATUS: Dict[str, str] = {
    "trialing": "trial",
    "active": "active",
    "past_due": "past_due",
    "canceled": "cancelled",
    "unpaid": "past_due",
    "incomplete": "pending",
    "incomplete_expired": "expired",
}


async def apply_subscription_status(
    db_session: AsyncSession,
    member: CommunityMember,
    plan: MembershipPlan,
    org: Organization,
    stripe_status: str,
    cancel_at_period_end: bool = False,
    current_period_end: Optional[int] = None,
    trial_end: Optional[int] = None,
) -> None:
    local_status = MAP_STRIPE_SUB_STATUS.get(stripe_status, "active")

    expires_date = None
    if current_period_end:
        expires_date = datetime.fromtimestamp(current_period_end, tz=timezone.utc).isoformat()

    trial_end_date = None
    if trial_end:
        trial_end_date = datetime.fromtimestamp(trial_end, tz=timezone.utc).isoformat()

    member.status = local_status
    member.expires_date = expires_date or member.expires_date
    member.trial_end_date = trial_end_date or member.trial_end_date
    member.update_date = _now_iso()

    if cancel_at_period_end and local_status == "active":
        member.status = "active"

    db_session.add(member)
    await db_session.commit()

    active_states = {"trial", "active"}
    inactive_states = {"cancelled", "expired", "past_due"}

    if local_status in active_states:
        await add_member_to_usergroup(db_session, plan, member.user_id, org.id)
    elif local_status in inactive_states:
        await remove_member_from_usergroup(db_session, plan, member.user_id)


async def lookup_subscription_dependencies(
    db_session: AsyncSession,
    subscription_data: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
) -> tuple:
    meta = metadata or subscription_data.get("metadata", {}) or {}
    plan_uuid = meta.get("plan_uuid")
    community_id = meta.get("community_id")

    subscription_id = subscription_data.get("id")

    if not plan_uuid:
        plan_uuid = meta.get("plan_uuid")
    if not community_id:
        community_id = meta.get("community_id")

    plan = None
    if subscription_data.get("plan_id"):
        plan = (
            await db_session.execute(
                select(MembershipPlan).where(
                    MembershipPlan.billing_provider_plan_id == subscription_data["plan_id"]
                )
            )
        ).scalars().first()

    if not plan and plan_uuid:
        plan = (
            await db_session.execute(
                select(MembershipPlan).where(MembershipPlan.plan_uuid == plan_uuid)
            )
        ).scalars().first()

    if not plan:
        return None, None, None, None

    community = (
        await db_session.execute(
            select(Community).where(Community.id == plan.community_id)
        )
    ).scalars().first()
    if not community:
        return None, None, None, None

    org = (
        await db_session.execute(
            select(Organization).where(Organization.id == community.org_id)
        )
    ).scalars().first()
    if not org:
        return None, None, None, None

    return plan, community, org, subscription_id


async def get_provider_subscription(
    provider: BillingProvider,
    subscription_id: str,
) -> Optional[BillingSubscription]:
    try:
        return await provider.get_subscription(subscription_id)
    except Exception:
        return None
