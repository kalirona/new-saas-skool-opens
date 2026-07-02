import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from sqlmodel import select
from src.db.usergroup_user import UserGroupUser


# ── Helper fixtures ──────────────────────────────────────────────────────


@pytest.fixture
async def community(db, org):
    from src.db.communities.communities import Community
    c = Community(
        id=1,
        name="Test Community",
        org_id=org.id,
        community_uuid="comm_test",
        creation_date=str(datetime.now()),
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
        id=1,
        name="Pro Plan",
        plan_uuid="plan_test",
        price=29.99,
        interval="monthly",
        community_id=community.id,
        org_id=org.id,
        billing_provider="stripe",
        billing_provider_plan_id="price_stripe_123",
        creation_date=str(datetime.now()),
        update_date=str(datetime.now()),
    )
    db.add(mp)
    await db.commit()
    await db.refresh(mp)
    return mp


@pytest.fixture
async def usergroup(db, org):
    from src.db.usergroups import UserGroup
    ug = UserGroup(
        id=1,
        name="Premium Members",
        org_id=org.id,
        usergroup_uuid="ug_test",
        creation_date=str(datetime.now()),
        update_date=str(datetime.now()),
    )
    db.add(ug)
    await db.commit()
    await db.refresh(ug)
    return ug


@pytest.fixture
async def plan_with_usergroup(db, org, community, usergroup):
    from src.db.communities.membership_plans import MembershipPlan
    mp = MembershipPlan(
        id=2,
        name="Premium Plan",
        plan_uuid="plan_ug_test",
        price=49.99,
        interval="monthly",
        community_id=community.id,
        org_id=org.id,
        usergroup_id=usergroup.id,
        billing_provider="stripe",
        billing_provider_plan_id="price_ug_123",
        creation_date=str(datetime.now()),
        update_date=str(datetime.now()),
    )
    db.add(mp)
    await db.commit()
    await db.refresh(mp)
    return mp


@pytest.fixture
async def community_member(db, org, community, membership_plan, regular_user):
    from src.db.communities.community_members import CommunityMember
    now = str(datetime.now())
    cm = CommunityMember(
        id=1,
        community_id=community.id,
        user_id=regular_user.id,
        org_id=org.id,
        plan_id=membership_plan.id,
        status="active",
        billing_provider_subscription_id="sub_stripe_123",
        billing_provider="stripe",
        joined_date=now,
        creation_date=now,
        update_date=now,
    )
    db.add(cm)
    await db.commit()
    await db.refresh(cm)
    return cm


# ── Usergroup helpers ────────────────────────────────────────────────────


class TestAddMemberToUsergroup:
    @pytest.mark.asyncio
    async def test_adds_when_not_exists(self, db, org, plan_with_usergroup, regular_user):
        from src.services.payments.lifecycle import add_member_to_usergroup
        await add_member_to_usergroup(db, plan_with_usergroup, regular_user.id, org.id)

        result = await db.execute(
            select(UserGroupUser).where(
                UserGroupUser.usergroup_id == plan_with_usergroup.usergroup_id,
                UserGroupUser.user_id == regular_user.id,
            )
        )
        assert result.scalars().first() is not None

    @pytest.mark.asyncio
    async def test_skips_when_plan_has_no_usergroup(self, db, org, membership_plan, regular_user):
        from src.services.payments.lifecycle import add_member_to_usergroup
        assert membership_plan.usergroup_id is None
        await add_member_to_usergroup(db, membership_plan, regular_user.id, org.id)

    @pytest.mark.asyncio
    async def test_idempotent_when_already_exists(self, db, org, plan_with_usergroup, regular_user):
        from src.services.payments.lifecycle import add_member_to_usergroup
        now = str(datetime.now())
        existing = UserGroupUser(
            usergroup_id=plan_with_usergroup.usergroup_id,
            user_id=regular_user.id,
            org_id=org.id,
            creation_date=now,
            update_date=now,
        )
        db.add(existing)
        await db.commit()

        await add_member_to_usergroup(db, plan_with_usergroup, regular_user.id, org.id)


