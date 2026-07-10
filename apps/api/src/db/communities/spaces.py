from typing import Optional, List
from sqlalchemy import Column, ForeignKey, Integer, Text, String, Index
from sqlmodel import Field, SQLModel


class SpaceBase(SQLModel):
    name: str
    icon: Optional[str] = Field(default=None, sa_column=Column(String(50)))
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    ordering: int = 0
    visibility: str = Field(default="public", sa_column=Column(String(20)))
    locked: bool = False


class Space(SpaceBase, table=True):
    __table_args__ = (
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    community_id: int = Field(
        sa_column=Column(Integer, ForeignKey("community.id", ondelete="CASCADE"), index=True)
    )
    org_id: int = Field(
        sa_column=Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), index=True)
    )
    space_uuid: str = Field(default="", index=True)
    creation_date: str = ""
    update_date: str = ""


class SpaceCreate(SpaceBase):
    community_id: int = Field(default=None, foreign_key="community.id")
    org_id: int = Field(default=None, foreign_key="organization.id")


class SpaceUpdate(SQLModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    ordering: Optional[int] = None
    visibility: Optional[str] = None
    locked: Optional[bool] = None


class SpaceRead(SpaceBase):
    id: int
    community_id: int = Field(default=None, foreign_key="community.id")
    org_id: int = Field(default=None, foreign_key="organization.id")
    space_uuid: str
    creation_date: str
    update_date: str
