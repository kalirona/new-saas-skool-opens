"""
Stripe billing provider implementation.

Implements the BillingProvider ABC using Stripe's API.
Uses Stripe Connect for marketplace-style payment flows.
"""

from typing import Optional, Dict, Any, List
import stripe
from src.billing.base import (
    BillingProvider,
    BillingPlan,
    BillingCustomer,
    BillingSubscription,
    BillingProviderError,
)
from src.billing.registry import BillingProviderRegistry


class StripeBillingProvider(BillingProvider):
    """Stripe billing integration using the Stripe API."""

    @property
    def provider_name(self) -> str:
        return "stripe"

    def __init__(self, config: dict):
        self.api_key = config.get("api_key", "")
        self.webhook_secret = config.get("webhook_secret", "")
        self.connect_webhook_secret = config.get("connect_webhook_secret", "")
        stripe.api_key = self.api_key

    # ── Plan / Product Management ──────────────────────────────────────────

    async def create_plan(self, plan: BillingPlan) -> BillingPlan:
        try:
            product = stripe.Product.create(name=plan.name, metadata=plan.metadata or {})
            price_data = {
                "product": product.id,
                "currency": plan.currency,
                "unit_amount": int(round(plan.amount * 100)),
            }
            if plan.interval == "one_time":
                price_data["recurring"] = None
            else:
                interval = "month" if plan.interval == "monthly" else "year"
                price_data["recurring"] = {"interval": interval}
                if plan.trial_days > 0:
                    price_data["recurring"]["trial_period_days"] = plan.trial_days

            price = stripe.Price.create(**{k: v for k, v in price_data.items() if v is not None})
            return BillingPlan(
                provider_plan_id=price.id,
                name=plan.name,
                description=plan.description,
                amount=plan.amount,
                currency=plan.currency,
                interval=plan.interval,
                trial_days=plan.trial_days,
                metadata={"product_id": product.id, **plan.metadata} if plan.metadata else {"product_id": product.id},
            )
        except stripe.StripeError as e:
            raise BillingProviderError(str(e), provider="stripe", code=e.code)

    async def update_plan(self, provider_plan_id: str, plan: BillingPlan) -> BillingPlan:
        try:
            price = stripe.Price.retrieve(provider_plan_id)
            product = stripe.Product.retrieve(price.product)
            stripe.Product.modify(product.id, name=plan.name)
            if plan.amount:
                interval = "month" if plan.interval == "monthly" else "year" if plan.interval == "yearly" else None
                new_price = stripe.Price.create(
                    product=product.id,
                    currency=plan.currency,
                    unit_amount=int(round(plan.amount * 100)),
                    recurring={"interval": interval} if interval else None,
                )
                return BillingPlan(
                    provider_plan_id=new_price.id,
                    name=plan.name,
                    description=plan.description,
                    amount=plan.amount,
                    currency=plan.currency,
                    interval=plan.interval,
                    trial_days=plan.trial_days,
                    metadata=plan.metadata,
                )
            return BillingPlan(
                provider_plan_id=provider_plan_id,
                name=plan.name,
                description=plan.description,
                amount=plan.amount,
                currency=plan.currency,
                interval=plan.interval,
                trial_days=plan.trial_days,
                metadata=plan.metadata,
            )
        except stripe.StripeError as e:
            raise BillingProviderError(str(e), provider="stripe", code=e.code)

    async def delete_plan(self, provider_plan_id: str) -> None:
        try:
            price = stripe.Price.retrieve(provider_plan_id)
            stripe.Product.modify(price.product, active=False)
        except stripe.StripeError as e:
            raise BillingProviderError(str(e), provider="stripe", code=e.code)

    # ── Customer Management ────────────────────────────────────────────────

    async def create_customer(self, customer: BillingCustomer) -> BillingCustomer:
        try:
            result = stripe.Customer.create(
                email=customer.email,
                name=customer.name,
                metadata=customer.metadata or {},
            )
            return BillingCustomer(
                provider_customer_id=result.id,
                email=result.email or customer.email,
                name=result.name or customer.name,
                metadata=dict(result.metadata) if result.metadata else None,
            )
        except stripe.StripeError as e:
            raise BillingProviderError(str(e), provider="stripe", code=e.code)

    async def get_customer(self, provider_customer_id: str) -> Optional[BillingCustomer]:
        try:
            result = stripe.Customer.retrieve(provider_customer_id)
            if result.deleted:
                return None
            return BillingCustomer(
                provider_customer_id=result.id,
                email=result.email or "",
                name=result.name,
                metadata=dict(result.metadata) if result.metadata else None,
            )
        except stripe.StripeError as e:
            raise BillingProviderError(str(e), provider="stripe", code=e.code)

    # ── Subscription Management ────────────────────────────────────────────

    async def create_subscription(
        self,
        provider_customer_id: str,
        provider_plan_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BillingSubscription:
        try:
            result = stripe.Subscription.create(
                customer=provider_customer_id,
                items=[{"price": provider_plan_id}],
                metadata=metadata or {},
                trial_period_days=metadata.get("trial_days", 0) if metadata else 0,
            )
            return BillingSubscription(
                provider_subscription_id=result.id,
                provider_customer_id=result.customer,
                provider_plan_id=result.plan.id if result.plan else provider_plan_id,
                status=result.status,
                current_period_start=str(result.current_period_start) if result.current_period_start else None,
                current_period_end=str(result.current_period_end) if result.current_period_end else None,
                cancel_at_period_end=result.cancel_at_period_end,
                metadata=dict(result.metadata) if result.metadata else None,
            )
        except stripe.StripeError as e:
            raise BillingProviderError(str(e), provider="stripe", code=e.code)

    async def cancel_subscription(
        self,
        provider_subscription_id: str,
        at_period_end: bool = True,
    ) -> BillingSubscription:
        try:
            if at_period_end:
                result = stripe.Subscription.modify(
                    provider_subscription_id,
                    cancel_at_period_end=True,
                )
            else:
                result = stripe.Subscription.cancel(provider_subscription_id)
            return BillingSubscription(
                provider_subscription_id=result.id,
                provider_customer_id=result.customer,
                provider_plan_id=result.plan.id if result.plan else "",
                status=result.status,
                current_period_start=str(result.current_period_start) if result.current_period_start else None,
                current_period_end=str(result.current_period_end) if result.current_period_end else None,
                cancel_at_period_end=result.cancel_at_period_end,
                metadata=dict(result.metadata) if result.metadata else None,
            )
        except stripe.StripeError as e:
            raise BillingProviderError(str(e), provider="stripe", code=e.code)

    async def get_subscription(self, provider_subscription_id: str) -> Optional[BillingSubscription]:
        try:
            result = stripe.Subscription.retrieve(provider_subscription_id)
            return BillingSubscription(
                provider_subscription_id=result.id,
                provider_customer_id=result.customer,
                provider_plan_id=result.plan.id if result.plan else "",
                status=result.status,
                current_period_start=str(result.current_period_start) if result.current_period_start else None,
                current_period_end=str(result.current_period_end) if result.current_period_end else None,
                cancel_at_period_end=result.cancel_at_period_end,
                metadata=dict(result.metadata) if result.metadata else None,
            )
        except stripe.StripeError as e:
            raise BillingProviderError(str(e), provider="stripe", code=e.code)

    async def update_subscription_plan(
        self,
        provider_subscription_id: str,
        new_provider_plan_id: str,
    ) -> BillingSubscription:
        try:
            sub = stripe.Subscription.retrieve(provider_subscription_id)
            subscription_item_id = sub.items.data[0].id
            result = stripe.Subscription.modify(
                provider_subscription_id,
                items=[{"id": subscription_item_id, "price": new_provider_plan_id}],
                proration_behavior="create_prorations",
            )
            return BillingSubscription(
                provider_subscription_id=result.id,
                provider_customer_id=result.customer,
                provider_plan_id=new_provider_plan_id,
                status=result.status,
                current_period_start=str(result.current_period_start) if result.current_period_start else None,
                current_period_end=str(result.current_period_end) if result.current_period_end else None,
                cancel_at_period_end=result.cancel_at_period_end,
                metadata=dict(result.metadata) if result.metadata else None,
            )
        except stripe.StripeError as e:
            raise BillingProviderError(str(e), provider="stripe", code=e.code)

    # ── Webhook Handling ───────────────────────────────────────────────────

    async def handle_webhook(
        self,
        raw_body: bytes,
        signature_header: Optional[str] = None,
    ) -> Dict[str, Any]:
        secret = self.webhook_secret
        if not signature_header:
            return {"event_type": "unknown", "event_id": "", "data": {}}
        try:
            event = stripe.Webhook.construct_event(raw_body, signature_header, secret)
        except stripe.SignatureVerificationError as e:
            raise BillingProviderError(str(e), provider="stripe", code="webhook_signature_invalid")
        except stripe.StripeError as e:
            raise BillingProviderError(str(e), provider="stripe", code=e.code)

        event_data = event.data.object if event.data else {}

        return {
            "event_type": event.type,
            "event_id": event.id,
            "data": event_data,
        }

    # ── Checkout / Hosted Pages ───────────────────────────────────────────

    async def create_checkout_session(
        self,
        provider_customer_id: str,
        provider_plan_id: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        try:
            session = stripe.checkout.Session.create(
                customer=provider_customer_id,
                mode="subscription",
                line_items=[{"price": provider_plan_id, "quantity": 1}],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata or {},
            )
            return session.url
        except stripe.StripeError as e:
            raise BillingProviderError(str(e), provider="stripe", code=e.code)

    # ── Stripe Connect helpers (not part of the ABC) ──────────────────────

    async def create_connect_account(self, email: str, country: str = "US") -> str:
        """Create a Stripe Connect Express account and return its ID."""
        try:
            account = stripe.Account.create(
                type="express",
                country=country,
                email=email,
                capabilities={
                    "transfers": {"requested": True},
                },
            )
            return account.id
        except stripe.StripeError as e:
            raise BillingProviderError(str(e), provider="stripe", code=e.code)

    async def create_connect_onboarding_link(
        self, connect_account_id: str, refresh_url: str, return_url: str
    ) -> str:
        """Generate a Stripe Connect onboarding link for an Express account."""
        try:
            link = stripe.AccountLink.create(
                account=connect_account_id,
                refresh_url=refresh_url,
                return_url=return_url,
                type="account_onboarding",
            )
            return link.url
        except stripe.StripeError as e:
            raise BillingProviderError(str(e), provider="stripe", code=e.code)

    async def create_connect_dashboard_link(self, connect_account_id: str) -> str:
        """Get the Stripe Express dashboard URL for a connected account."""
        try:
            link = stripe.Account.create_login_link(connect_account_id)
            return link.url
        except stripe.StripeError as e:
            raise BillingProviderError(str(e), provider="stripe", code=e.code)


BillingProviderRegistry.register("stripe", StripeBillingProvider)
