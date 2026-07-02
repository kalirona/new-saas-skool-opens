import pytest
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock
from src.billing.base import BillingPlan, BillingCustomer, BillingSubscription, BillingProviderError


# ── Registry ──────────────────────────────────────────────────────────────


class TestBillingProviderRegistry:
    def test_register_and_get(self):
        from src.billing.registry import BillingProviderRegistry
        BillingProviderRegistry._providers.clear()
        mock_cls = MagicMock()
        BillingProviderRegistry.register("stripe", mock_cls)
        assert BillingProviderRegistry.get("stripe") == mock_cls
        assert BillingProviderRegistry.is_supported("stripe") is True
        assert BillingProviderRegistry.is_supported("paypal") is False

    def test_create_instance(self):
        from src.billing.registry import BillingProviderRegistry
        BillingProviderRegistry._providers.clear()
        mock_cls = MagicMock()
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        BillingProviderRegistry.register("test", mock_cls)
        instance = BillingProviderRegistry.create_instance("test", {"key": "val"})
        mock_cls.assert_called_once_with({"key": "val"})
        assert instance == mock_instance

    def test_create_instance_unknown_returns_none(self):
        from src.billing.registry import BillingProviderRegistry
        BillingProviderRegistry._providers.clear()
        assert BillingProviderRegistry.create_instance("nonexistent") is None

    def test_list_supported_and_get_all(self):
        from src.billing.registry import BillingProviderRegistry
        BillingProviderRegistry._providers.clear()
        BillingProviderRegistry.register("a", MagicMock())
        BillingProviderRegistry.register("b", MagicMock())
        all_p = BillingProviderRegistry.get_all()
        assert set(all_p.keys()) == {"a", "b"}
        supported = BillingProviderRegistry.list_supported()
        assert "a" in supported
        assert "b" in supported


# ── StripeBillingProvider ────────────────────────────────────────────────


