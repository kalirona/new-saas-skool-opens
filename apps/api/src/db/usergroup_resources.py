from typing import Optional
from sqlalchemy import Column, ForeignKey, Integer, Index
from sqlmodel import Field, SQLModel


class UserGroupResource(SQLModel, table=True):
    __table_args__ = (
        Index("ix_usergroupresource_resource", "resource_uuid"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    usergroup_id: int = Field(
        sa_column=Column(Integer, ForeignKey("usergroup.id", ondelete="CASCADE"), index=True)
    )
    resource_uuid: str = Field(default="", index=True)
    org_id: int = Field(
        sa_column=Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), index=True)
    )
    creation_date: str = ""
    update_date: str = ""
