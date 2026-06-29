from typing import Optional
from sqlalchemy import Column, ForeignKey, Integer, Index
from sqlmodel import Field, SQLModel


class UserGroupResource(SQLModel, table=True):
    __table_args__ = (
        Index("ix_usergroupresource_resource", "resource_uuid"),
        Index("ix_usergroupresource_usergroup", "usergroup_id"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    usergroup_id: int = Field(
        sa_column=Column(Integer, ForeignKey("usergroup.id", ondelete="CASCADE"))
    )
    resource_uuid: str = ""
    org_id: int = Field(
        sa_column=Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"))
    )
    creation_date: str = ""
    update_date: str = ""