class TestStripeBillingProvider:
    @pytest.fixture
    def provider(self):
        with patch("src.billing.providers.stripe.stripe") as mock_stripe:
            from src.billing.providers.stripe import StripeBillingProvider
            p = StripeBillingProvider({
                "api_key": "sk_test_xxx",
                "webhook_secret": "whsec_test",
                "connect_webhook_secret": "whsec_connect",
            })
            yield p, mock_stripe

    @pytest.mark.asyncio
    async def test_create_plan_monthly(self, provider):
        p, mock_stripe = provider
        mock_stripe.Product.create.return_value = MagicMock(id="prod_123")
        mock_stripe.Price.create.return_value = MagicMock(id="price_456")

        plan = BillingPlan(
            provider_plan_id="",
            name="Pro Monthly",
            amount=29.99,
            currency="usd",
            interval="monthly",
            trial_days=7,
        )
        result = await p.create_plan(plan)

        assert result.provider_plan_id == "price_456"
        mock_stripe.Product.create.assert_called_once_with(name="Pro Monthly", metadata={})
        mock_stripe.Price.create.assert_called_once()
        call_kwargs = mock_stripe.Price.create.call_args[1]
        assert call_kwargs["currency"] == "usd"
        assert call_kwargs["unit_amount"] == 2999
        assert call_kwargs["recurring"] == {"interval": "month", "trial_period_days": 7}

    @pytest.mark.asyncio
    async def test_create_plan_yearly(self, provider):
        p, mock_stripe = provider
        mock_stripe.Product.create.return_value = MagicMock(id="prod_1")
        mock_stripe.Price.create.return_value = MagicMock(id="price_1")

        plan = BillingPlan(
            provider_plan_id="", name="Pro Yearly", amount=199.99, currency="usd", interval="yearly"
        )
        result = await p.create_plan(plan)
        call_kwargs = mock_stripe.Price.create.call_args[1]
        assert call_kwargs["recurring"] == {"interval": "year"}

    @pytest.mark.asyncio
    async def test_create_plan_one_time(self, provider):
        p, mock_stripe = provider
        mock_stripe.Product.create.return_value = MagicMock(id="prod_1")
        mock_stripe.Price.create.return_value = MagicMock(id="price_1")

        plan = BillingPlan(
            provider_plan_id="", name="Lifetime", amount=499.99, currency="usd", interval="one_time"
        )
        result = await p.create_plan(plan)
        call_kwargs = mock_stripe.Price.create.call_args[1]
        assert call_kwargs["recurring"] is None

    @pytest.mark.asyncio
    async def test_create_plan_with_metadata(self, provider):
        p, mock_stripe = provider
        mock_stripe.Product.create.return_value = MagicMock(id="prod_1")
        mock_stripe.Price.create.return_value = MagicMock(id="price_1")

        plan = BillingPlan(
            provider_plan_id="", name="Pro", amount=10.0, currency="usd",
            interval="monthly", metadata={"plan_uuid": "p_001"},
        )
        result = await p.create_plan(plan)
        mock_stripe.Product.create.assert_called_once_with(name="Pro", metadata={"plan_uuid": "p_001"})

    @pytest.mark.asyncio
    async def test_create_plan_stripe_error(self, provider):
        p, mock_stripe = provider
        mock_stripe.Product.create.side_effect = Exception("Stripe API error")

        plan = BillingPlan(provider_plan_id="", name="Fail", amount=10.0, currency="usd", interval="monthly")
        with pytest.raises(BillingProviderError, match="Stripe API error"):
            await p.create_plan(plan)

    @pytest.mark.asyncio
    async def test_update_plan(self, provider):
        p, mock_stripe = provider
        mock_stripe.Product.create.return_value = MagicMock(id="prod_1")
        mock_stripe.Price.create.return_value = MagicMock(id="price_new")

        plan = BillingPlan(
            provider_plan_id="price_old", name="Updated", amount=15.0,
            currency="usd", interval="monthly",
        )
        result = await p.update_plan("price_old", plan)
        assert result.provider_plan_id == "price_new"
        mock_stripe.Price.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_plan(self, provider):
        p, mock_stripe = provider
        mock_stripe.Price.modify.return_value = MagicMock()
        result = await p.delete_plan("price_123")
        mock_stripe.Price.modify.assert_called_once_with("price_123", active=False)

    @pytest.mark.asyncio
    async def test_delete_plan_error(self, provider):
        p, mock_stripe = provider
        mock_stripe.Price.modify.side_effect = Exception("Stripe error")
        with pytest.raises(BillingProviderError):
            await p.delete_plan("price_123")

    @pytest.mark.asyncio
    async def test_create_customer(self, provider):
        p, mock_stripe = provider
        mock_stripe.Customer.create.return_value = MagicMock(id="cus_123")

        customer = BillingCustomer(provider_customer_id="", email="test@test.com", name="Alice")
        result = await p.create_customer(customer)
        assert result.provider_customer_id == "cus_123"
        assert result.email == "test@test.com"

    @pytest.mark.asyncio
    async def test_get_customer_found(self, provider):
        p, mock_stripe = provider
        mock_stripe.Customer.retrieve.return_value = MagicMock(id="cus_123", email="a@b.com", name=None)
        result = await p.get_customer("cus_123")
        assert result.provider_customer_id == "cus_123"
        assert result.email == "a@b.com"

    @pytest.mark.asyncio
    async def test_get_customer_not_found(self, provider):
        p, mock_stripe = provider
        mock_stripe.Customer.retrieve.side_effect = Exception("Not found")
        result = await p.get_customer("cus_missing")
        assert result is None

    @pytest.mark.asyncio
    async def test_create_subscription(self, provider):
        p, mock_stripe = provider
        mock_stripe.Subscription.create.return_value = MagicMock(
            id="sub_123", customer="cus_1", items={"data": [{"price": {"id": "price_1"}}]},
            status="active", current_period_start=1000, current_period_end=2000,
            cancel_at_period_end=False, metadata={},
        )
        sub = await p.create_subscription("cus_1", "price_1", metadata={"plan_uuid": "p_001"})
        assert sub.provider_subscription_id == "sub_123"
        assert sub.status == "active"
        mock_stripe.Subscription.create.assert_called_once()
        call_kwargs = mock_stripe.Subscription.create.call_args[1]
        assert call_kwargs["customer"] == "cus_1"
        assert call_kwargs["items"][0]["price"] == "price_1"

    @pytest.mark.asyncio
    async def test_create_subscription_with_trial(self, provider):
        p, mock_stripe = provider
        mock_stripe.Subscription.create.return_value = MagicMock(
            id="sub_123", customer="cus_1", items={"data": []},
            status="trialing", current_period_start=1000, current_period_end=2000,
            cancel_at_period_end=False, metadata={},
        )
        sub = await p.create_subscription("cus_1", "price_1", metadata={"trial_days": "14"})
        assert sub.status == "trialing"

    @pytest.mark.asyncio
    async def test_cancel_subscription_immediately(self, provider):
        p, mock_stripe = provider
        mock_stripe.Subscription.delete.return_value = MagicMock(
            id="sub_123", customer="cus_1", items={"data": []},
            status="canceled", current_period_start=1000, current_period_end=2000,
            cancel_at_period_end=False, metadata={},
        )
        sub = await p.cancel_subscription("sub_123", at_period_end=False)
        assert sub.status == "canceled"
        mock_stripe.Subscription.delete.assert_called_once_with("sub_123", invoice_now=True, prorate=True)

    @pytest.mark.asyncio
    async def test_cancel_subscription_at_period_end(self, provider):
        p, mock_stripe = provider
        mock_stripe.Subscription.modify.return_value = MagicMock(
            id="sub_123", customer="cus_1", items={"data": []},
            status="active", current_period_start=1000, current_period_end=2000,
            cancel_at_period_end=True, metadata={},
        )
        sub = await p.cancel_subscription("sub_123", at_period_end=True)
        assert sub.cancel_at_period_end is True
        mock_stripe.Subscription.modify.assert_called_once_with("sub_123", cancel_at_period_end=True)

    @pytest.mark.asyncio
    async def test_get_subscription(self, provider):
        p, mock_stripe = provider
        mock_stripe.Subscription.retrieve.return_value = MagicMock(
            id="sub_123", customer="cus_1", items={"data": [{"price": {"id": "price_1"}}]},
            status="active", current_period_start=1000, current_period_end=2000,
            cancel_at_period_end=False, metadata={},
        )
        sub = await p.get_subscription("sub_123")
        assert sub.provider_subscription_id == "sub_123"
        assert sub.status == "active"

    @pytest.mark.asyncio
    async def test_get_subscription_not_found(self, provider):
        p, mock_stripe = provider
        mock_stripe.Subscription.retrieve.side_effect = Exception("Not found")
        sub = await p.get_subscription("sub_missing")
        assert sub is None

    @pytest.mark.asyncio
    async def test_update_subscription_plan(self, provider):
        p, mock_stripe = provider
        mock_stripe.Subscription.retrieve.return_value = MagicMock(
            id="sub_123", items={"data": [{"id": "si_1", "price": {"id": "price_old"}}]}
        )
        mock_stripe.Subscription.modify.return_value = MagicMock(
            id="sub_123", customer="cus_1", items={"data": [{"price": {"id": "price_new"}}]},
            status="active", current_period_start=1000, current_period_end=2000,
            cancel_at_period_end=False, metadata={},
        )
        sub = await p.update_subscription_plan("sub_123", "price_new")
        assert sub.provider_plan_id == "price_new"
        mock_stripe.Subscription.retrieve.assert_called_once_with("sub_123")

    @pytest.mark.asyncio
    async def test_create_checkout_session(self, provider):
        p, mock_stripe = provider
        mock_stripe.checkout.Session.create.return_value = MagicMock(url="https://checkout.stripe.com/sess_123")
        url = await p.create_checkout_session(
            "cus_1", "price_1", "http://success", "http://cancel",
            metadata={"plan_uuid": "p_001"},
        )
        assert url == "https://checkout.stripe.com/sess_123"
        mock_stripe.checkout.Session.create.assert_called_once()
        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["customer"] == "cus_1"
        assert call_kwargs["line_items"][0]["price"] == "price_1"
        assert call_kwargs["mode"] == "subscription"

    @pytest.mark.asyncio
    async def test_handle_webhook_standard(self, provider):
        p, mock_stripe = provider
        fake_event = MagicMock()
        fake_event.type = "checkout.session.completed"
        fake_event.data.object.to_dict.return_value = {"id": "cs_123"}
        fake_event.account = None
        mock_stripe.Webhook.construct_event.return_value = fake_event

        result = await p.handle_webhook(b'{}', "whsig_test")
        assert result["event_type"] == "checkout.session.completed"
        assert result["event_id"] == "cs_123"
        assert "data" in result

    @pytest.mark.asyncio
    async def test_handle_webhook_connect(self, provider):
        p, mock_stripe = provider
        fake_event = MagicMock()
        fake_event.type = "checkout.session.completed"
        fake_event.data.object.to_dict.return_value = {"id": "cs_456"}
        fake_event.account = "acct_connected"
        mock_stripe.Webhook.construct_event.return_value = fake_event

        result = await p.handle_webhook(b'{}', "whsig_connect", webhook_type="connect")
        assert result["event_data"]["stripe_account"] == "acct_connected"

    @pytest.mark.asyncio
    async def test_handle_webhook_signature_error(self, provider):
        p, mock_stripe = provider
        mock_stripe.Webhook.construct_event.side_effect = Exception("Bad signature")
        with pytest.raises(BillingProviderError, match="Bad signature"):
            await p.handle_webhook(b'{}', "bad_sig")


