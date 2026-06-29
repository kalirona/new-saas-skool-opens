"""
LemonSqueezy billing provider stub.

Implementation placeholder — no actual LemonSqueezy API calls.
LemonSqueezy will be integrated primarily via webhooks.
"""

from typing import Optional, Dict, Any
from src.billing.base import BillingProvider, BillingPlan, BillingCustomer, BillingSubscription, BillingProviderError
from src.billing.registry import BillingProviderRegistry


class LemonSqueezyBillingProvider(BillingProvider):
    """LemonSqueezy billing integration (placeholder)."""

    @property
    def provider_name(self) -> str:
        return "lemonsqueezy"

    def __init__(self, config: dict):
        self.api_key = config.get("api_key", "")
        self.store_id = config.get("store_id", "")
        self.webhook_secret = config.get("webhook_secret", "")

    async def create_plan(self, plan: BillingPlan) -> BillingPlan:
        raise NotImplementedError("LemonSqueezy provider not yet implemented")

    async def update_plan(self, provider_plan_id: str, plan: BillingPlan) -> BillingPlan:
        raise NotImplementedError("LemonSqueezy provider not yet implemented")

    async def delete_plan(self, provider_plan_id: str) -> None:
        raise NotImplementedError("LemonSqueezy provider not yet implemented")

    async def create_customer(self, customer: BillingCustomer) -> BillingCustomer:
        raise NotImplementedError("LemonSqueezy provider not yet implemented")

    async def get_customer(self, provider_customer_id: str) -> Optional[BillingCustomer]:
        raise NotImplementedError("LemonSqueezy provider not yet implemented")

    async def create_subscription(
        self, provider_customer_id: str, provider_plan_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BillingSubscription:
        raise NotImplementedError("LemonSqueezy provider not yet implemented")

    async def cancel_subscription(
        self, provider_subscription_id: str, at_period_end: bool = True,
    ) -> BillingSubscription:
        raise NotImplementedError("LemonSqueezy provider not yet implemented")

    async def get_subscription(self, provider_subscription_id: str) -> Optional[BillingSubscription]:
        raise NotImplementedError("LemonSqueezy provider not yet implemented")

    async def update_subscription_plan(
        self, provider_subscription_id: str, new_provider_plan_id: str,
    ) -> BillingSubscription:
        raise NotImplementedError("LemonSqueezy provider not yet implemented")

    async def handle_webhook(
        self, raw_body: bytes, signature_header: Optional[str] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError("LemonSqueezy provider not yet implemented")

    async def create_checkout_session(
        self, provider_customer_id: str, provider_plan_id: str,
        success_url: str, cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        raise NotImplementedError("LemonSqueezy provider not yet implemented")


BillingProviderRegistry.register("lemonsqueezy", LemonSqueezyBillingProvider)
