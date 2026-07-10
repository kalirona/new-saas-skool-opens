from typing import Optional
from sqlalchemy import Column, ForeignKey, Integer, Index
from sqlmodel import Field, SQLModel


class PlanEventBase(SQLModel):
    plan_id: int
    event_id: int


class PlanEvent(PlanEventBase, table=True):
    __table_args__ = (
        Index("ix_planevent_plan_event", "plan_id", "event_id", unique=True),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    plan_id: int = Field(
        sa_column=Column(Integer, ForeignKey("membershipplan.id", ondelete="CASCADE"), index=True)
    )
    event_id: int = Field(
        sa_column=Column(Integer, ForeignKey("event.id", ondelete="CASCADE"), index=True)
    )
    creation_date: str = ""
    update_date: str = ""


class PlanEventCreate(SQLModel):
    plan_id: int
    event_id: int


class PlanEventRead(PlanEventBase):
    id: int
    creation_date: str
    update_date: str
