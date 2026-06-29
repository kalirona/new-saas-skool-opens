"""PostgreSQL-backed org analytics queries for the dashboard.

Queries the app's own database directly (no Tinybird dependency)
to return aggregated metrics and monthly growth charts.
"""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession

from src.services.dash_analytics.schemas import (
    DashboardAnalyticsResponse,
    MetricSummary,
    MonthlyDataPoint,
    DiscussionActivity,
    GrowthCharts,
)

logger = logging.getLogger(__name__)


def _month_range(months_ago: int = 0) -> tuple[str, str]:
    """Return (first_day, last_day) of ``months_ago`` from current month."""
    now = datetime.utcnow()
    year, month = now.year, now.month
    for _ in range(months_ago):
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    first = f"{year:04d}-{month:02d}-01"
    if month == 12:
        next_first = f"{year + 1:04d}-01-01"
    else:
        next_first = f"{year:04d}-{month + 1:02d}-01"
    return first, next_first


async def _fetch_val(db: AsyncSession, sql: str, **params) -> int:
    """Run a scalar query and return the integer result."""
    result = await db.execute(text(sql), params)
    row = result.one_or_none()
    return row[0] if row else 0


async def _monthly_series(
    db: AsyncSession,
    sql: str,
    **params,
) -> list[MonthlyDataPoint]:
    """Run a monthly-grouped query and return a 12-point zero-filled series."""
    result = await db.execute(text(sql), params)
    rows = result.all()
    lookup = {r[0]: r[1] for r in rows}

    series: list[MonthlyDataPoint] = []
    now = datetime.utcnow()
    for i in range(11, -1, -1):
        y, m = now.year, now.month
        for _ in range(i):
            m -= 1
            if m == 0:
                m = 12
                y -= 1
        key = f"{y:04d}-{m:02d}"
        series.append(MonthlyDataPoint(month=key, count=lookup.get(key, 0)))
    return series


def _growth(prev: int, curr: int) -> float:
    if prev == 0:
        return 100.0 if curr > 0 else 0.0
    return round(((curr - prev) / prev) * 100, 1)