# ── PayPalBillingProvider ────────────────────────────────────────────────


class TestPayPalBillingProvider:
    @pytest.fixture
    def provider(self):
        with patch("src.billing.providers.paypal.httpx.AsyncClient") as mock_client_cls:
            from src.billing.providers.paypal import PayPalBillingProvider
            p = PayPalBillingProvider({
                "client_id": "test_client",
                "client_secret": "test_secret",
                "webhook_id": "wh_test",
                "sandbox": True,
            })
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            yield p, mock_client

    @pytest.mark.asyncio
    async def test_get_access_token_cached(self, provider):
        p, mock_client = provider
        p._access_token = "cached_token"
        token = await p._get_access_token()
        assert token == "cached_token"
        mock_client.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_access_token_fetches(self, provider):
        p, mock_client = provider
        p._access_token = None
        mock_client.post.return_value = MagicMock(status_code=200, json=lambda: {"access_token": "fresh_token"})
        token = await p._get_access_token()
        assert token == "fresh_token"
        assert p._access_token == "fresh_token"

    @pytest.mark.asyncio
    async def test_get_access_token_failure(self, provider):
        p, mock_client = provider
        p._access_token = None
        mock_client.post.return_value = MagicMock(status_code=401)
        with pytest.raises(BillingProviderError, match="Failed to get PayPal access token"):
            await p._get_access_token()

    @pytest.mark.asyncio
    async def test_create_plan(self, provider):
        p, mock_client = provider
        p._access_token = "tok"
        mock_client.post.return_value = MagicMock(status_code=201, json=lambda: {"id": "P-123"})
        plan = BillingPlan(provider_plan_id="", name="Pro", amount=29.99, currency="USD", interval="monthly")
        result = await p.create_plan(plan)
        assert result.provider_plan_id == "P-123"

    @pytest.mark.asyncio
    async def test_create_plan_error(self, provider):
        p, mock_client = provider
        p._access_token = "tok"
        mock_client.post.return_value = MagicMock(status_code=400)
        with pytest.raises(BillingProviderError):
            await p.create_plan(BillingPlan(provider_plan_id="", name="Fail", amount=10.0, currency="USD", interval="monthly"))

    @pytest.mark.asyncio
    async def test_update_plan(self, provider):
        p, mock_client = provider
        p._access_token = "tok"
        mock_client.patch.return_value = MagicMock(status_code=200)
        plan = BillingPlan(provider_plan_id="P-123", name="Updated", amount=20.0, currency="USD", interval="monthly")
        result = await p.update_plan("P-123", plan)
        assert result.provider_plan_id == "P-123"

    @pytest.mark.asyncio
    async def test_delete_plan(self, provider):
        p, mock_client = provider
        p._access_token = "tok"
        mock_client.post.return_value = MagicMock(status_code=204)
        result = await p.delete_plan("P-123")
        assert result is None

    @pytest.mark.asyncio
    async def test_create_customer(self, provider):
        p, mock_client = provider
        customer = BillingCustomer(provider_customer_id="", email="a@b.com", name="Alice")
        with pytest.raises(NotImplementedError):
            await p.create_customer(customer)

    @pytest.mark.asyncio
    async def test_get_customer(self, provider):
        p, mock_client = provider
        result = await p.get_customer("cust_123")
        assert result is None

    @pytest.mark.asyncio
    async def test_create_subscription(self, provider):
        p, mock_client = provider
        p._access_token = "tok"
        mock_client.post.return_value = MagicMock(status_code=201, json=lambda: {"id": "I-123"})
        sub = await p.create_subscription("cust_1", "plan_1")
        assert sub.provider_subscription_id == "I-123"
        assert sub.status == "active"

    @pytest.mark.asyncio
    async def test_cancel_subscription(self, provider):
        p, mock_client = provider
        p._access_token = "tok"
        mock_client.post.return_value = MagicMock(status_code=204)
        sub = await p.cancel_subscription("I-123")
        assert sub.status == "cancelled"

    @pytest.mark.asyncio
    async def test_get_subscription(self, provider):
        p, mock_client = provider
        p._access_token = "tok"
        mock_client.get.return_value = MagicMock(status_code=200, json=lambda: {"id": "I-123", "status": "ACTIVE", "plan_id": "P-123", "subscriber": {"payer_id": "payer_1"}})
        sub = await p.get_subscription("I-123")
        assert sub.provider_subscription_id == "I-123"
        assert sub.status == "active"

    @pytest.mark.asyncio
    async def test_update_subscription_plan(self, provider):
        p, mock_client = provider
        p._access_token = "tok"
        mock_client.post.return_value = MagicMock(status_code=200, json=lambda: {"id": "I-123", "status": "ACTIVE", "plan_id": "P-NEW", "subscriber": {"payer_id": "payer_1"}})
        sub = await p.update_subscription_plan("I-123", "P-NEW")
        assert sub.provider_plan_id == "P-NEW"

    @pytest.mark.asyncio
    async def test_create_checkout_session(self, provider):
        p, mock_client = provider
        p._access_token = "tok"
        mock_client.post.return_value = MagicMock(status_code=201, json=lambda: {"id": "LINK_123", "links": [{"rel": "approve", "href": "https://paypal.com/checkout"}]})
        url = await p.create_checkout_session("cust_1", "plan_1", "http://success", "http://cancel")
        assert url == "https://paypal.com/checkout"

    @pytest.mark.asyncio
    async def test_create_checkout_session_no_approve_link(self, provider):
        p, mock_client = provider
        p._access_token = "tok"
        mock_client.post.return_value = MagicMock(status_code=201, json=lambda: {"id": "LINK_123", "links": [{"rel": "self", "href": "https://paypal.com/checkout"}]})
        with pytest.raises(BillingProviderError, match="No approval URL"):
            await p.create_checkout_session("cust_1", "plan_1", "http://success", "http://cancel")

    @pytest.mark.asyncio
    async def test_handle_webhook_verify_success(self, provider):
        p, mock_client = provider
        mock_client.post.return_value = MagicMock(status_code=200, json=lambda: {"verification_status": "SUCCESS"})
        result = await p.handle_webhook(b'{}', "sig")
        assert "event_type" in result
        assert "event_id" in result

    @pytest.mark.asyncio
    async def test_handle_webhook_verify_failure(self, provider):
        p, mock_client = provider
        mock_client.post.return_value = MagicMock(status_code=200, json=lambda: {"verification_status": "FAILURE"})
        with pytest.raises(BillingProviderError, match="Webhook verification failed"):
            await p.handle_webhook(b'{}', "sig")

    @pytest.mark.asyncio
    async def test_handle_webhook_invalid_json(self, provider):
        p, mock_client = provider
        p._access_token = "tok"
        mock_client.post.return_value = MagicMock(status_code=200, json=lambda: {"verification_status": "SUCCESS"})
        with pytest.raises(BillingProviderError):
            await p.handle_webhook(b'invalid json', "sig")


