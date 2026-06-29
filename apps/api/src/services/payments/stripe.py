"""
Stripe billing service.

Coordinates between the StripeBillingProvider (raw Stripe API) and the
LearnHouse membership/subscription models. Uses the lifecycle service
for status transitions and usergroup management.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from config.config import get_learnhouse_config
from src.billing.base import BillingPlan, BillingCustomer, BillingProviderError
from src.billing.providers.stripe import StripeBillingProvider
from src.db.communities.membership_plans import MembershipPlan
from src.db.organizations import Organization
from src.services.payments.lifecycle import (
    find_member_by_subscription,
    upsert_member,
    apply_subscription_status,
    add_member_to_usergroup,
    remove_member_from_usergroup,
    lookup_subscription_dependencies,
)

logger = logging.getLogger(__name__)


def _get_stripe_provider() -> StripeBillingProvider:
    cfg = get_learnhouse_config()
    stripe_cfg = cfg.payments_config.stripe
    return StripeBillingProvider({
        "api_key": stripe_cfg.stripe_secret_key or "",
        "webhook_secret": stripe_cfg.stripe_webhook_standard_secret or "",
        "connect_webhook_secret": stripe_cfg.stripe_webhook_connect_secret or "",
    })


async def sync_plan_with_provider(
    db_session: AsyncSession,
    plan: MembershipPlan,
) -> MembershipPlan:
    """Sync a local MembershipPlan with a Stripe product + price.

    Creates a new Stripe price (and product if needed) when ``plan`` has no
    ``billing_provider_plan_id``.  Updates the existing Stripe price when the
    ID is already set.  Raises ``ValueError`` on Stripe API failures so the
    caller can surface the error to the operator.
    """
    provider = _get_stripe_provider()
    billing_plan = BillingPlan(
        provider_plan_id=plan.billing_provider_plan_id or "",
        name=plan.name,
        description=plan.description,
        amount=plan.price,
        currency=plan.currency,
        interval=plan.interval,
        trial_days=plan.trial_days,
        metadata={"plan_uuid": plan.plan_uuid, "community_id": str(plan.community_id)},
    )

    if plan.billing_provider_plan_id:
        try:
            await provider.update_plan(plan.billing_provider_plan_id, billing_plan)
        except BillingProviderError as e:
            logger.error("Failed to update Stripe plan %s: %s", plan.billing_provider_plan_id, e)
            raise ValueError(f"Failed to update Stripe plan: {e}") from e
    else:
        try:
            result = await provider.create_plan(billing_plan)
        except BillingProviderError as e:
            logger.error("Failed to create Stripe plan for %s: %s", plan.name, e)
            raise ValueError(f"Failed to create Stripe plan: {e}") from e

        plan.billing_provider_plan_id = result.provider_plan_id
        plan.billing_provider = "stripe"
        db_session.add(plan)
        await db_session.commit()
        await db_session.refresh(plan)
    return plan


async def cancel_plan_with_provider(plan: MembershipPlan) -> None:
    if plan.billing_provider_plan_id:
        provider = _get_stripe_provider()
        await provider.delete_plan(plan.billing_provider_plan_id)


async def create_checkout_session(
    plan: MembershipPlan,
    customer_email: str,
    success_url: str,
    cancel_url: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    if not plan.billing_provider_plan_id:
        raise ValueError("Plan has no billing provider plan ID")
    provider = _get_stripe_provider()
    cust = await provider.create_customer(
        BillingCustomer(
            provider_customer_id="",
            email=customer_email,
            name=metadata.get("customer_name") if metadata else None,
            metadata=metadata,
        )
    )
    return await provider.create_checkout_session(
        provider_customer_id=cust.provider_customer_id,
        provider_plan_id=plan.billing_provider_plan_id,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "plan_uuid": plan.plan_uuid,
            "community_id": str(plan.community_id),
            **(metadata or {}),
        },
    )


# ── Webhook handlers ──────────────────────────────────────────────────────


async def handle_checkout_completed(
    db_session: AsyncSession,
    session_data: Dict[str, Any],
) -> None:
    metadata = session_data.get("metadata", {}) or {}
    subscription_id = session_data.get("subscription")
    if not subscription_id:
        return

    plan, community, org, _ = await lookup_subscription_dependencies(
        db_session, session_data, metadata
    )
    if not plan or not community or not org:
        return

    # Verify price ID alignment: the Stripe price used in this checkout
    # should match the local plan's billing_provider_plan_id. If the
    # subscription references a different price, update the local plan
    # so the IDs stay synchronized.
    line_items = session_data.get("line_items", {}) or {}
    stripe_price_id = line_items.get("price") or (
        session_data.get("amount_total") and plan.billing_provider_plan_id
    )
    if (
        plan.billing_provider_plan_id
        and stripe_price_id
        and stripe_price_id != plan.billing_provider_plan_id
    ):
        logger.info(
            "Price ID mismatch on checkout: subscription uses %s, "
            "local plan %s has %s — updating",
            stripe_price_id, plan.plan_uuid, plan.billing_provider_plan_id,
        )
        plan.billing_provider_plan_id = stripe_price_id
        db_session.add(plan)
        await db_session.commit()

    user_id_str = metadata.get("user_id")
    if not user_id_str:
        return
    user_id = int(user_id_str)

    sub_data = session_data.get("subscription_data") or {}

    trial_end = None
    expires = None
    if sub_data:
        trial_end = sub_data.get("trial_end")
        current_period_end = sub_data.get("current_period_end")
        if current_period_end:
            expires = datetime.fromtimestamp(current_period_end, tz=timezone.utc).isoformat()
        if trial_end:
            trial_end = datetime.fromtimestamp(trial_end, tz=timezone.utc).isoformat()

    member = await find_member_by_subscription(db_session, subscription_id)
    if member:
        member.status = "trial" if trial_end else "active"
        member.billing_provider_subscription_id = subscription_id
        member.billing_provider = "stripe"
        member.expires_date = expires
        member.trial_end_date = trial_end
        db_session.add(member)
        await db_session.commit()
    else:
        member = await upsert_member(
            db_session=db_session,
            plan=plan,
            community=community,
            org=org,
            user_id=user_id,
            status="trial" if trial_end else "active",
            subscription_id=subscription_id,
            provider="stripe",
            expires_date=expires,
            trial_end_date=trial_end,
        )

    await add_member_to_usergroup(db_session, plan, user_id, org.id)


async def _sync_price_id_on_subscription_change(
    db_session: AsyncSession,
    subscription_data: Dict[str, Any],
    plan: MembershipPlan,
) -> None:
    """Update ``plan.billing_provider_plan_id`` if the Stripe subscription
    references a different price than the local plan record.

    This keeps IDs synchronized when a subscription is upgraded/downgraded
    on the Stripe side (e.g. via the Stripe customer portal).
    """
    items = subscription_data.get("items", {}) or {}
    data_list = items.get("data") if isinstance(items, dict) else items
    if not data_list or not isinstance(data_list, list):
        return

    for item in data_list:
        price_id = (item.get("price") or {}).get("id")
        if price_id and plan.billing_provider_plan_id and price_id != plan.billing_provider_plan_id:
            logger.info(
                "Price ID changed on subscription %s: from %s to %s — updating plan %s",
                subscription_data.get("id"),
                plan.billing_provider_plan_id, price_id, plan.plan_uuid,
            )
            plan.billing_provider_plan_id = price_id
            db_session.add(plan)
            await db_session.commit()
            return


async def handle_subscription_updated(
    db_session: AsyncSession,
    subscription_data: Dict[str, Any],
) -> None:
    provider_subscription_id = subscription_data.get("id")
    if not provider_subscription_id:
        return

    member = await find_member_by_subscription(db_session, provider_subscription_id)
    if not member:
        return

    plan = (
        await db_session.execute(
            select(MembershipPlan).where(MembershipPlan.id == member.plan_id)
        )
    ).scalars().first()
    if not plan:
        return

    org = (
        await db_session.execute(
            select(Organization).where(Organization.id == member.org_id)
        )
    ).scalars().first()
    if not org:
        return

    # Keep price IDs synchronized on plan changes
    await _sync_price_id_on_subscription_change(db_session, subscription_data, plan)

    stripe_status = subscription_data.get("status", "active")
    cancel_at_period_end = subscription_data.get("cancel_at_period_end", False)
    current_period_end = subscription_data.get("current_period_end")
    trial_end = subscription_data.get("trial_end")

    await apply_subscription_status(
        db_session=db_session,
        member=member,
        plan=plan,
        org=org,
        stripe_status=stripe_status,
        cancel_at_period_end=cancel_at_period_end,
        current_period_end=current_period_end,
        trial_end=trial_end,
    )


async def handle_subscription_deleted(
    db_session: AsyncSession,
    subscription_data: Dict[str, Any],
) -> None:
    provider_subscription_id = subscription_data.get("id")
    if not provider_subscription_id:
        return

    member = await find_member_by_subscription(db_session, provider_subscription_id)
    if not member:
        return

    plan = (
        await db_session.execute(
            select(MembershipPlan).where(MembershipPlan.id == member.plan_id)
        )
    ).scalars().first()

    member.status = "cancelled"
    member.update_date = datetime.now(timezone.utc).isoformat()
    db_session.add(member)
    await db_session.commit()

    if plan:
        await remove_member_from_usergroup(db_session, plan, member.user_id)
