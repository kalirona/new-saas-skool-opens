"""
PayPal billing API router.

Provides endpoints for:
- PayPal merchant onboarding
- Checkout / subscription creation
- Webhook handling
- Plan syncing with PayPal
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from config.config import get_learnhouse_config
from src.core.events.database import get_db_session
from src.db.users import PublicUser
from src.db.communities.membership_plans import MembershipPlan, MembershipPlanRead
from src.db.communities.communities import Community
from src.db.communities.community_members import CommunityMember
from src.db.organizations import Organization
from src.db.payments import WebhookEventLog
from src.security.auth import get_current_user
from src.security.rbac import authorization_verify_based_on_org_admin_status
from src.billing.providers.paypal import PayPalBillingProvider
from src.billing.base import BillingPlan, BillingProviderError
from src.services.payments.lifecycle import (
    find_member_by_subscription,
    upsert_member,
    find_or_create_pending_member,
    add_member_to_usergroup,
    remove_member_from_usergroup,
    lookup_subscription_dependencies,
)


router = APIRouter()


def _get_paypal_provider(request: Request) -> PayPalBillingProvider:
    cfg = get_learnhouse_config()
    pp_cfg = cfg.payments_config.paypal
    return PayPalBillingProvider({
        "client_id": pp_cfg.paypal_client_id or "",
        "client_secret": pp_cfg.paypal_client_secret or "",
        "webhook_id": pp_cfg.paypal_webhook_id or "",
        "sandbox": pp_cfg.paypal_sandbox,
    })


# ── Plan Sync ─────────────────────────────────────────────────────────────


class SyncPlanRequest(BaseModel):
    plan_uuid: str


@router.post(
    "/payments/paypal/plans/sync",
    response_model=MembershipPlanRead,
    summary="Sync a membership plan with PayPal",
)
async def api_sync_plan(
    request: Request,
    body: SyncPlanRequest,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> MembershipPlanRead:
    plan = (
        await db_session.execute(
            select(MembershipPlan).where(MembershipPlan.plan_uuid == body.plan_uuid)
        )
    ).scalars().first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    community = (
        await db_session.execute(
            select(Community).where(Community.id == plan.community_id)
        )
    ).scalars().first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    org = (
        await db_session.execute(
            select(Organization).where(Organization.id == community.org_id)
        )
    ).scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    is_admin = await authorization_verify_based_on_org_admin_status(
        request, current_user.id, "update", org.org_uuid, db_session
    )
    if not is_admin:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    provider = _get_paypal_provider(request)

    if plan.billing_provider_plan_id:
        bp = BillingPlan(
            provider_plan_id=plan.billing_provider_plan_id,
            name=plan.name,
            description=plan.description,
            amount=float(plan.price),
            currency=plan.currency or "USD",
            interval=plan.interval or "monthly",
            trial_days=plan.trial_days,
            metadata={"plan_uuid": plan.plan_uuid},
        )
        result = await provider.update_plan(plan.billing_provider_plan_id, bp)
    else:
        bp = BillingPlan(
            provider_plan_id="",
            name=plan.name,
            description=plan.description,
            amount=float(plan.price),
            currency=plan.currency or "USD",
            interval=plan.interval or "monthly",
            trial_days=plan.trial_days,
            metadata={"plan_uuid": plan.plan_uuid},
        )
        result = await provider.create_plan(bp)
        plan.billing_provider = "paypal"
        plan.billing_provider_plan_id = result.provider_plan_id

    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)

    return MembershipPlanRead.model_validate(plan.model_dump())


# ── Checkout / Subscribe ──────────────────────────────────────────────────


class CreateSubscriptionRequest(BaseModel):
    plan_uuid: str
    success_url: str
    cancel_url: str


@router.post(
    "/payments/paypal/checkout",
    summary="Create a PayPal subscription for a plan",
)
async def api_create_checkout_session(
    request: Request,
    body: CreateSubscriptionRequest,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    plan = (
        await db_session.execute(
            select(MembershipPlan).where(MembershipPlan.plan_uuid == body.plan_uuid)
        )
    ).scalars().first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    if not plan.billing_provider_plan_id:
        raise HTTPException(status_code=400, detail="Plan not synced with PayPal")

    community = (
        await db_session.execute(
            select(Community).where(Community.id == plan.community_id)
        )
    ).scalars().first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    org = (
        await db_session.execute(
            select(Organization).where(Organization.id == community.org_id)
        )
    ).scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    existing_active = (
        await db_session.execute(
            select(CommunityMember).where(
                CommunityMember.user_id == current_user.id,
                CommunityMember.community_id == community.id,
                CommunityMember.status.in_(["active", "trial", "past_due"]),
            )
        )
    ).scalars().first()
    if existing_active:
        raise HTTPException(
            status_code=409,
            detail="You already have an active subscription for this community",
        )

    pending = await find_or_create_pending_member(
        db_session=db_session,
        plan=plan,
        community=community,
        org=org,
        user_id=current_user.id,
        provider="paypal",
    )

    provider = _get_paypal_provider(request)
    url = await provider.create_checkout_session(
        provider_customer_id="",
        provider_plan_id=plan.billing_provider_plan_id,
        success_url=body.success_url,
        cancel_url=body.cancel_url,
        metadata={
            "email": current_user.email,
            "plan_uuid": plan.plan_uuid,
            "user_id": str(current_user.id),
            "community_id": str(plan.community_id),
            "pending_member_id": str(pending.id),
            "return_url": body.success_url,
            "cancel_url": body.cancel_url,
        },
    )
    return {"url": url, "member_id": pending.id}


# ── Merchant Onboarding ───────────────────────────────────────────────────


class OnboardingRequest(BaseModel):
    return_url: str
    cancel_url: str


class MerchantStatusRequest(BaseModel):
    merchant_id: str
    status: str
    permissions_granted: bool = False
    account_status: str = ""


@router.post(
    "/payments/{org_id}/paypal/merchant/onboarding",
    summary="Initiate PayPal merchant onboarding",
)
async def api_paypal_merchant_onboarding(
    request: Request,
    org_id: int,
    body: OnboardingRequest,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    is_admin = await authorization_verify_based_on_org_admin_status(
        request, current_user.id, "update", org_id, db_session
    )
    if not is_admin:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    org = (
        await db_session.execute(select(Organization).where(Organization.id == org_id))
    ).scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    merchant_id = org.paypal_merchant_id
    if not merchant_id:
        merchant_id = f"org_{org.id}_{org.org_uuid[:8]}"
        org.paypal_merchant_id = merchant_id
        db_session.add(org)
        await db_session.commit()

    return {
        "url": f"https://www.paypal.com/signin/client?merchantId={merchant_id}",
        "merchant_id": merchant_id,
    }


@router.post(
    "/payments/{org_id}/paypal/merchant/status",
    summary="Update PayPal merchant onboarding status",
)
async def api_update_paypal_merchant_status(
    request: Request,
    org_id: int,
    body: MerchantStatusRequest,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    is_admin = await authorization_verify_based_on_org_admin_status(
        request, current_user.id, "update", org_id, db_session
    )
    if not is_admin:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    org = (
        await db_session.execute(select(Organization).where(Organization.id == org_id))
    ).scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    completed = body.get("onboarding_completed", False)
    org.paypal_onboarding_completed = completed
    db_session.add(org)
    await db_session.commit()

    if completed:
        from src.services.orgs.orgs import update_org_payments_config
        await update_org_payments_config(
            request, True, org.id, None, db_session
        )

    return {"onboarding_completed": completed}


# ── Webhooks ──────────────────────────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _log_pp_webhook_event(
    db_session: AsyncSession,
    event_id: str,
    event_type: str,
    raw_body: str,
    status: str = "received",
    error_message: Optional[str] = None,
) -> WebhookEventLog:
    log = WebhookEventLog(
        provider="paypal",
        event_id=event_id,
        event_type=event_type,
        status=status,
        raw_body=raw_body,
        error_message=error_message,
        created_at=_now_iso(),
    )
    db_session.add(log)
    await db_session.commit()
    await db_session.refresh(log)
    return log


async def _update_pp_log(
    db_session: AsyncSession,
    log_id: int,
    status: str,
    error_message: Optional[str] = None,
) -> None:
    log = await db_session.get(WebhookEventLog, log_id)
    if log:
        log.status = status
        log.processed_at = _now_iso()
        if error_message:
            log.error_message = error_message
        db_session.add(log)
        await db_session.commit()


async def _check_pp_idempotency(
    db_session: AsyncSession,
    event_id: str,
) -> bool:
    existing = (
        await db_session.execute(
            select(WebhookEventLog).where(
                WebhookEventLog.event_id == event_id,
                WebhookEventLog.status.in_(["processed", "skipped"]),
            )
        )
    ).scalars().first()
    return existing is not None


import json as _json


_PAYPAL_WEBHOOK_HEADERS = [
    "paypal-auth-algo",
    "paypal-cert-url",
    "paypal-transmission-id",
    "paypal-transmission-sig",
    "paypal-transmission-time",
]


def _extract_paypal_webhook_headers(request: Request) -> Optional[str]:
    """Extract PayPal webhook verification headers and return as JSON string."""
    headers = {}
    for h in _PAYPAL_WEBHOOK_HEADERS:
        value = request.headers.get(h)
        if value:
            key = h.replace("paypal-", "").replace("-", "_")
            headers[key] = value

    if len(headers) < 5:
        return None

    return _json.dumps(headers)


@router.post(
    "/payments/paypal/webhook",
    summary="PayPal webhook endpoint",
)
async def api_paypal_webhook(
    request: Request,
    db_session: AsyncSession = Depends(get_db_session),
):
    raw_body_bytes = await request.body()
    raw_body_str = raw_body_bytes.decode("utf-8")

    webhook_headers_json = _extract_paypal_webhook_headers(request)

    provider = _get_paypal_provider(request)
    try:
        event = await provider.handle_webhook(raw_body_bytes, webhook_headers_json)
    except BillingProviderError as e:
        import logging
        logging.getLogger(__name__).error(
            "PayPal webhook verification failed: %s (code=%s)", e, e.code
        )
        status_code = 400 if e.code in ("webhook_signature_missing", "webhook_signature_invalid") else 500
        raise HTTPException(status_code=status_code, detail=str(e))

    event_type = event.get("event_type", "")
    event_id = event.get("event_id", "")
    data = event.get("data", {})

    if await _check_pp_idempotency(db_session, event_id):
        return {"received": True, "event_type": event_type, "idempotent": True}

    log = await _log_pp_webhook_event(
        db_session, event_id, event_type, raw_body_str
    )

    try:
        if event_type == "checkout.session.completed":
            sub_id = data.get("id")
            plan_provider_id = data.get("plan_id")
            plan = None
            if plan_provider_id:
                plan = (
                    await db_session.execute(
                        select(MembershipPlan).where(
                            MembershipPlan.billing_provider_plan_id == plan_provider_id
                        )
                    )
                ).scalars().first()
            if not plan:
                plan_uuid = data.get("plan_uuid") or (data.get("metadata") or {}).get("plan_uuid")
                if plan_uuid:
                    plan = (
                        await db_session.execute(
                            select(MembershipPlan).where(MembershipPlan.plan_uuid == plan_uuid)
                        )
                    ).scalars().first()
            if not plan or not sub_id:
                await _update_pp_log(db_session, log.id, "skipped", "No plan or subscription ID found")
                return {"received": True, "event_type": event_type}

            community = (
                await db_session.execute(
                    select(Community).where(Community.id == plan.community_id)
                )
            ).scalars().first()
            if not community:
                await _update_pp_log(db_session, log.id, "skipped", "Community not found")
                return {"received": True, "event_type": event_type}

            org = (
                await db_session.execute(
                    select(Organization).where(Organization.id == community.org_id)
                )
            ).scalars().first()
            if not org:
                await _update_pp_log(db_session, log.id, "skipped", "Organization not found")
                return {"received": True, "event_type": event_type}

            user_id_str = (data.get("metadata") or {}).get("user_id")
            user_id = int(user_id_str) if user_id_str else 0

            status = data.get("status", "")
            if status == "ACTIVE":
                local_status = "active"
            elif status == "APPROVAL_PENDING":
                local_status = "pending"
            elif status in ("CANCELLED", "SUSPENDED"):
                local_status = "cancelled"
            elif status == "EXPIRED":
                local_status = "expired"
            else:
                local_status = "pending"

            member = await find_member_by_subscription(db_session, sub_id)
            if member:
                member.status = local_status
                member.billing_provider = "paypal"
                db_session.add(member)
                await db_session.commit()
            else:
                member = await upsert_member(
                    db_session=db_session,
                    plan=plan,
                    community=community,
                    org=org,
                    user_id=user_id,
                    status=local_status,
                    subscription_id=sub_id,
                    provider="paypal",
                )

            if local_status in ("active", "trial"):
                await add_member_to_usergroup(db_session, plan, member.user_id, org.id)
            elif local_status in ("cancelled", "expired"):
                await remove_member_from_usergroup(db_session, plan, member.user_id)

        elif event_type == "customer.subscription.updated":
            sub_id = data.get("id")
            member = await find_member_by_subscription(db_session, sub_id) if sub_id else None
            if not member:
                await _update_pp_log(db_session, log.id, "skipped", "No member found for subscription")
                return {"received": True, "event_type": event_type}

            plan = (
                await db_session.execute(
                    select(MembershipPlan).where(MembershipPlan.id == member.plan_id)
                )
            ).scalars().first()
            if not plan:
                await _update_pp_log(db_session, log.id, "skipped", "Plan not found")
                return {"received": True, "event_type": event_type}

            org = (
                await db_session.execute(
                    select(Organization).where(Organization.id == member.org_id)
                )
            ).scalars().first()
            if not org:
                await _update_pp_log(db_session, log.id, "skipped", "Organization not found")
                return {"received": True, "event_type": event_type}

            status = data.get("status", "")

            if status == "ACTIVE":
                member.status = "active"
            elif status == "CANCELLED":
                member.status = "cancelled"
            elif status == "EXPIRED":
                member.status = "expired"
            elif status == "SUSPENDED":
                member.status = "past_due"

            member.update_date = _now_iso()
            db_session.add(member)
            await db_session.commit()

            if member.status in ("active", "trial"):
                await add_member_to_usergroup(db_session, plan, member.user_id, org.id)
            elif member.status in ("cancelled", "expired", "past_due"):
                await remove_member_from_usergroup(db_session, plan, member.user_id)

        elif event_type == "customer.subscription.deleted":
            sub_id = data.get("id")
            member = await find_member_by_subscription(db_session, sub_id) if sub_id else None
            if not member:
                await _update_pp_log(db_session, log.id, "skipped", "No member found for deleted subscription")
                return {"received": True, "event_type": event_type}

            plan = (
                await db_session.execute(
                    select(MembershipPlan).where(MembershipPlan.id == member.plan_id)
                )
            ).scalars().first()

            member.status = "cancelled"
            member.cancelled_at = _now_iso()
            member.update_date = _now_iso()
            db_session.add(member)
            await db_session.commit()

            if plan:
                await remove_member_from_usergroup(db_session, plan, member.user_id)

        await _update_pp_log(db_session, log.id, "processed")

    except Exception as e:
        await _update_pp_log(db_session, log.id, "failed", str(e))
        raise

    return {"received": True, "event_type": event_type}


# ── Overview ──────────────────────────────────────────────────────────────


@router.get(
    "/payments/{org_id}/paypal/overview",
    summary="Get PayPal account overview",
)
async def api_paypal_overview(
    request: Request,
    org_id: int,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    org = (
        await db_session.execute(select(Organization).where(Organization.id == org_id))
    ).scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    is_admin = await authorization_verify_based_on_org_admin_status(
        request, current_user.id, "read", org.org_uuid, db_session
    )
    if not is_admin:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return {
        "connected": bool(org.paypal_merchant_id),
        "merchant_id": org.paypal_merchant_id,
        "onboarding_completed": org.paypal_onboarding_completed,
        "payments_enabled": True,
    }



