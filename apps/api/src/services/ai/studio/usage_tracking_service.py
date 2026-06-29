from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.ai.usage_tracking import AIRequestLog, AIQuota

logger = logging.getLogger(__name__)


class AIUsageTrackingService:
    """Per-workspace AI usage tracking and quota enforcement."""

    @staticmethod
    async def log_request(
        org_id: int,
        user_id: int,
        feature: str,
        provider: str,
        model_name: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        estimated_cost: float = 0.0,
        success: bool = True,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
        request_id: Optional[str] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> None:
        if db_session is None:
            return
        log = AIRequestLog(
            org_id=org_id,
            user_id=user_id,
            feature=feature,
            provider=provider,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated_cost=round(estimated_cost, 6),
            success=success,
            error_message=error_message,
            duration_ms=duration_ms,
            request_id=request_id,
            created_at=str(datetime.now()),
        )
        db_session.add(log)
        await db_session.commit()

    @staticmethod
    async def get_or_create_quota(
        org_id: int,
        db_session: AsyncSession,
    ) -> AIQuota:
        quota = (
            await db_session.execute(
                select(AIQuota).where(AIQuota.org_id == org_id)
            )
        ).scalars().first()
        if quota:
            return quota

        quota = AIQuota(
            org_id=org_id,
            creation_date=str(datetime.now()),
            update_date=str(datetime.now()),
        )
        db_session.add(quota)
        await db_session.commit()
        await db_session.refresh(quota)
        return quota

    @staticmethod
    async def update_quota(
        org_id: int,
        db_session: AsyncSession,
        **kwargs,
    ) -> Optional[AIQuota]:
        quota = (
            await db_session.execute(
                select(AIQuota).where(AIQuota.org_id == org_id)
            )
        ).scalars().first()
        if not quota:
            return None

        for field, value in kwargs.items():
            if hasattr(quota, field):
                setattr(quota, field, value)

        quota.update_date = str(datetime.now())
        db_session.add(quota)
        await db_session.commit()
        await db_session.refresh(quota)
        return quota

    @staticmethod
    async def check_quota(
        org_id: int,
        db_session: AsyncSession,
        estimated_tokens: int = 0,
    ) -> tuple[bool, dict]:
        quota = await AIUsageTrackingService.get_or_create_quota(org_id, db_session)
        if not quota.enabled:
            return False, {"reason": "AI usage disabled for this workspace"}

        today = str(datetime.now().date())

        today_requests = (
            await db_session.execute(
                select(func.count(AIRequestLog.id)).where(
                    AIRequestLog.org_id == org_id,
                    AIRequestLog.created_at.startswith(today),
                )
            )
        ).scalar() or 0

        month_start = str(datetime.now().replace(day=1).date())
        monthly_tokens = (
            await db_session.execute(
                select(func.sum(AIRequestLog.total_tokens)).where(
                    AIRequestLog.org_id == org_id,
                    AIRequestLog.created_at >= month_start,
                )
            )
        ).scalar() or 0

        monthly_cost = (
            await db_session.execute(
                select(func.sum(AIRequestLog.estimated_cost)).where(
                    AIRequestLog.org_id == org_id,
                    AIRequestLog.created_at >= month_start,
                )
            )
        ).scalar() or 0.0

        violations = []
        if today_requests >= quota.daily_request_limit:
            violations.append(f"Daily request limit ({quota.daily_request_limit}) reached")
        if monthly_tokens + estimated_tokens > quota.monthly_token_limit:
            violations.append(f"Monthly token limit ({quota.monthly_token_limit}) would be exceeded")
        if monthly_cost >= quota.monthly_cost_limit:
            violations.append(f"Monthly cost limit (${quota.monthly_cost_limit}) reached")

        return len(violations) == 0, {
            "within_quota": len(violations) == 0,
            "violations": violations,
            "daily_requests": today_requests,
            "daily_limit": quota.daily_request_limit,
            "monthly_tokens": monthly_tokens,
            "monthly_token_limit": quota.monthly_token_limit,
            "monthly_cost": round(monthly_cost, 4),
            "monthly_cost_limit": quota.monthly_cost_limit,
        }

    @staticmethod
    async def get_usage_summary(
        org_id: int,
        db_session: AsyncSession,
    ) -> dict:
        today = str(datetime.now().date())
        month_start = str(datetime.now().replace(day=1).date())

        total_requests = (
            await db_session.execute(
                select(func.count(AIRequestLog.id)).where(
                    AIRequestLog.org_id == org_id,
                )
            )
        ).scalar() or 0

        today_requests = (
            await db_session.execute(
                select(func.count(AIRequestLog.id)).where(
                    AIRequestLog.org_id == org_id,
                    AIRequestLog.created_at.startswith(today),
                )
            )
        ).scalar() or 0

        monthly_tokens = (
            await db_session.execute(
                select(func.sum(AIRequestLog.total_tokens)).where(
                    AIRequestLog.org_id == org_id,
                    AIRequestLog.created_at >= month_start,
                )
            )
        ).scalar() or 0

        monthly_cost = (
            await db_session.execute(
                select(func.sum(AIRequestLog.estimated_cost)).where(
                    AIRequestLog.org_id == org_id,
                    AIRequestLog.created_at >= month_start,
                )
            )
        ).scalar() or 0.0

        failures = (
            await db_session.execute(
                select(func.count(AIRequestLog.id)).where(
                    AIRequestLog.org_id == org_id,
                    AIRequestLog.success == False,
                )
            )
        ).scalar() or 0

        top_providers = (
            await db_session.execute(
                select(AIRequestLog.provider, func.count(AIRequestLog.id))
                .where(AIRequestLog.org_id == org_id)
                .group_by(AIRequestLog.provider)
                .order_by(func.count(AIRequestLog.id).desc())
                .limit(5)
            )
        ).all()

        quota = await AIUsageTrackingService.get_or_create_quota(org_id, db_session)

        return {
            "total_requests": total_requests,
            "today_requests": today_requests,
            "monthly_tokens": monthly_tokens,
            "monthly_cost": round(monthly_cost, 4),
            "total_failures": failures,
            "top_providers": [{"provider": p, "count": c} for p, c in top_providers],
            "quota": {
                "daily_request_limit": quota.daily_request_limit,
                "monthly_token_limit": quota.monthly_token_limit,
                "monthly_cost_limit": quota.monthly_cost_limit,
                "concurrent_request_limit": quota.concurrent_request_limit,
                "enabled": quota.enabled,
            },
        }