# ── LemonSqueezyBillingProvider ──────────────────────────────────────────


class TestLemonSqueezyBillingProvider:
    @pytest.fixture
    def provider(self):
        with patch("src.billing.providers.lemonsqueezy.httpx.AsyncClient") as mock_client_cls:
            from src.billing.providers.lemonsqueezy import LemonSqueezyBillingProvider
            p = LemonSqueezyBillingProvider({
                "api_key": "ls_test",
                "store_id": "store_1",
                "webhook_secret": "whsec_ls",
            })
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            yield p, mock_client

    @pytest.mark.asyncio
    async def test_provider_name(self, provider):
        p, _ = provider
        assert p.provider_name == "lemonsqueezy"

    @pytest.mark.asyncio
    async def test_create_plan(self, provider):
        p, mock_client = provider
        mock_client.post.return_value = MagicMock(status_code=201, json=lambda: {"data": {"id": "12345", "attributes": {"name": "Pro", "status": "published"}}})
        plan = BillingPlan(provider_plan_id="", name="Pro", amount=29.99, currency="USD", interval="monthly")
        result = await p.create_plan(plan)
        assert result.provider_plan_id == "12345"

    @pytest.mark.asyncio
    async def test_create_plan_error(self, provider):
        p, mock_client = provider
        mock_client.post.return_value = MagicMock(status_code=422)
        plan = BillingPlan(provider_plan_id="", name="Fail", amount=10.0, currency="USD", interval="monthly")
        with pytest.raises(BillingProviderError):
            await p.create_plan(plan)

    @pytest.mark.asyncio
    async def test_create_customer(self, provider):
        p, mock_client = provider
        customer = BillingCustomer(provider_customer_id="", email="a@b.com")
        with pytest.raises(NotImplementedError):
            await p.create_customer(customer)

    @pytest.mark.asyncio
    async def test_create_subscription(self, provider):
        p, mock_client = provider
        mock_client.post.return_value = MagicMock(status_code=201, json=lambda: {"data": {"id": "sub_123", "attributes": {"status": "active", "product_id": "prod_1", "order_id": 1, "customer_id": 1, "product_name": "Pro"}}})
        sub = await p.create_subscription("cust_1", "plan_1")
        assert sub.provider_subscription_id == "sub_123"
        assert sub.status == "active"

    @pytest.mark.asyncio
    async def test_cancel_subscription(self, provider):
        p, mock_client = provider
        mock_client.delete.return_value = MagicMock(status_code=200, json=lambda: {"data": {"id": "sub_123", "attributes": {"status": "cancelled"}}})
        sub = await p.cancel_subscription("sub_123")
        assert sub.status == "cancelled"


