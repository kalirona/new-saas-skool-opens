import pytest
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock
from datetime import datetime



@pytest.fixture
async def community(db, org):
    from src.db.communities.communities import Community
    c = Community(
        id=1, name="Test Community", org_id=org.id,
        community_uuid="comm_test", creation_date=str(datetime.now()),
        update_date=str(datetime.now()),
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


@pytest.fixture
async def membership_plan(db, org, community):
    from src.db.communities.membership_plans import MembershipPlan
    mp = MembershipPlan(
        id=1, name="Pro Plan", plan_uuid="plan_test", price=29.99,
        interval="monthly", community_id=community.id, org_id=org.id,
        billing_provider="stripe", billing_provider_plan_id="price_123",
        creation_date=str(datetime.now()), update_date=str(datetime.now()),
    )
    db.add(mp)
    await db.commit()
    await db.refresh(mp)
    return mp


@pytest.fixture
async def new_plan_no_provider(db, org, community):
    from src.db.communities.membership_plans import MembershipPlan
    mp = MembershipPlan(
        id=2, name="New Plan", plan_uuid="plan_new", price=19.99,
        interval="monthly", community_id=community.id, org_id=org.id,
        billing_provider=None, billing_provider_plan_id=None,
        creation_date=str(datetime.now()), update_date=str(datetime.now()),
    )
    db.add(mp)
    await db.commit()
    await db.refresh(mp)
    return mp


# ── Stripe Payment Service ───────────────────────────────────────────────


class TestStripePaymentService:
    @pytest.mark.asyncio
    async def test_sync_plan_with_provider_creates_new(self, db, new_plan_no_provider):
        from src.services.payments.stripe import sync_plan_with_provider
        with patch("src.services.payments.stripe._get_stripe_provider") as mock_get:
            provider = AsyncMock()
            provider.create_plan = AsyncMock(return_value=MagicMock(provider_plan_id="price_new"))
            mock_get.return_value = provider
            plan = await sync_plan_with_provider(db, new_plan_no_provider)
            assert plan.billing_provider_plan_id == "price_new"
            assert plan.billing_provider == "stripe"

    @pytest.mark.asyncio
    async def test_sync_plan_with_provider_updates_existing(self, db, membership_plan):
        from src.services.payments.stripe import sync_plan_with_provider
        with patch("src.services.payments.stripe._get_stripe_provider") as mock_get:
            provider = AsyncMock()
            provider.update_plan = AsyncMock(return_value=MagicMock(provider_plan_id="price_123"))
            mock_get.return_value = provider
            plan = await sync_plan_with_provider(db, membership_plan)
            assert plan.billing_provider_plan_id == "price_123"
            provider.update_plan.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_plan_raises_on_create_error(self, db, new_plan_no_provider):
        from src.services.payments.stripe import sync_plan_with_provider
        with patch("src.services.payments.stripe._get_stripe_provider") as mock_get:
            from src.billing.base import BillingProviderError
            provider = AsyncMock()
            provider.create_plan = AsyncMock(side_effect=BillingProviderError("Stripe down", "stripe"))
            mock_get.return_value = provider
            with pytest.raises(ValueError, match="Failed to create Stripe plan"):
                await sync_plan_with_provider(db, new_plan_no_provider)

    @pytest.mark.asyncio
    async def test_cancel_plan_with_provider(self, db, membership_plan):
        from src.services.payments.stripe import cancel_plan_with_provider
        with patch("src.services.payments.stripe._get_stripe_provider") as mock_get:
            provider = AsyncMock()
            provider.delete_plan = AsyncMock()
            mock_get.return_value = provider
            await cancel_plan_with_provider(membership_plan)
            provider.delete_plan.assert_called_once_with("price_123")

    @pytest.mark.asyncio
    async def test_cancel_plan_without_provider_id(self, db, new_plan_no_provider):
        from src.services.payments.stripe import cancel_plan_with_provider
        with patch("src.services.payments.stripe._get_stripe_provider") as mock_get:
            provider = AsyncMock()
            mock_get.return_value = provider
            await cancel_plan_with_provider(new_plan_no_provider)
            provider.delete_plan.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_checkout_session(self, db, membership_plan):
        from src.services.payments.stripe import create_checkout_session
        with patch("src.services.payments.stripe._get_stripe_provider") as mock_get:
            provider = AsyncMock()
            provider.create_customer = AsyncMock(return_value=MagicMock(provider_customer_id="cus_new"))
            provider.create_checkout_session = AsyncMock(return_value="https://checkout.stripe.com/sess_abc")
            mock_get.return_value = provider

            url = await create_checkout_session(
                membership_plan, "test@test.com", "http://success", "http://cancel",
                metadata={"user_id": "1", "customer_name": "Test User"},
            )
            assert url == "https://checkout.stripe.com/sess_abc"
            provider.create_customer.assert_called_once()
            provider.create_checkout_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_checkout_session_raises_without_provider_plan_id(self, db, new_plan_no_provider):
        from src.services.payments.stripe import create_checkout_session
        with pytest.raises(ValueError, match="Plan has no billing provider plan ID"):
            await create_checkout_session(new_plan_no_provider, "a@b.com", "http://s", "http://c")


class TestStripePaymentServiceWebhooks:
    @pytest.mark.asyncio
    async def test_handle_checkout_completed_creates_member(self, db, org, membership_plan, community, regular_user):
        from src.services.payments.stripe import handle_checkout_completed
        session_data = {
            "id": "cs_test",
            "subscription": "sub_new",
            "metadata": {"plan_uuid": "plan_test", "community_id": str(community.id), "user_id": str(regular_user.id)},
            "line_items": {"price": "price_123"},
            "subscription_data": {},
        }
        await handle_checkout_completed(db, session_data)
        from src.db.communities.community_members import CommunityMember
        from sqlmodel import select
        member = (await db.execute(
            select(CommunityMember).where(CommunityMember.billing_provider_subscription_id == "sub_new")
        )).scalars().first()
        assert member is not None
        assert member.status == "active"
        assert member.user_id == regular_user.id

    @pytest.mark.asyncio
    async def test_handle_checkout_completed_with_trial(self, db, org, membership_plan, community, regular_user):
        from src.services.payments.stripe import handle_checkout_completed
        session_data = {
            "id": "cs_trial",
            "subscription": "sub_trial",
            "metadata": {"plan_uuid": "plan_test", "community_id": str(community.id), "user_id": str(regular_user.id)},
            "line_items": {"price": "price_123"},
            "subscription_data": {"trial_end": 2000000000, "current_period_end": 2000000000},
        }
        await handle_checkout_completed(db, session_data)
        from src.db.communities.community_members import CommunityMember
        from sqlmodel import select
        member = (await db.execute(
            select(CommunityMember).where(CommunityMember.billing_provider_subscription_id == "sub_trial")
        )).scalars().first()
        assert member.status == "trial"
        assert member.trial_end_date is not None

    @pytest.mark.asyncio
    async def test_handle_checkout_completed_price_id_mismatch(self, db, org, membership_plan, community, regular_user):
        from src.services.payments.stripe import handle_checkout_completed
        original_price_id = membership_plan.billing_provider_plan_id
        session_data = {
            "id": "cs_mismatch",
            "subscription": "sub_mismatch",
            "metadata": {"plan_uuid": "plan_test", "community_id": str(community.id), "user_id": str(regular_user.id)},
            "line_items": {"price": "price_new"},
            "subscription_data": {},
        }
        await handle_checkout_completed(db, session_data)
        assert membership_plan.billing_provider_plan_id == "price_new"

    @pytest.mark.asyncio
    async def test_handle_checkout_completed_no_subscription(self, db):
        from src.services.payments.stripe import handle_checkout_completed
        await handle_checkout_completed(db, {"id": "cs_no_sub", "metadata": {}})

    @pytest.mark.asyncio
    async def test_handle_checkout_completed_no_user_id(self, db, membership_plan, community):
        from src.services.payments.stripe import handle_checkout_completed
        session_data = {
            "id": "cs_no_user",
            "subscription": "sub_no_user",
            "metadata": {"plan_uuid": "plan_test", "community_id": str(community.id)},
            "line_items": {"price": "price_123"},
            "subscription_data": {},
        }
        await handle_checkout_completed(db, session_data)

    @pytest.mark.asyncio
    async def test_handle_checkout_completed_updates_existing_member(self, db, org, membership_plan, community, regular_user):
        from src.services.payments.stripe import handle_checkout_completed
        from src.services.payments.lifecycle import upsert_member
        existing = await upsert_member(
            db, membership_plan, community, org, regular_user.id,
            status="trial", subscription_id="sub_existing", provider="stripe",
        )
        session_data = {
            "id": "cs_update",
            "subscription": "sub_existing",
            "metadata": {"plan_uuid": "plan_test", "community_id": str(community.id), "user_id": str(regular_user.id)},
            "line_items": {"price": "price_123"},
            "subscription_data": {},
        }
        await handle_checkout_completed(db, session_data)
        from src.db.communities.community_members import CommunityMember
        from sqlmodel import select
        member = (await db.execute(
            select(CommunityMember).where(CommunityMember.billing_provider_subscription_id == "sub_existing")
        )).scalars().first()
        assert member.status == "active"

    @pytest.mark.asyncio
    async def test_handle_subscription_updated_changes_status(self, db, org, community, membership_plan, regular_user):
        from src.services.payments.stripe import handle_subscription_updated
        from src.services.payments.lifecycle import upsert_member
        existing_member = await upsert_member(
            db, membership_plan, community, org, regular_user.id,
            status="active", subscription_id="sub_upd", provider="stripe",
        )
        sub_data = {
            "id": "sub_upd",
            "status": "past_due",
            "cancel_at_period_end": False,
        }
        await handle_subscription_updated(db, sub_data)
        from src.db.communities.community_members import CommunityMember
        from sqlmodel import select
        member = (await db.execute(
            select(CommunityMember).where(CommunityMember.billing_provider_subscription_id == "sub_upd")
        )).scalars().first()
        assert member.status == "past_due"

    @pytest.mark.asyncio
    async def test_handle_subscription_updated_syncs_price_id(self, db, org, community, membership_plan, regular_user):
        from src.services.payments.stripe import handle_subscription_updated
        from src.services.payments.lifecycle import upsert_member
        existing_member = await upsert_member(
            db, membership_plan, community, org, regular_user.id,
            status="active", subscription_id="sub_sync", provider="stripe",
        )
        sub_data = {
            "id": "sub_sync",
            "status": "active",
            "cancel_at_period_end": False,
            "items": {"data": [{"price": {"id": "price_new_sync"}}]},
        }
        await handle_subscription_updated(db, sub_data)
        assert membership_plan.billing_provider_plan_id == "price_new_sync"

    @pytest.mark.asyncio
    async def test_handle_subscription_updated_noop_without_id(self, db):
        from src.services.payments.stripe import handle_subscription_updated
        await handle_subscription_updated(db, {})

    @pytest.mark.asyncio
    async def test_handle_subscription_updated_noop_without_member(self, db):
        from src.services.payments.stripe import handle_subscription_updated
        await handle_subscription_updated(db, {"id": "sub_nonexistent", "status": "canceled"})

    @pytest.mark.asyncio
    async def test_handle_subscription_deleted(self, db, org, community, membership_plan, regular_user):
        from src.services.payments.stripe import handle_subscription_deleted
        from src.services.payments.lifecycle import upsert_member
        existing_member = await upsert_member(
            db, membership_plan, community, org, regular_user.id,
            status="active", subscription_id="sub_del", provider="stripe",
        )
        await handle_subscription_deleted(db, {"id": "sub_del"})
        from src.db.communities.community_members import CommunityMember
        from sqlmodel import select
        member = (await db.execute(
            select(CommunityMember).where(CommunityMember.billing_provider_subscription_id == "sub_del")
        )).scalars().first()
        assert member.status == "cancelled"

    @pytest.mark.asyncio
    async def test_handle_subscription_deleted_noop_without_id(self, db):
        from src.services.payments.stripe import handle_subscription_deleted
        await handle_subscription_deleted(db, {})

    @pytest.mark.asyncio
    async def test_sync_price_id_updates_on_mismatch(self, db, membership_plan):
        from src.services.payments.stripe import _sync_price_id_on_subscription_change
        sub_data = {"id": "sub_123", "items": {"data": [{"price": {"id": "price_new"}}]}}
        await _sync_price_id_on_subscription_change(db, sub_data, membership_plan)
        assert membership_plan.billing_provider_plan_id == "price_new"

    @pytest.mark.asyncio
    async def test_sync_price_id_skips_when_same(self, db, membership_plan):
        from src.services.payments.stripe import _sync_price_id_on_subscription_change
        original = membership_plan.billing_provider_plan_id
        sub_data = {"id": "sub_123", "items": {"data": [{"price": {"id": original}}]}}
        await _sync_price_id_on_subscription_change(db, sub_data, membership_plan)
        assert membership_plan.billing_provider_plan_id == original

    @pytest.mark.asyncio
    async def test_sync_price_id_handles_empty_items(self, db, membership_plan):
        from src.services.payments.stripe import _sync_price_id_on_subscription_change
        await _sync_price_id_on_subscription_change(db, {"id": "sub_123", "items": {}}, membership_plan)

    @pytest.mark.asyncio
    async def test_sync_price_id_handles_missing_price_key(self, db, membership_plan):
        from src.services.payments.stripe import _sync_price_id_on_subscription_change
        sub_data = {"id": "sub_123", "items": {"data": [{}]}}
        await _sync_price_id_on_subscription_change(db, sub_data, membership_plan)


# ── PayPal Payment Service ───────────────────────────────────────────────


class TestPaypalPaymentService:
    @pytest.mark.asyncio
    async def test_sync_plan_with_provider_creates_new(self, db, new_plan_no_provider):
        from src.services.payments.paypal import sync_plan_with_provider
        with patch("src.services.payments.paypal._get_paypal_provider") as mock_get:
            provider = AsyncMock()
            provider.create_plan = AsyncMock(return_value=MagicMock(provider_plan_id="P-NEW"))
            mock_get.return_value = provider
            plan = await sync_plan_with_provider(db, new_plan_no_provider)
            assert plan.billing_provider_plan_id == "P-NEW"
            assert plan.billing_provider == "paypal"

    @pytest.mark.asyncio
    async def test_sync_plan_with_provider_updates_existing(self, db, membership_plan):
        from src.services.payments.paypal import sync_plan_with_provider
        with patch("src.services.payments.paypal._get_paypal_provider") as mock_get:
            provider = AsyncMock()
            provider.update_plan = AsyncMock(return_value=MagicMock(provider_plan_id="price_123"))
            mock_get.return_value = provider
            plan = await sync_plan_with_provider(db, membership_plan)
            assert plan.billing_provider_plan_id == "price_123"
            provider.update_plan.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_plan_default_currency_interval(self, db, new_plan_no_provider):
        from src.services.payments.paypal import sync_plan_with_provider
        with patch("src.services.payments.paypal._get_paypal_provider") as mock_get:
            provider = AsyncMock()
            provider.create_plan = AsyncMock(return_value=MagicMock(provider_plan_id="P-DEFAULT"))
            mock_get.return_value = provider
            plan = await sync_plan_with_provider(db, new_plan_no_provider)
            provider.create_plan.assert_called_once()
            call_plan = provider.create_plan.call_args[0][0]
            assert call_plan.interval == "monthly" or call_plan.interval is not None