async def get_dashboard_analytics(
    org_id: int,
    db_session: AsyncSession,
) -> DashboardAnalyticsResponse:
    """Compute all dashboard metrics for an organization."""

    _this_start, _ = _month_range(0)
    c_prev, c_this = _month_range(1)

    params = {"org_id": org_id, "c_this": c_this, "c_prev": c_prev}

    # ── Active members ────────────────────────────────────────────────
    total_members = await _fetch_val(
        db_session, "SELECT count(*) FROM userorganization WHERE org_id = :org_id", org_id=org_id
    )
    members_this_month = await _fetch_val(
        db_session,
        "SELECT count(*) FROM userorganization WHERE org_id = :org_id AND creation_date >= :c_this",
        **params,
    )
    members_prev_month = await _fetch_val(
        db_session,
        "SELECT count(*) FROM userorganization WHERE org_id = :org_id "
        "AND creation_date >= :c_prev AND creation_date < :c_this",
        **params,
    )
    members_chart = await _monthly_series(
        db_session,
        "SELECT substr(creation_date, 1, 7) AS month, count(*) AS cnt "
        "FROM userorganization WHERE org_id = :org_id "
        "GROUP BY month ORDER BY month",
        org_id=org_id,
    )

    # ── Course completions ────────────────────────────────────────────
    total_completions = await _fetch_val(
        db_session,
        "SELECT count(*) FROM trailrun WHERE org_id = :org_id AND status = 'STATUS_COMPLETED'",
        org_id=org_id,
    )
    completions_this_month = await _fetch_val(
        db_session,
        "SELECT count(*) FROM trailrun WHERE org_id = :org_id AND status = 'STATUS_COMPLETED' "
        "AND update_date >= :c_this",
        **params,
    )
    completions_prev_month = await _fetch_val(
        db_session,
        "SELECT count(*) FROM trailrun WHERE org_id = :org_id AND status = 'STATUS_COMPLETED' "
        "AND update_date >= :c_prev AND update_date < :c_this",
        **params,
    )
    completions_chart = await _monthly_series(
        db_session,
        "SELECT substr(update_date, 1, 7) AS month, count(*) AS cnt "
        "FROM trailrun WHERE org_id = :org_id AND status = 'STATUS_COMPLETED' "
        "GROUP BY month ORDER BY month",
        org_id=org_id,
    )

    # ── Discussion activity ───────────────────────────────────────────
    total_discussions = await _fetch_val(
        db_session, "SELECT count(*) FROM discussion WHERE org_id = :org_id", org_id=org_id
    )
    discussions_this_month = await _fetch_val(
        db_session,
        "SELECT count(*) FROM discussion WHERE org_id = :org_id AND creation_date >= :c_this",
        **params,
    )
    discussions_prev_month = await _fetch_val(
        db_session,
        "SELECT count(*) FROM discussion WHERE org_id = :org_id "
        "AND creation_date >= :c_prev AND creation_date < :c_this",
        **params,
    )

    total_comments = await _fetch_val(
        db_session,
        "SELECT count(*) FROM discussioncomment dc "
        "JOIN discussion d ON dc.discussion_id = d.id WHERE d.org_id = :org_id",
        org_id=org_id,
    )
    comments_this_month = await _fetch_val(
        db_session,
        "SELECT count(*) FROM discussioncomment dc "
        "JOIN discussion d ON dc.discussion_id = d.id "
        "WHERE d.org_id = :org_id AND dc.creation_date >= :c_this",
        **params,
    )
    comments_prev_month = await _fetch_val(
        db_session,
        "SELECT count(*) FROM discussioncomment dc "
        "JOIN discussion d ON dc.discussion_id = d.id "
        "WHERE d.org_id = :org_id "
        "AND dc.creation_date >= :c_prev AND dc.creation_date < :c_this",
        **params,
    )

    discussions_chart = await _monthly_series(
        db_session,
        "SELECT substr(creation_date, 1, 7) AS month, count(*) AS cnt "
        "FROM discussion WHERE org_id = :org_id "
        "GROUP BY month ORDER BY month",
        org_id=org_id,
    )
    comments_chart = await _monthly_series(
        db_session,
        "SELECT substr(dc.creation_date, 1, 7) AS month, count(*) AS cnt "
        "FROM discussioncomment dc "
        "JOIN discussion d ON dc.discussion_id = d.id "
        "WHERE d.org_id = :org_id "
        "GROUP BY month ORDER BY month",
        org_id=org_id,
    )

    # ── Resources ─────────────────────────────────────────────────────
    total_resources = await _fetch_val(
        db_session, "SELECT count(*) FROM resource WHERE org_id = :org_id", org_id=org_id
    )
    resources_this_month = await _fetch_val(
        db_session,
        "SELECT count(*) FROM resource WHERE org_id = :org_id AND creation_date >= :c_this",
        **params,
    )
    resources_prev_month = await _fetch_val(
        db_session,
        "SELECT count(*) FROM resource WHERE org_id = :org_id "
        "AND creation_date >= :c_prev AND creation_date < :c_this",
        **params,
    )
    resources_chart = await _monthly_series(
        db_session,
        "SELECT substr(creation_date, 1, 7) AS month, count(*) AS cnt "
        "FROM resource WHERE org_id = :org_id "
        "GROUP BY month ORDER BY month",
        org_id=org_id,
    )

    return DashboardAnalyticsResponse(
        org_id=org_id,
        active_members=MetricSummary(
            total=total_members,
            this_month=members_this_month,
            growth_percent=_growth(members_prev_month, members_this_month),
        ),
        course_completions=MetricSummary(
            total=total_completions,
            this_month=completions_this_month,
            growth_percent=_growth(completions_prev_month, completions_this_month),
        ),
        discussion_activity=DiscussionActivity(
            total_discussions=total_discussions,
            total_comments=total_comments,
            this_month_discussions=discussions_this_month,
            this_month_comments=comments_this_month,
            growth_percent_discussions=_growth(discussions_prev_month, discussions_this_month),
            growth_percent_comments=_growth(comments_prev_month, comments_this_month),
        ),
        resources=MetricSummary(
            total=total_resources,
            this_month=resources_this_month,
            growth_percent=_growth(resources_prev_month, resources_this_month),
        ),
        growth_charts=GrowthCharts(
            members=members_chart,
            completions=completions_chart,
            discussions=discussions_chart,
            comments=comments_chart,
            resources=resources_chart,
        ),
    )