# ── PaddleBillingProvider ────────────────────────────────────────────────


class TestPaddleBillingProvider:
    @pytest.fixture
    def provider(self):
        with patch("src.billing.providers.paddle.httpx.AsyncClient") as mock_client_cls:
            from src.billing.providers.paddle import PaddleBillingProvider
            p = PaddleBillingProvider({
                "api_key": "pdl_test",
                "webhook_secret": "whsec_pdl",
                "sandbox": True,
            })
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            yield p, mock_client

    @pytest.mark.asyncio
    async def test_provider_name(self, provider):
        p, _ = provider
        assert p.provider_name == "paddle"

    @pytest.mark.asyncio
    async def test_create_plan(self, provider):
        p, mock_client = provider
        mock_client.post.return_value = MagicMock(status_code=201, json=lambda: {"data": {"id": "pri_123"}})
        plan = BillingPlan(provider_plan_id="", name="Pro", amount=29.99, currency="USD", interval="monthly")
        result = await p.create_plan(plan)
        assert result.provider_plan_id == "pri_123"

    @pytest.mark.asyncio
    async def test_create_customer(self, provider):
        p, mock_client = provider
        customer = BillingCustomer(provider_customer_id="", email="a@b.com")
        with pytest.raises(NotImplementedError):
            await p.create_customer(customer)

    @pytest.mark.asyncio
    async def test_create_subscription(self, provider):
        p, mock_client = provider
        mock_client.post.return_value = MagicMock(status_code=201, json=lambda: {"data": {"id": "sub_123", "attributes": {"status": "active"}}})
        sub = await p.create_subscription("cust_1", "plan_1")
        assert sub.provider_subscription_id == "sub_123"
        assert sub.status == "active"


