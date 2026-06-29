"""
Paddle billing provider stub.

Implementation placeholder — no actual Paddle API calls.
"""

from typing import Optional, Dict, Any
from src.billing.base import BillingProvider, BillingPlan, BillingCustomer, BillingSubscription, BillingProviderError
from src.billing.registry import BillingProviderRegistry


class PaddleBillingProvider(BillingProvider):
    """Paddle billing integration (placeholder)."""

    @property
    def provider_name(self) -> str:
        return "paddle"

    def __init__(self, config: dict):
        self.api_key = config.get("api_key", "")
        self.webhook_secret = config.get("webhook_secret", "")

    async def create_plan(self, plan: BillingPlan) -> BillingPlan:
        raise NotImplementedError("Paddle provider not yet implemented")

    async def update_plan(self, provider_plan_id: str, plan: BillingPlan) -> BillingPlan:
        raise NotImplementedError("Paddle provider not yet implemented")

    async def delete_plan(self, provider_plan_id: str) -> None:
        raise NotImplementedError("Paddle provider not yet implemented")

    async def create_customer(self, customer: BillingCustomer) -> BillingCustomer:
        raise NotImplementedError("Paddle provider not yet implemented")

    async def get_customer(self, provider_customer_id: str) -> Optional[BillingCustomer]:
        raise NotImplementedError("Paddle provider not yet implemented")

    async def create_subscription(
        self, provider_customer_id: str, provider_plan_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BillingSubscription:
        raise NotImplementedError("Paddle provider not yet implemented")

    async def cancel_subscription(
        self, provider_subscription_id: str, at_period_end: bool = True,
    ) -> BillingSubscription:
        raise NotImplementedError("Paddle provider not yet implemented")

    async def get_subscription(self, provider_subscription_id: str) -> Optional[BillingSubscription]:
        raise NotImplementedError("Paddle provider not yet implemented")

    async def update_subscription_plan(
        self, provider_subscription_id: str, new_provider_plan_id: str,
    ) -> BillingSubscription:
        raise NotImplementedError("Paddle provider not yet implemented")

    async def handle_webhook(
        self, raw_body: bytes, signature_header: Optional[str] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError("Paddle provider not yet implemented")

    async def create_checkout_session(
        self, provider_customer_id: str, provider_plan_id: str,
        success_url: str, cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        raise NotImplementedError("Paddle provider not yet implemented")


BillingProviderRegistry.register("paddle", PaddleBillingProvider)