class TestRemoveMemberFromUsergroup:
    @pytest.mark.asyncio
    async def test_removes_when_exists(self, db, org, plan_with_usergroup, regular_user):
        from src.services.payments.lifecycle import add_member_to_usergroup, remove_member_from_usergroup
        await add_member_to_usergroup(db, plan_with_usergroup, regular_user.id, org.id)
        await remove_member_from_usergroup(db, plan_with_usergroup, regular_user.id)

        result = await db.execute(
            select(UserGroupUser).where(
                UserGroupUser.usergroup_id == plan_with_usergroup.usergroup_id,
                UserGroupUser.user_id == regular_user.id,
            )
        )
        assert result.scalars().first() is None

    @pytest.mark.asyncio
    async def test_skips_when_plan_has_no_usergroup(self, db, membership_plan, regular_user):
        from src.services.payments.lifecycle import remove_member_from_usergroup
        await remove_member_from_usergroup(db, membership_plan, regular_user.id)

    @pytest.mark.asyncio
    async def test_noop_when_not_a_member(self, db, plan_with_usergroup, regular_user):
        from src.services.payments.lifecycle import remove_member_from_usergroup
        await remove_member_from_usergroup(db, plan_with_usergroup, regular_user.id)


# ── Member CRUD ──────────────────────────────────────────────────────────


class TestFindMemberBySubscription:
    @pytest.mark.asyncio
    async def test_finds_existing(self, db, community_member):
        from src.services.payments.lifecycle import find_member_by_subscription
        member = await find_member_by_subscription(db, "sub_stripe_123")
        assert member is not None
        assert member.id == community_member.id

    @pytest.mark.asyncio
    async def test_returns_none_for_missing(self, db):
        from src.services.payments.lifecycle import find_member_by_subscription
        member = await find_member_by_subscription(db, "sub_nonexistent")
        assert member is None


class TestCreateMember:
    @pytest.mark.asyncio
    async def test_creates_with_minimal_args(self, db, org, community, membership_plan, regular_user):
        from src.services.payments.lifecycle import create_member
        member = await create_member(db, membership_plan, community, org, regular_user.id)
        assert member.status == "active"
        assert member.user_id == regular_user.id
        assert member.community_id == community.id
        assert member.plan_id == membership_plan.id
        assert member.billing_provider_subscription_id is None

    @pytest.mark.asyncio
    async def test_creates_with_subscription(self, db, org, community, membership_plan, regular_user):
        from src.services.payments.lifecycle import create_member
        member = await create_member(
            db, membership_plan, community, org, regular_user.id,
            status="trial", subscription_id="sub_trial_123", provider="stripe",
        )
        assert member.status == "trial"
        assert member.billing_provider_subscription_id == "sub_trial_123"
        assert member.billing_provider == "stripe"


class TestUpsertMember:
    @pytest.mark.asyncio
    async def test_creates_new(self, db, org, community, membership_plan, regular_user):
        from src.services.payments.lifecycle import upsert_member
        member = await upsert_member(
            db, membership_plan, community, org, regular_user.id,
            status="active", subscription_id="sub_new", provider="stripe",
        )
        assert member.status == "active"
        assert member.billing_provider_subscription_id == "sub_new"

    @pytest.mark.asyncio
    async def test_updates_existing(self, db, org, community, membership_plan, regular_user, community_member):
        from src.services.payments.lifecycle import upsert_member
        member = await upsert_member(
            db, membership_plan, community, org, regular_user.id,
            status="cancelled", subscription_id="sub_stripe_123", provider="stripe",
        )
        assert member.id == community_member.id
        assert member.status == "cancelled"


