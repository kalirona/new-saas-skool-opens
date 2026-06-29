from typing import Optional
from sqlalchemy import Column, ForeignKey, Integer
from sqlmodel import Field, SQLModel


class PlanResourceBase(SQLModel):
    plan_id: int
    resource_id: int


class PlanResource(PlanResourceBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plan_id: int = Field(
        sa_column=Column(Integer, ForeignKey("membershipplan.id", ondelete="CASCADE"))
    )
    resource_id: int = Field(
        sa_column=Column(Integer, ForeignKey("resource.id", ondelete="CASCADE"))
    )
    creation_date: str = ""
    update_date: str = ""


class PlanResourceCreate(SQLModel):
    plan_id: int
    resource_id: int


class PlanResourceRead(PlanResourceBase):
    id: int
    creation_date: str
    update_date: str
