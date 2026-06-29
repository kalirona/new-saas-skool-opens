"""Response schemas for the org analytics dashboard."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class MetricSummary(BaseModel):
    total: int = Field(description="Total count all-time")
    this_month: int = Field(description="Count created this calendar month")
    growth_percent: float = Field(description="Percent change vs previous month")


class MonthlyDataPoint(BaseModel):
    month: str = Field(description="ISO month string, e.g. 2026-01")
    count: int = Field(description="Value for that month")


class GrowthCharts(BaseModel):
    members: List[MonthlyDataPoint] = Field(description="Monthly org member joins")
    completions: List[MonthlyDataPoint] = Field(description="Monthly course completions")
    discussions: List[MonthlyDataPoint] = Field(description="Monthly discussions posted")
    comments: List[MonthlyDataPoint] = Field(description="Monthly comments posted")
    resources: List[MonthlyDataPoint] = Field(description="Monthly resources created")


class DiscussionActivity(BaseModel):
    total_discussions: int
    total_comments: int
    this_month_discussions: int
    this_month_comments: int
    growth_percent_discussions: float
    growth_percent_comments: float


class DashboardAnalyticsResponse(BaseModel):
    org_id: int
    active_members: MetricSummary
    course_completions: MetricSummary
    discussion_activity: DiscussionActivity
    resources: MetricSummary
    growth_charts: GrowthCharts