class TestFindOrCreatePendingMember:
    @pytest.mark.asyncio
    async def test_creates_when_not_found(self, db, org, community, membership_plan, regular_user):
        from src.services.payments.lifecycle import find_or_create_pending_member
        member = await find_or_create_pending_member(
            db, membership_plan, community, org, regular_user.id, "stripe",
        )
        assert member.status == "pending"
        assert member.billing_provider == "stripe"

    @pytest.mark.asyncio
    async def test_returns_existing_pending(self, db, org, community, membership_plan, regular_user):
        from src.services.payments.lifecycle import find_or_create_pending_member, create_member
        existing = await create_member(
            db, membership_plan, community, org, regular_user.id,
            status="pending", provider="stripe",
        )
        member = await find_or_create_pending_member(
            db, membership_plan, community, org, regular_user.id, "stripe",
        )
        assert member.id == existing.id


# ── Status transitions ───────────────────────────────────────────────────


class TestApplySubscriptionStatus:
    @pytest.mark.asyncio
    async def test_sets_active_and_adds_usergroup(self, db, org, community, plan_with_usergroup, regular_user):
        from src.services.payments.lifecycle import apply_subscription_status, create_member
        member = await create_member(
            db, plan_with_usergroup, community, org, regular_user.id,
            subscription_id="sub_active", provider="stripe",
        )
        await apply_subscription_status(db, member, plan_with_usergroup, org, "active")
        assert member.status == "active"

        result = await db.execute(
            select(UserGroupUser).where(
                UserGroupUser.usergroup_id == plan_with_usergroup.usergroup_id,
                UserGroupUser.user_id == regular_user.id,
            )
        )
        assert result.scalars().first() is not None

    @pytest.mark.asyncio
    async def test_sets_cancelled_and_removes_usergroup(self, db, org, community, plan_with_usergroup, regular_user):
        from src.services.payments.lifecycle import apply_subscription_status, create_member, add_member_to_usergroup
        member = await create_member(
            db, plan_with_usergroup, community, org, regular_user.id,
            subscription_id="sub_cancel", provider="stripe",
        )
        await add_member_to_usergroup(db, plan_with_usergroup, regular_user.id, org.id)
        await apply_subscription_status(db, member, plan_with_usergroup, org, "canceled")
        assert member.status == "cancelled"

        result = await db.execute(
            select(UserGroupUser).where(
                UserGroupUser.usergroup_id == plan_with_usergroup.usergroup_id,
                UserGroupUser.user_id == regular_user.id,
            )
        )
        assert result.scalars().first() is None

    @pytest.mark.asyncio
    async def test_sets_trial(self, db, org, community, membership_plan, regular_user):
        from src.services.payments.lifecycle import apply_subscription_status, create_member
        member = await create_member(
            db, membership_plan, community, org, regular_user.id,
            subscription_id="sub_trial", provider="stripe",
        )
        await apply_subscription_status(db, member, membership_plan, org, "trialing")
        assert member.status == "trial"

    @pytest.mark.asyncio
    async def test_sets_past_due(self, db, org, community, membership_plan, regular_user):
        from src.services.payments.lifecycle import apply_subscription_status, create_member
        member = await create_member(
            db, membership_plan, community, org, regular_user.id,
            subscription_id="sub_due", provider="stripe",
        )
        await apply_subscription_status(db, member, membership_plan, org, "past_due")
        assert member.status == "past_due"

    @pytest.mark.asyncio
    async def test_sets_expired(self, db, org, community, membership_plan, regular_user):
        from src.services.payments.lifecycle import apply_subscription_status, create_member
        member = await create_member(
            db, membership_plan, community, org, regular_user.id,
            subscription_id="sub_exp", provider="stripe",
        )
        await apply_subscription_status(db, member, membership_plan, org, "incomplete_expired")
        assert member.status == "expired"

    @pytest.mark.asyncio
    async def test_preserves_active_with_cancel_at_period_end(self, db, org, community, membership_plan, regular_user):
        from src.services.payments.lifecycle import apply_subscription_status, create_member
        member = await create_member(
            db, membership_plan, community, org, regular_user.id,
            subscription_id="sub_cancel_at_end", provider="stripe",
        )
        await apply_subscription_status(
            db, member, membership_plan, org, "active", cancel_at_period_end=True, current_period_end=2000000000,
        )
        assert member.status == "active"
        assert member.expires_date is not None

    @pytest.mark.asyncio
    async def test_sets_expires_date(self, db, org, community, membership_plan, regular_user):
        from src.services.payments.lifecycle import apply_subscription_status, create_member
        member = await create_member(
            db, membership_plan, community, org, regular_user.id,
            subscription_id="sub_expires", provider="stripe",
        )
        await apply_subscription_status(db, member, membership_plan, org, "active", current_period_end=2000000000)
        assert member.expires_date is not None
        assert "2033" in member.expires_date

    @pytest.mark.asyncio
    async def test_map_stripe_status_all_values(self):
        from src.services.payments.lifecycle import MAP_STRIPE_SUB_STATUS
        assert MAP_STRIPE_SUB_STATUS["trialing"] == "trial"
        assert MAP_STRIPE_SUB_STATUS["active"] == "active"
        assert MAP_STRIPE_SUB_STATUS["past_due"] == "past_due"
        assert MAP_STRIPE_SUB_STATUS["canceled"] == "cancelled"
        assert MAP_STRIPE_SUB_STATUS["unpaid"] == "past_due"
        assert MAP_STRIPE_SUB_STATUS["incomplete"] == "pending"
        assert MAP_STRIPE_SUB_STATUS["incomplete_expired"] == "expired"