# ── SureCartBillingProvider ──────────────────────────────────────────────


class TestSureCartBillingProvider:
    @pytest.fixture
    def provider(self):
        with patch("src.billing.providers.surecart.httpx.AsyncClient") as mock_client_cls:
            from src.billing.providers.surecart import SureCartBillingProvider
            p = SureCartBillingProvider({
                "api_token": "sc_test",
                "webhook_secret": "whsec_sc",
            })
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            yield p, mock_client

    @pytest.mark.asyncio
    async def test_provider_name(self, provider):
        p, _ = provider
        assert p.provider_name == "surecart"

    @pytest.mark.asyncio
    async def test_create_plan(self, provider):
        p, mock_client = provider
        mock_client.post.return_value = MagicMock(status_code=201, json=lambda: {"data": {"id": "price_123"}})
        plan = BillingPlan(provider_plan_id="", name="Pro", amount=29.99, currency="usd", interval="monthly")
        result = await p.create_plan(plan)
        assert result.provider_plan_id == "price_123"

    @pytest.mark.asyncio
    async def test_create_customer_not_implemented(self, provider):
        p, mock_client = provider
        customer = BillingCustomer(provider_customer_id="", email="a@b.com")
        with pytest.raises(NotImplementedError):
            await p.create_customer(customer)

    @pytest.mark.asyncio
    async def test_create_subscription(self, provider):
        p, mock_client = provider
        mock_client.post.return_value = MagicMock(status_code=201, json=lambda: {"data": {"id": "sub_123", "attributes": {"status": "active", "customer_id": "cust_1", "plan_id": "plan_1"}}})
        sub = await p.create_subscription("cust_1", "plan_1")
        assert sub.provider_subscription_id == "sub_123"
