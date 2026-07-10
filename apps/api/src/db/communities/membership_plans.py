from typing import Optional, Dict, Any
from sqlalchemy import Column, ForeignKey, Integer, Text, String, JSON, Index
from sqlmodel import Field, SQLModel


MEMBERSHIP_INTERVALS = ["monthly", "yearly", "one_time"]
MEMBERSHIP_STATUSES = ["draft", "active", "archived"]


class MembershipPlanBase(SQLModel):
    name: str
    slug: str = Field(default="", index=True, unique=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    price: float = 0.0
    currency: str = "usd"
    interval: str = "monthly"
    max_members: int = 0
    is_free: bool = False
    is_public: bool = True
    trial_days: int = 0
    display_order: int = 0
    features: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    status: str = "draft"


class MembershipPlan(MembershipPlanBase, table=True):
    __table_args__ = (
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    community_id: int = Field(
        sa_column=Column(Integer, ForeignKey("community.id", ondelete="CASCADE"), index=True)
    )
    org_id: int = Field(
        sa_column=Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), index=True)
    )
    usergroup_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("usergroup.id", ondelete="SET NULL"), nullable=True, index=True)
    )
    plan_uuid: str = Field(default="", index=True)
    billing_provider: Optional[str] = None
    billing_provider_plan_id: Optional[str] = None
    creation_date: str = ""
    update_date: str = ""


class MembershipPlanCreate(MembershipPlanBase):
    community_id: int
    org_id: int
    usergroup_id: Optional[int] = None


class MembershipPlanUpdate(SQLModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    interval: Optional[str] = None
    max_members: Optional[int] = None
    is_free: Optional[bool] = None
    is_public: Optional[bool] = None
    trial_days: Optional[int] = None
    display_order: Optional[int] = None
    features: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    usergroup_id: Optional[int] = None
    billing_provider: Optional[str] = None
    billing_provider_plan_id: Optional[str] = None


class MembershipPlanRead(MembershipPlanBase):
    id: int
    community_id: int
    org_id: int
    usergroup_id: Optional[int] = None
    plan_uuid: str
    billing_provider: Optional[str] = None
    billing_provider_plan_id: Optional[str] = None
    creation_date: str
    update_date: str
