from typing import Optional
from sqlalchemy import Column, ForeignKey, Integer, String, Index
from sqlmodel import Field, SQLModel


MEMBER_STATUSES = ["trial", "active", "past_due", "cancelled", "expired", "pending"]


class CommunityMemberBase(SQLModel):
    status: str = "active"


class CommunityMember(CommunityMemberBase, table=True):
    __table_args__ = (
        Index("ix_communitymember_community_user", "community_id", "user_id"),
        Index("ix_communitymember_user", "user_id"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    community_id: int = Field(
        sa_column=Column(Integer, ForeignKey("community.id", ondelete="CASCADE"))
    )
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    )
    org_id: int = Field(
        sa_column=Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"))
    )
    plan_id: int = Field(
        sa_column=Column(Integer, ForeignKey("membershipplan.id", ondelete="CASCADE"))
    )
    billing_provider_subscription_id: Optional[str] = None
    billing_provider: Optional[str] = None
    joined_date: str = ""
    expires_date: Optional[str] = None
    trial_end_date: Optional[str] = None
    cancelled_at: Optional[str] = None
    next_billing_date: Optional[str] = None
    creation_date: str = ""
    update_date: str = ""


class CommunityMemberCreate(SQLModel):
    community_id: int
    user_id: int
    org_id: int
    plan_id: int
    status: str = "pending"
    billing_provider_subscription_id: Optional[str] = None
    billing_provider: Optional[str] = None


class CommunityMemberRead(CommunityMemberBase):
    id: int
    community_id: int
    user_id: int
    org_id: int
    plan_id: int
    billing_provider_subscription_id: Optional[str] = None
    billing_provider: Optional[str] = None
    joined_date: str
    expires_date: Optional[str] = None
    trial_end_date: Optional[str] = None
    creation_date: str
    update_date: str
