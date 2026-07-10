from typing import Optional, Dict, Any, List
from sqlalchemy import Column, ForeignKey, Integer, String, JSON, UniqueConstraint
from sqlmodel import Field, SQLModel


BENEFIT_TYPES = [
    "community_access",
    "space_access",
    "course_access",
    "resource_access",
    "event_access",
    "download_permissions",
    "ai_credits",
]


class MembershipBenefitBase(SQLModel):
    benefit_type: str
    benefit_value: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON, nullable=True))


class MembershipBenefit(MembershipBenefitBase, table=True):
    __table_args__ = (
        UniqueConstraint("plan_id", "benefit_type", name="uq_plan_benefit_type"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    plan_id: int = Field(
        sa_column=Column(Integer, ForeignKey("membershipplan.id", ondelete="CASCADE"), index=True)
    )
    creation_date: str = ""
    update_date: str = ""


class MembershipBenefitCreate(MembershipBenefitBase):
    plan_id: int


class MembershipBenefitUpdate(SQLModel):
    benefit_type: Optional[str] = None
    benefit_value: Optional[Dict[str, Any]] = None


class MembershipBenefitRead(MembershipBenefitBase):
    id: int
    plan_id: int
    creation_date: str
    update_date: str


DEFAULT_BENEFITS: Dict[str, Dict[str, Any]] = {
    "community_access": {"enabled": True},
    "space_access": {"enabled": True, "space_uuids": None},
    "course_access": {"enabled": False, "course_uuids": None},
    "resource_access": {"enabled": False, "resource_uuids": None},
    "event_access": {"enabled": False, "event_uuids": None},
    "download_permissions": {"enabled": False},
    "ai_credits": {"enabled": False, "credits": 0},
}
