"""
PayPal billing service — bridges between LearnHouse models and PayPalBillingProvider.
"""

from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from config.config import get_learnhouse_config
from src.billing.base import BillingPlan
from src.billing.providers.paypal import PayPalBillingProvider
from src.db.communities.membership_plans import MembershipPlan


def _get_paypal_provider() -> PayPalBillingProvider:
    cfg = get_learnhouse_config()
    pp_cfg = cfg.payments_config.paypal
    return PayPalBillingProvider({
        "client_id": pp_cfg.paypal_client_id or "",
        "client_secret": pp_cfg.paypal_client_secret or "",
        "webhook_id": pp_cfg.paypal_webhook_id or "",
        "sandbox": pp_cfg.paypal_sandbox,
    })


async def sync_plan_with_provider(
    db_session: AsyncSession,
    plan: MembershipPlan,
) -> MembershipPlan:
    provider = _get_paypal_provider()

    bp = BillingPlan(
        provider_plan_id=plan.billing_provider_plan_id or "",
        name=plan.name,
        description=plan.description or "",
        amount=float(plan.price),
        currency=plan.currency or "USD",
        interval=plan.interval or "monthly",
        trial_days=plan.trial_days or 0,
        metadata={"plan_uuid": plan.plan_uuid},
    )

    if plan.billing_provider_plan_id:
        await provider.update_plan(plan.billing_provider_plan_id, bp)
    else:
        result = await provider.create_plan(bp)
        plan.billing_provider = "paypal"
        plan.billing_provider_plan_id = result.provider_plan_id
        db_session.add(plan)
        await db_session.commit()
        await db_session.refresh(plan)

    return plan
