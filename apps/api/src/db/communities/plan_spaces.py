from typing import Optional
from sqlalchemy import Column, ForeignKey, Integer, Index
from sqlmodel import Field, SQLModel


class PlanSpaceBase(SQLModel):
    plan_id: int
    space_id: int


class PlanSpace(PlanSpaceBase, table=True):
    __table_args__ = (
        Index("ix_planspace_plan_space", "plan_id", "space_id", unique=True),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    plan_id: int = Field(
        sa_column=Column(Integer, ForeignKey("membershipplan.id", ondelete="CASCADE"), index=True)
    )
    space_id: int = Field(
        sa_column=Column(Integer, ForeignKey("space.id", ondelete="CASCADE"), index=True)
    )
    creation_date: str = ""
    update_date: str = ""


class PlanSpaceCreate(SQLModel):
    plan_id: int
    space_id: int


class PlanSpaceRead(PlanSpaceBase):
    id: int
    creation_date: str
    update_date: str
