import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.billing.base import BillingProvider, BillingPlan, BillingSubscription, BillingCustomer, BillingProviderError


class TestBillingProviderError:
    def test_error_with_provider_and_code(self):
        err = BillingProviderError("Failed", "stripe", "auth_failed")
        assert err.provider == "stripe"
        assert err.code == "auth_failed"
        assert "Failed" in str(err)

    def test_error_without_code(self):
        err = BillingProviderError("Timeout", "paypal")
        assert err.provider == "paypal"
        assert err.code is None


class TestBillingPlan:
    def test_default_values(self):
        plan = BillingPlan(provider_plan_id="price_123", name="Pro")
        assert plan.amount == 0.0
        assert plan.currency == "usd"
        assert plan.interval == "monthly"
        assert plan.trial_days == 0
        assert plan.metadata is None
        assert plan.description is None

    def test_full_construction(self):
        plan = BillingPlan(
            provider_plan_id="price_456",
            name="Enterprise",
            description="Full access",
            amount=99.99,
            currency="eur",
            interval="yearly",
            trial_days=14,
            metadata={"plan_uuid": "p_001"},
        )
        assert plan.amount == 99.99
        assert plan.currency == "eur"
        assert plan.interval == "yearly"
        assert plan.trial_days == 14
        assert plan.metadata == {"plan_uuid": "p_001"}


class TestBillingSubscription:
    def test_defaults(self):
        sub = BillingSubscription(
            provider_subscription_id="sub_123",
            provider_customer_id="cus_123",
            provider_plan_id="price_123",
            status="active",
        )
        assert sub.cancel_at_period_end is False
        assert sub.current_period_start is None
        assert sub.metadata is None


class TestBillingCustomer:
    def test_name_optional(self):
        c = BillingCustomer(provider_customer_id="cus_abc", email="test@test.com")
        assert c.name is None

    def test_with_name(self):
        c = BillingCustomer(provider_customer_id="cus_xyz", email="bob@test.com", name="Bob")
        assert c.name == "Bob"


class TestBillingProvider:
    @pytest.mark.asyncio
    async def test_provider_is_abstract(self):
        with pytest.raises(TypeError):
            BillingProvider()

    @pytest.mark.asyncio
    async def test_concrete_provider_works(self):
        class ConcreteProvider(BillingProvider):
            @property
            def provider_name(self):
                return "test"

            async def create_plan(self, plan):
                return plan

            async def update_plan(self, provider_plan_id, plan):
                return plan

            async def delete_plan(self, provider_plan_id):
                pass

            async def create_customer(self, customer):
                return customer

            async def get_customer(self, provider_customer_id):
                return None

            async def create_subscription(self, provider_customer_id, provider_plan_id, metadata=None):
                return BillingSubscription(
                    provider_subscription_id="sub_test",
                    provider_customer_id=provider_customer_id,
                    provider_plan_id=provider_plan_id,
                    status="active",
                )

            async def cancel_subscription(self, provider_subscription_id, at_period_end=True):
                return BillingSubscription(
                    provider_subscription_id=provider_subscription_id,
                    provider_customer_id="cus_test",
                    provider_plan_id="price_test",
                    status="canceled",
                    cancel_at_period_end=at_period_end,
                )

            async def get_subscription(self, provider_subscription_id):
                return None

            async def update_subscription_plan(self, provider_subscription_id, new_provider_plan_id):
                return BillingSubscription(
                    provider_subscription_id=provider_subscription_id,
                    provider_customer_id="cus_test",
                    provider_plan_id=new_provider_plan_id,
                    status="active",
                )

            async def handle_webhook(self, raw_body, signature_header=None):
                return {"event_type": "test.event", "event_id": "evt_001", "data": {}}

            async def create_checkout_session(self, provider_customer_id, provider_plan_id, success_url, cancel_url, metadata=None):
                return "https://checkout.test.com/session"

        provider = ConcreteProvider()
        assert provider.provider_name == "test"

        plan = BillingPlan(provider_plan_id="price_t", name="Test")
        result = await provider.create_plan(plan)
        assert result == plan

        sub = await provider.create_subscription("cus_1", "price_1")
        assert sub.status == "active"
        assert sub.provider_subscription_id == "sub_test"

        canceled = await provider.cancel_subscription("sub_1")
        assert canceled.status == "canceled"
        assert canceled.cancel_at_period_end is True

        upgraded = await provider.update_subscription_plan("sub_1", "price_2")
        assert upgraded.provider_plan_id == "price_2"

        url = await provider.create_checkout_session("cus_1", "price_1", "http://success", "http://cancel")
        assert url == "https://checkout.test.com/session"

        wh = await provider.handle_webhook(b'{}', "sig")
        assert wh["event_type"] == "test.event"

    @pytest.mark.asyncio
    async def test_provider_raises_on_abstract_methods(self):
        class IncompleteProvider(BillingProvider):
            @property
            def provider_name(self):
                return "incomplete"

        with pytest.raises(TypeError):
            IncompleteProvider()
