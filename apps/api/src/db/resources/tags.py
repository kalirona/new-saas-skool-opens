from typing import Optional, List
from sqlalchemy import Column, ForeignKey, Integer, String, Index
from sqlmodel import Field, SQLModel


class TagBase(SQLModel):
    name: str
    color: Optional[str] = None


class Tag(TagBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(
        sa_column=Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    tag_uuid: str = Field(default="", index=True)
    creation_date: str = ""


class TagCreate(TagBase):
    org_id: int


class TagRead(TagBase):
    id: int
    org_id: int
    tag_uuid: str
    creation_date: str


class ResourceTag(SQLModel, table=True):
    __table_args__ = (
        Index("ix_resourcetag_resource_tag", "resource_id", "tag_id", unique=True),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    resource_id: int = Field(
        sa_column=Column(Integer, ForeignKey("resource.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    tag_id: int = Field(
        sa_column=Column(Integer, ForeignKey("tag.id", ondelete="CASCADE"), nullable=False, index=True)
    )
