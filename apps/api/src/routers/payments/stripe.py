"""
Stripe billing API router.

Provides endpoints for:
- Stripe Connect account onboarding (Express)
- Checkout session creation
- Webhook handling
- Plan syncing with Stripe
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from config.config import get_learnhouse_config
from src.core.events.database import get_db_session
from src.db.users import PublicUser
from src.db.communities.membership_plans import MembershipPlan, MembershipPlanRead
from src.db.communities.communities import Community
from src.db.organizations import Organization
from src.db.payments import WebhookEventLog, Payment
from src.security.auth import get_current_user
from src.security.rbac import authorization_verify_based_on_org_admin_status
from src.services.payments.stripe import (
    sync_plan_with_provider,
    cancel_plan_with_provider,
    create_checkout_session,
    handle_subscription_updated,
    handle_subscription_deleted,
    handle_checkout_completed,
)
from src.services.payments.lifecycle import find_or_create_pending_member, find_member_by_subscription
from src.billing.providers.stripe import StripeBillingProvider
from src.billing.base import BillingProviderError


router = APIRouter()


def _get_stripe_provider(request: Request) -> StripeBillingProvider:
    """Create a Stripe provider instance from config."""
    cfg = get_learnhouse_config()
    stripe_cfg = cfg.payments_config.stripe
    return StripeBillingProvider({
        "api_key": stripe_cfg.stripe_secret_key or "",
        "webhook_secret": stripe_cfg.stripe_webhook_standard_secret or "",
        "connect_webhook_secret": stripe_cfg.stripe_webhook_connect_secret or "",
    })


# ── Plan Sync ─────────────────────────────────────────────────────────────


class SyncPlanRequest(BaseModel):
    plan_uuid: str


@router.post(
    "/payments/plans/sync",
    response_model=MembershipPlanRead,
    summary="Sync a membership plan with Stripe",
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

    plan = await sync_plan_with_provider(db_session, plan)
    return MembershipPlanRead.model_validate(plan.model_dump())


# ── Checkout Session ──────────────────────────────────────────────────────


class CreateCheckoutRequest(BaseModel):
    plan_uuid: str
    success_url: str
    cancel_url: str
    metadata: Optional[Dict[str, Any]] = None


@router.post(
    "/payments/checkout",
    summary="Create a Stripe Checkout Session for a plan",
)
async def api_create_checkout_session(
    request: Request,
    body: CreateCheckoutRequest,
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
        provider="stripe",
    )

    url = await create_checkout_session(
        plan=plan,
        customer_email=current_user.email,
        success_url=body.success_url,
        cancel_url=body.cancel_url,
        metadata={
            "customer_name": f"{current_user.first_name} {current_user.last_name}".strip(),
            "user_id": str(current_user.id),
            "community_id": str(plan.community_id),
            "pending_member_id": str(pending.id),
            **(body.metadata or {}),
        },
    )
    return {"url": url, "member_id": pending.id}


# ── Stripe Connect Onboarding (Express) ──────────────────────────────────


class ConnectOnboardingRequest(BaseModel):
    refresh_url: str
    return_url: str


@router.post(
    "/payments/{org_id}/stripe/express/connect/link",
    summary="Get Stripe Express onboarding link",
)
async def api_get_express_onboarding_link(
    request: Request,
    org_id: int,
    body: ConnectOnboardingRequest,
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

    provider = _get_stripe_provider(request)

    if org.stripe_connect_account_id:
        link = await provider.create_connect_onboarding_link(
            org.stripe_connect_account_id,
            refresh_url=body.refresh_url,
            return_url=body.return_url,
        )
        return {"url": link}

    account_id = await provider.create_connect_account(
        email=current_user.email,
    )
    org.stripe_connect_account_id = account_id
    db_session.add(org)
    await db_session.commit()

    link = await provider.create_connect_onboarding_link(
        account_id,
        refresh_url=body.refresh_url,
        return_url=body.return_url,
    )
    return {"url": link}


@router.post(
    "/payments/{org_id}/stripe/express/connect/refresh",
    summary="Refresh Stripe Express onboarding link",
)
async def api_refresh_express_onboarding_link(
    request: Request,
    org_id: int,
    body: ConnectOnboardingRequest,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    org = (
        await db_session.execute(select(Organization).where(Organization.id == org_id))
    ).scalars().first()
    if not org or not org.stripe_connect_account_id:
        raise HTTPException(status_code=404, detail="No connected Stripe account")

    provider = _get_stripe_provider(request)
    link = await provider.create_connect_onboarding_link(
        org.stripe_connect_account_id,
        refresh_url=body.refresh_url,
        return_url=body.return_url,
    )
    return {"url": link}


@router.get(
    "/payments/{org_id}/stripe/express/dashboard",
    summary="Get Stripe Express dashboard URL",
)
async def api_get_express_dashboard_link(
    request: Request,
    org_id: int,
    current_user: PublicUser = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    org = (
        await db_session.execute(select(Organization).where(Organization.id == org_id))
    ).scalars().first()
    if not org or not org.stripe_connect_account_id:
        raise HTTPException(status_code=404, detail="No connected Stripe account")

    provider = _get_stripe_provider(request)
    url = await provider.create_connect_dashboard_link(org.stripe_connect_account_id)
    return {"url": url}


# ── Webhooks ──────────────────────────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _log_webhook_event(
    db_session: AsyncSession,
    provider: str,
    event_id: str,
    event_type: str,
    raw_body: str,
    status: str = "received",
    error_message: Optional[str] = None,
) -> WebhookEventLog:
    log = WebhookEventLog(
        provider=provider,
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


async def _update_webhook_log(
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


async def _check_idempotency(
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


async def _record_payment_from_checkout(
    db_session: AsyncSession,
    session_data: Dict[str, Any],
) -> None:
    metadata = session_data.get("metadata", {}) or {}
    plan_uuid = metadata.get("plan_uuid")
    community_id_str = metadata.get("community_id")
    user_id_str = metadata.get("user_id")

    if not plan_uuid or not community_id_str:
        return

    plan = (
        await db_session.execute(
            select(MembershipPlan).where(MembershipPlan.plan_uuid == plan_uuid)
        )
    ).scalars().first()
    if not plan:
        return

    community = (
        await db_session.execute(
            select(Community).where(Community.id == plan.community_id)
        )
    ).scalars().first()
    if not community:
        return

    org = (
        await db_session.execute(
            select(Organization).where(Organization.id == community.org_id)
        )
    ).scalars().first()
    if not org:
        return

    user_id = int(user_id_str) if user_id_str else 0

    subscription_id = session_data.get("subscription", "")
    member = None
    if subscription_id:
        member = await find_member_by_subscription(db_session, subscription_id)

    amount = 0.0
    amount_total = session_data.get("amount_total")
    if amount_total:
        amount = amount_total / 100.0

    currency = session_data.get("currency", "usd")

    provider_payment_id = session_data.get("payment_intent", "") or session_data.get("id", "")

    existing_payment = None
    if provider_payment_id:
        existing_payment = (
            await db_session.execute(
                select(Payment).where(Payment.provider_payment_id == provider_payment_id)
            )
        ).scalars().first()

    if existing_payment:
        return

    payment = Payment(
        org_id=org.id,
        community_id=community.id,
        member_id=member.id if member else None,
        user_id=user_id,
        plan_id=plan.id,
        provider="stripe",
        provider_payment_id=provider_payment_id,
        provider_invoice_id=session_data.get("invoice", None),
        amount=amount,
        currency=currency,
        status="succeeded",
        created_at=_now_iso(),
        updated_at=_now_iso(),
    )
    db_session.add(payment)
    await db_session.commit()


@router.post(
    "/payments/stripe/webhook/standard",
    summary="Stripe standard webhook endpoint",
)
async def api_stripe_standard_webhook(
    request: Request,
    db_session: AsyncSession = Depends(get_db_session),
):
    raw_body_bytes = await request.body()
    raw_body = raw_body_bytes.decode("utf-8")
    signature = request.headers.get("stripe-signature")

    provider = _get_stripe_provider(request)
    event = await provider.handle_webhook(raw_body_bytes, signature)

    event_type = event.get("event_type", "")
    event_id = event.get("event_id", "")
    data = event.get("data", {})

    if await _check_idempotency(db_session, event_id):
        return {"received": True, "event_type": event_type, "idempotent": True}

    log = await _log_webhook_event(
        db_session=db_session,
        provider="stripe",
        event_id=event_id,
        event_type=event_type,
        raw_body=raw_body,
        status="received",
    )

    try:
        if event_type == "checkout.session.completed":
            await handle_checkout_completed(db_session, data)
            await _record_payment_from_checkout(db_session, data)

        elif event_type in (
            "customer.subscription.updated",
            "customer.subscription.created",
        ):
            await handle_subscription_updated(db_session, data)

        elif event_type == "customer.subscription.deleted":
            await handle_subscription_deleted(db_session, data)

        elif event_type == "invoice.payment_succeeded":
            await _record_payment_from_checkout(db_session, data)

        elif event_type == "invoice.payment_failed":
            subscription_id = data.get("subscription")
            if subscription_id:
                member = await find_member_by_subscription(db_session, subscription_id)
                if member:
                    member.status = "past_due"
                    member.update_date = _now_iso()
                    db_session.add(member)
                    await db_session.commit()

        await _update_webhook_log(db_session, log.id, "processed")

    except Exception as e:
        await _update_webhook_log(db_session, log.id, "failed", str(e))
        raise

    return {"received": True, "event_type": event_type}


@router.post(
    "/payments/stripe/webhook/connect",
    summary="Stripe Connect webhook endpoint",
)
async def api_stripe_connect_webhook(
    request: Request,
    db_session: AsyncSession = Depends(get_db_session),
):
    raw_body = await request.body()
    signature = request.headers.get("stripe-signature")

    cfg = get_learnhouse_config()
    provider = StripeBillingProvider({
        "api_key": cfg.payments_config.stripe.stripe_secret_key or "",
        "webhook_secret": cfg.payments_config.stripe.stripe_webhook_connect_secret or "",
    })
    event = await provider.handle_webhook(raw_body, signature)

    event_type = event.get("event_type", "")
    data = event.get("data", {})

    if event_type == "account.updated":
        account_id = data.get("id")
        if account_id:
            org = (
                await db_session.execute(
                    select(Organization).where(
                        Organization.stripe_connect_account_id == account_id
                    )
                )
            ).scalars().first()
            if org:
                charges_enabled = data.get("charges_enabled", False)
                details_submitted = data.get("details_submitted", False)
                if details_submitted and charges_enabled:
                    from src.services.orgs.orgs import update_org_payments_config
                    await update_org_payments_config(
                        request, True, org.id, None, db_session
                    )

    return {"received": True, "event_type": event_type}


# ── Stripe Overview (for dashboard) ──────────────────────────────────────


@router.get(
    "/payments/{org_id}/stripe/overview",
    summary="Get Stripe account overview",
)
async def api_stripe_overview(
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
        "connected": bool(org.stripe_connect_account_id),
        "connect_account_id": org.stripe_connect_account_id,
        "payments_enabled": True,
    }


@router.get(
    "/payments/{org_id}/config",
    summary="Get payment config for an org",
)
async def api_get_payment_config(
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

    return {
        "org_id": org.id,
        "connected": bool(org.stripe_connect_account_id),
        "connect_account_id": org.stripe_connect_account_id,
    }
