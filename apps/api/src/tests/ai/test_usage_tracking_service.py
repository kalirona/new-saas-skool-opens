import pytest
from datetime import datetime
from sqlmodel import select
from src.db.ai.usage_tracking import AIRequestLog, AIQuota
from src.services.ai.studio.usage_tracking_service import AIUsageTrackingService



class TestAIUsageTrackingService:
    @pytest.mark.asyncio
    async def test_log_request_creates_record(self, db, org, admin_user):
        await AIUsageTrackingService.log_request(
            org_id=org.id, user_id=admin_user.id, feature="chat",
            provider="openai", model_name="gpt-4o",
            prompt_tokens=100, completion_tokens=50, estimated_cost=0.002,
            success=True, db_session=db,
        )
        result = (await db.execute(select(AIRequestLog))).scalars().all()
        assert len(result) == 1
        assert result[0].org_id == org.id
        assert result[0].total_tokens == 150
        assert result[0].estimated_cost == 0.002

    @pytest.mark.asyncio
    async def test_log_request_sets_error_message(self, db, org, admin_user):
        await AIUsageTrackingService.log_request(
            org_id=org.id, user_id=admin_user.id, feature="chat",
            provider="openai", model_name="gpt-4o",
            success=False, error_message="Rate limit exceeded", db_session=db,
        )
        result = (await db.execute(select(AIRequestLog))).scalars().first()
        assert result.success is False
        assert result.error_message == "Rate limit exceeded"

    @pytest.mark.asyncio
    async def test_log_request_with_duration_and_request_id(self, db, org, admin_user):
        await AIUsageTrackingService.log_request(
            org_id=org.id, user_id=admin_user.id, feature="studio",
            provider="anthropic", model_name="claude-3",
            duration_ms=1500, request_id="req_abc", db_session=db,
        )
        result = (await db.execute(select(AIRequestLog))).scalars().first()
        assert result.duration_ms == 1500
        assert result.request_id == "req_abc"

    @pytest.mark.asyncio
    async def test_log_request_noop_without_db_session(self, db, org, admin_user):
        await AIUsageTrackingService.log_request(
            org_id=org.id, user_id=admin_user.id, feature="test",
            provider="test", model_name="test",
        )
        result = (await db.execute(select(AIRequestLog))).scalars().all()
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_or_create_quota_creates_new(self, db, org):
        quota = await AIUsageTrackingService.get_or_create_quota(org.id, db)
        assert quota.org_id == org.id
        assert quota.enabled is True
        assert quota.daily_request_limit == 1000
        assert quota.monthly_token_limit == 1_000_000
        assert quota.monthly_cost_limit == 50.0

    @pytest.mark.asyncio
    async def test_get_or_create_quota_returns_existing(self, db, org):
        first = await AIUsageTrackingService.get_or_create_quota(org.id, db)
        second = await AIUsageTrackingService.get_or_create_quota(org.id, db)
        assert first.id == second.id

    @pytest.mark.asyncio
    async def test_update_quota_modifies_fields(self, db, org):
        await AIUsageTrackingService.get_or_create_quota(org.id, db)
        updated = await AIUsageTrackingService.update_quota(
            org.id, db, daily_request_limit=500, monthly_cost_limit=100.0,
        )
        assert updated.daily_request_limit == 500
        assert updated.monthly_cost_limit == 100.0

    @pytest.mark.asyncio
    async def test_update_quota_returns_none_if_not_found(self, db):
        result = await AIUsageTrackingService.update_quota(999, db, enabled=False)
        assert result is None

    @pytest.mark.asyncio
    async def test_check_quota_disabled(self, db, org):
        quota = await AIUsageTrackingService.get_or_create_quota(org.id, db)
        quota.enabled = False
        db.add(quota)
        await db.commit()

        within, info = await AIUsageTrackingService.check_quota(org.id, db)
        assert within is False
        assert "disabled" in info["reason"]

    @pytest.mark.asyncio
    async def test_check_quota_within_limits(self, db, org):
        quota = await AIUsageTrackingService.get_or_create_quota(org.id, db)
        quota.daily_request_limit = 1000
        quota.monthly_token_limit = 1_000_000
        quota.monthly_cost_limit = 50.0
        db.add(quota)
        await db.commit()

        within, info = await AIUsageTrackingService.check_quota(org.id, db, estimated_tokens=100)
        assert within is True
        assert len(info["violations"]) == 0

    @pytest.mark.asyncio
    async def test_check_quota_exceeds_daily_limit(self, db, org):
        quota = await AIUsageTrackingService.get_or_create_quota(org.id, db)
        quota.daily_request_limit = 0
        db.add(quota)
        await db.commit()

        within, info = await AIUsageTrackingService.check_quota(org.id, db)
        assert within is False
        assert any("Daily request limit" in v for v in info["violations"])

    @pytest.mark.asyncio
    async def test_check_quota_exceeds_monthly_token(self, db, org):
        quota = await AIUsageTrackingService.get_or_create_quota(org.id, db)
        quota.monthly_token_limit = 50
        db.add(quota)
        await db.commit()

        within, info = await AIUsageTrackingService.check_quota(org.id, db, estimated_tokens=100)
        assert within is False
        assert any("Monthly token limit" in v for v in info["violations"])

    @pytest.mark.asyncio
    async def test_check_quota_exceeds_monthly_cost(self, db, org, admin_user):
        quota = await AIUsageTrackingService.get_or_create_quota(org.id, db)
        quota.monthly_cost_limit = 0.0
        db.add(quota)
        await db.commit()

        await AIUsageTrackingService.log_request(
            org_id=org.id, user_id=admin_user.id, feature="chat",
            provider="openai", model_name="gpt-4o",
            estimated_cost=0.1, db_session=db,
        )

        within, info = await AIUsageTrackingService.check_quota(org.id, db)
        assert within is False
        assert any("Monthly cost limit" in v for v in info["violations"])

    @pytest.mark.asyncio
    async def test_get_usage_summary(self, db, org, admin_user):
        await AIUsageTrackingService.log_request(
            org_id=org.id, user_id=admin_user.id, feature="chat",
            provider="openai", model_name="gpt-4o",
            prompt_tokens=100, completion_tokens=50, estimated_cost=0.002,
            success=True, db_session=db,
        )
        await AIUsageTrackingService.log_request(
            org_id=org.id, user_id=admin_user.id, feature="chat",
            provider="anthropic", model_name="claude-3",
            prompt_tokens=200, completion_tokens=100, estimated_cost=0.005,
            success=False, db_session=db,
        )

        summary = await AIUsageTrackingService.get_usage_summary(org.id, db)
        assert summary["total_requests"] == 2
        assert summary["total_failures"] == 1
        assert summary["monthly_tokens"] == 450
        assert summary["monthly_cost"] > 0
        assert len(summary["top_providers"]) == 2
        assert summary["quota"]["enabled"] is True

    @pytest.mark.asyncio
    async def test_get_usage_summary_empty(self, db, org):
        summary = await AIUsageTrackingService.get_usage_summary(org.id, db)
        assert summary["total_requests"] == 0
        assert summary["total_failures"] == 0
        assert summary["monthly_tokens"] == 0
