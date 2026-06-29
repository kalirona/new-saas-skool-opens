from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any


class BillingProviderError(Exception):
    """Base exception for billing provider errors."""

    def __init__(self, message: str, provider: str, code: Optional[str] = None):
        self.provider = provider
        self.code = code
        super().__init__(message)


@dataclass
class BillingPlan:
    """Represents a pricing plan in the billing provider."""
    provider_plan_id: str
    name: str
    description: Optional[str] = None
    amount: float = 0.0
    currency: str = "usd"
    interval: str = "monthly"
    trial_days: int = 0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class BillingSubscription:
    """Represents a subscription in the billing provider."""
    provider_subscription_id: str
    provider_customer_id: str
    provider_plan_id: str
    status: str
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class BillingCustomer:
    """Represents a customer in the billing provider."""
    provider_customer_id: str
    email: str
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BillingProvider(ABC):
    """
    Abstract base class for billing provider integrations.

    All payment providers (Stripe, PayPal, LemonSqueezy, Paddle, SureCart)
    must implement this interface. The LearnHouse core never calls payment
    providers directly — it always goes through this abstraction layer.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name, e.g. 'stripe', 'paypal', 'lemonsqueezy'."""
        pass

    # ── Plan / Product Management ──────────────────────────────────────────

    @abstractmethod
    async def create_plan(self, plan: BillingPlan) -> BillingPlan:
        """
        Create a pricing plan/product in the billing provider.

        Raises BillingProviderError on failure.
        """
        pass

    @abstractmethod
    async def update_plan(self, provider_plan_id: str, plan: BillingPlan) -> BillingPlan:
        """
        Update an existing plan in the billing provider.
        """
        pass

    @abstractmethod
    async def delete_plan(self, provider_plan_id: str) -> None:
        """
        Archive/deactivate a plan in the billing provider.
        """
        pass

    # ── Customer Management ────────────────────────────────────────────────

    @abstractmethod
    async def create_customer(self, customer: BillingCustomer) -> BillingCustomer:
        """
        Create a customer record in the billing provider.
        """
        pass

    @abstractmethod
    async def get_customer(self, provider_customer_id: str) -> Optional[BillingCustomer]:
        """
        Retrieve a customer from the billing provider.
        """
        pass

    # ── Subscription Management ────────────────────────────────────────────

    @abstractmethod
    async def create_subscription(
        self,
        provider_customer_id: str,
        provider_plan_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BillingSubscription:
        """
        Create a subscription for a customer to a plan.

        Returns the BillingSubscription with provider IDs populated.
        """
        pass

    @abstractmethod
    async def cancel_subscription(
        self,
        provider_subscription_id: str,
        at_period_end: bool = True,
    ) -> BillingSubscription:
        """
        Cancel an active subscription.

        If at_period_end is True, the subscription remains active
        until the current billing period ends.
        """
        pass

    @abstractmethod
    async def get_subscription(
        self,
        provider_subscription_id: str,
    ) -> Optional[BillingSubscription]:
        """
        Retrieve a subscription's current state from the billing provider.
        """
        pass

    @abstractmethod
    async def update_subscription_plan(
        self,
        provider_subscription_id: str,
        new_provider_plan_id: str,
    ) -> BillingSubscription:
        """
        Change the plan on an existing subscription (upgrade/downgrade).
        """
        pass

    # ── Webhook Handling ───────────────────────────────────────────────────

    @abstractmethod
    async def handle_webhook(
        self,
        raw_body: bytes,
        signature_header: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process an incoming webhook from the billing provider.

        Returns a normalized dict with at minimum:
          - event_type: str
          - event_id: str
          - data: dict

        The caller is responsible for routing the event type to the
        appropriate business logic (e.g., subscription.updated ->
        update user's membership status).
        """
        pass

    # ── Checkout / Hosted Pages ───────────────────────────────────────────

    @abstractmethod
    async def create_checkout_session(
        self,
        provider_customer_id: str,
        provider_plan_id: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a hosted checkout page URL.

        Returns the URL the user should be redirected to.
        This is intentionally _not_ a payment processing call —
        the user completes payment on the provider's hosted page.
        """
        pass
