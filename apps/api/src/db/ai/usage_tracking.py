from typing import Optional
from sqlalchemy import Column, ForeignKey, Integer, BigInteger, Text, String, Float, Index
from sqlmodel import Field, SQLModel


class AIRequestLog(SQLModel, table=True):
    """Detailed log of every AI generation request for usage tracking."""
    __table_args__ = (
        Index("ix_airequestlog_org", "org_id"),
        Index("ix_airequestlog_user", "user_id"),
        Index("ix_airequestlog_org_created", "org_id", "created_at"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(
        sa_column=Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), index=True)
    )
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), index=True)
    )
    feature: str = Field(sa_column=Column(String(50)))
    provider: str = Field(sa_column=Column(String(30)))
    model_name: str = Field(sa_column=Column(String(100)))
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    success: bool = True
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text))
    duration_ms: Optional[int] = None
    request_id: Optional[str] = Field(default=None, sa_column=Column(String(100)))
    created_at: str = ""


class AIQuota(SQLModel, table=True):
    """Per-workspace AI usage quota configuration."""
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(
        sa_column=Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), unique=True)
    )
    daily_request_limit: int = 1000
    monthly_token_limit: int = 1_000_000
    monthly_cost_limit: float = 50.0
    concurrent_request_limit: int = 5
    enabled: bool = True
    creation_date: str = ""
    update_date: str = ""