# ── Dependency lookup ────────────────────────────────────────────────────


class TestLookupSubscriptionDependencies:
    @pytest.mark.asyncio
    async def test_resolves_from_plan_uuid_metadata(self, db, org, community, membership_plan):
        from src.services.payments.lifecycle import lookup_subscription_dependencies
        metadata = {"plan_uuid": "plan_test", "community_id": str(community.id)}
        plan, resolved_community, resolved_org, sub_id = await lookup_subscription_dependencies(
            db, {"id": "sub_123", "plan_id": None}, metadata
        )
        assert plan is not None
        assert resolved_community.id == community.id
        assert resolved_org.id == org.id

    @pytest.mark.asyncio
    async def test_resolves_from_subscription_plan_id(self, db, org, community, membership_plan):
        from src.services.payments.lifecycle import lookup_subscription_dependencies
        plan, resolved_community, resolved_org, sub_id = await lookup_subscription_dependencies(
            db, {"id": "sub_123", "plan_id": "price_stripe_123"}, {"plan_uuid": "plan_test", "community_id": str(community.id)}
        )
        assert plan is not None

    @pytest.mark.asyncio
    async def test_returns_none_when_no_plan_found(self, db):
        from src.services.payments.lifecycle import lookup_subscription_dependencies
        plan, community, org, sub_id = await lookup_subscription_dependencies(
            db, {"id": "sub_missing", "plan_id": "price_nonexistent"}, {}
        )
        assert plan is None


# ── Provider subscription proxy ──────────────────────────────────────────


class TestGetProviderSubscription:
    @pytest.mark.asyncio
    async def test_returns_subscription_on_success(self):
        from src.services.payments.lifecycle import get_provider_subscription
        provider = MagicMock()
        provider.get_subscription = AsyncMock(return_value=MagicMock(provider_subscription_id="sub_123"))
        result = await get_provider_subscription(provider, "sub_123")
        assert result.provider_subscription_id == "sub_123"

    @pytest.mark.asyncio
    async def test_returns_none_on_exception(self):
        from src.services.payments.lifecycle import get_provider_subscription
        provider = MagicMock()
        provider.get_subscription = AsyncMock(side_effect=Exception("API down"))
        result = await get_provider_subscription(provider, "sub_fail")
        assert result is None
