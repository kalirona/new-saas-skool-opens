"""
Creator Billing Dashboard & Member Billing endpoints (TASKS 5, 7).

Provides:
- Creator dashboard metrics (revenue, subscribers, MRR, churn, recent payments)
- Member subscription management (view, upgrade, downgrade, cancel, invoices)
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, func
from src.core.events.database import get_db_session
from src.db.users import PublicUser
from src.db.communities.membership_plans import MembershipPlan
from src.db.communities.community_members import CommunityMember
from src.db.communities.communities import Community
from src.db.organizations import Organization
from src.db.payments import Payment, PaymentRead
from src.security.auth import get_current_user
from src.security.rbac import authorization_verify_based_on_org_admin_status
from src.services.payments.lifecycle import (
    add_member_to_usergroup,
    remove_member_from_usergroup,
)


router = APIRouter()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── TASK 5: Creator Billing Dashboard ─────────────────────────────────────


@router.get(
    "/payments/{org_id}/dashboard",
    summary="Creator billing dashboard metrics",
)
async def api_billing_dashboard(
    request: Request,
    org_id: int,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    is_admin = await authorization_verify_based_on_org_admin_status(
        request, current_user.id, "read", org_id, db_session
    )
    if not is_admin:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    org = (
        await db_session.execute(select(Organization).where(Organization.id == org_id))
    ).scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # All communities for this org
    communities = (
        await db_session.execute(
            select(Community).where(Community.org_id == org_id)
        )
    ).scalars().all()
    community_ids = [c.id for c in communities]

    if not community_ids:
        return {
            "total_revenue": 0.0,
            "active_subscribers": 0,
            "mrr": 0.0,
            "churn_rate": 0.0,
            "recent_payments": [],
            "total_members": 0,
            "community_count": 0,
        }

    # Active subscribers (trial + active)
    active_count = (
        await db_session.execute(
            select(func.count(CommunityMember.id)).where(
                CommunityMember.org_id == org_id,
                CommunityMember.status.in_(["active", "trial"]),
            )
        )
    ).scalar() or 0

    # Total revenue from payments
    total_result = await db_session.execute(
        select(func.coalesce(func.sum(Payment.amount), 0.0)).where(
            Payment.org_id == org_id,
            Payment.status == "succeeded",
        )
    )
    total_revenue = float(total_result.scalar() or 0.0)

    # MRR: sum of active subscription plan prices
    active_members = (
        await db_session.execute(
            select(CommunityMember).where(
                CommunityMember.org_id == org_id,
                CommunityMember.status.in_(["active", "trial"]),
            )
        )
    ).scalars().all()

    plan_ids = list(set(m.plan_id for m in active_members if m.plan_id))
    mrr = 0.0
    if plan_ids:
        plans = (
            await db_session.execute(
                select(MembershipPlan).where(MembershipPlan.id.in_(plan_ids))
            )
        ).scalars().all()
        plan_map = {p.id: p for p in plans}
        for m in active_members:
            p = plan_map.get(m.plan_id)
            if p and p.interval == "monthly":
                mrr += p.price
            elif p and p.interval == "yearly":
                mrr += p.price / 12

    # Churn: cancelled / (active + cancelled) over last 30 days
    cancelled_30d = (
        await db_session.execute(
            select(func.count(CommunityMember.id)).where(
                CommunityMember.org_id == org_id,
                CommunityMember.status == "cancelled",
            )
        )
    ).scalar() or 0

    total_members = (
        await db_session.execute(
            select(func.count(CommunityMember.id)).where(
                CommunityMember.org_id == org_id,
            )
        )
    ).scalar() or 0

    churn_rate = 0.0
    if total_members > 0:
        churn_rate = round(cancelled_30d / total_members * 100, 2)

    # Recent payments (last 20)
    recent_payments_raw = (
        await db_session.execute(
            select(Payment)
            .where(Payment.org_id == org_id)
            .order_by(Payment.created_at.desc())
            .limit(20)
        )
    ).scalars().all()

    recent_payments = [
        PaymentRead(
            id=p.id,
            amount=p.amount,
            currency=p.currency,
            status=p.status,
            provider=p.provider,
            provider_payment_id=p.provider_payment_id,
            provider_invoice_id=p.provider_invoice_id,
            billing_period_start=p.billing_period_start,
            billing_period_end=p.billing_period_end,
            invoice_url=p.invoice_url,
            invoice_pdf=p.invoice_pdf,
            created_at=p.created_at,
        ).model_dump()
        for p in recent_payments_raw
    ]

    return {
        "total_revenue": round(total_revenue, 2),
        "active_subscribers": active_count,
        "mrr": round(mrr, 2),
        "churn_rate": churn_rate,
        "recent_payments": recent_payments,
        "total_members": total_members,
        "community_count": len(community_ids),
    }


# ── TASK 7: Member Billing — My Subscription ──────────────────────────────


@router.get(
    "/payments/subscription/me",
    summary="Get current user's subscription details",
)
async def api_my_subscription(
    request: Request,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    subscriptions = (
        await db_session.execute(
            select(CommunityMember)
            .where(
                CommunityMember.user_id == current_user.id,
                CommunityMember.status.in_(["active", "trial", "past_due", "pending"]),
            )
            .order_by(CommunityMember.creation_date.desc())
        )
    ).scalars().all()

    results = []
    for sub in subscriptions:
        plan = (
            await db_session.execute(
                select(MembershipPlan).where(MembershipPlan.id == sub.plan_id)
            )
        ).scalars().first()
        community = (
            await db_session.execute(
                select(Community).where(Community.id == sub.community_id)
            )
        ).scalars().first()

        available_plans = []
        if community:
            all_plans = (
                await db_session.execute(
                    select(MembershipPlan).where(
                        MembershipPlan.community_id == community.id,
                        MembershipPlan.status == "active",
                    )
                )
            ).scalars().all()
            available_plans = [
                {
                    "id": p.id,
                    "name": p.name,
                    "price": p.price,
                    "currency": p.currency,
                    "interval": p.interval,
                    "plan_uuid": p.plan_uuid,
                }
                for p in all_plans
            ]

        results.append({
            "id": sub.id,
            "community_id": sub.community_id,
            "community_name": community.name if community else None,
            "plan_id": sub.plan_id,
            "plan_name": plan.name if plan else None,
            "plan_price": plan.price if plan else 0,
            "plan_interval": plan.interval if plan else "",
            "status": sub.status,
            "billing_provider": sub.billing_provider,
            "joined_date": sub.joined_date,
            "expires_date": sub.expires_date,
            "trial_end_date": sub.trial_end_date,
            "cancelled_at": sub.cancelled_at,
            "next_billing_date": sub.next_billing_date,
            "available_plans": available_plans,
        })

    return results


# ── Upgrade / Downgrade Plan ──────────────────────────────────────────────


class ChangePlanRequest(BaseModel):
    subscription_id: int
    new_plan_id: int


@router.post(
    "/payments/subscription/change",
    summary="Upgrade or downgrade subscription plan",
)
async def api_change_subscription_plan(
    request: Request,
    body: ChangePlanRequest,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    member = (
        await db_session.execute(
            select(CommunityMember).where(
                CommunityMember.id == body.subscription_id,
                CommunityMember.user_id == current_user.id,
            )
        )
    ).scalars().first()
    if not member:
        raise HTTPException(status_code=404, detail="Subscription not found")

    new_plan = (
        await db_session.execute(
            select(MembershipPlan).where(MembershipPlan.id == body.new_plan_id)
        )
    ).scalars().first()
    if not new_plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Verify same community
    if new_plan.community_id != member.community_id:
        raise HTTPException(status_code=400, detail="Plan does not belong to the same community")

    community = (
        await db_session.execute(
            select(Community).where(Community.id == member.community_id)
        )
    ).scalars().first()

    old_plan = (
        await db_session.execute(
            select(MembershipPlan).where(MembershipPlan.id == member.plan_id)
        )
    ).scalars().first()

    member.plan_id = new_plan.id
    member.update_date = _now()
    db_session.add(member)

    # Update usergroup membership if plans have different usergroups
    if old_plan and old_plan.usergroup_id and old_plan.usergroup_id != new_plan.usergroup_id:
        await remove_member_from_usergroup(db_session, old_plan, member.user_id)

    if new_plan.usergroup_id:
        org = (
            await db_session.execute(
                select(Organization).where(Organization.id == member.org_id)
            )
        ).scalars().first()
        if org:
            await add_member_to_usergroup(db_session, new_plan, member.user_id, org.id)

    await db_session.commit()
    await db_session.refresh(member)

    return {
        "id": member.id,
        "status": member.status,
        "plan_id": member.plan_id,
        "plan_name": new_plan.name,
        "update_date": member.update_date,
    }


# ── Cancel Subscription ──────────────────────────────────────────────────


@router.post(
    "/payments/subscription/cancel",
    summary="Cancel active subscription",
)
async def api_cancel_subscription(
    request: Request,
    body: dict,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    subscription_id = body.get("subscription_id")
    if not subscription_id:
        raise HTTPException(status_code=400, detail="subscription_id required")

    member = (
        await db_session.execute(
            select(CommunityMember).where(
                CommunityMember.id == subscription_id,
                CommunityMember.user_id == current_user.id,
            )
        )
    ).scalars().first()
    if not member:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if member.status not in ("active", "trial", "past_due"):
        raise HTTPException(status_code=400, detail="Subscription is not active")

    member.status = "cancelled"
    member.cancelled_at = _now()
    member.update_date = _now()
    db_session.add(member)
    await db_session.commit()

    plan = (
        await db_session.execute(
            select(MembershipPlan).where(MembershipPlan.id == member.plan_id)
        )
    ).scalars().first()

    if plan:
        await remove_member_from_usergroup(db_session, plan, member.user_id)

    return {
        "id": member.id,
        "status": "cancelled",
        "cancelled_at": member.cancelled_at,
    }


# ── Invoices ──────────────────────────────────────────────────────────────


@router.get(
    "/payments/subscription/invoices",
    summary="List invoices for current user",
)
async def api_my_invoices(
    request: Request,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    payments = (
        await db_session.execute(
            select(Payment)
            .where(Payment.user_id == current_user.id)
            .order_by(Payment.created_at.desc())
            .limit(50)
        )
    ).scalars().all()

    return [
        PaymentRead(
            id=p.id,
            amount=p.amount,
            currency=p.currency,
            status=p.status,
            provider=p.provider,
            provider_payment_id=p.provider_payment_id,
            provider_invoice_id=p.provider_invoice_id,
            billing_period_start=p.billing_period_start,
            billing_period_end=p.billing_period_end,
            invoice_url=p.invoice_url,
            invoice_pdf=p.invoice_pdf,
            created_at=p.created_at,
        ).model_dump()
        for p in payments
    ]
