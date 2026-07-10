from typing import Optional
from sqlalchemy import Column, ForeignKey, Integer, Index
from sqlmodel import Field, SQLModel


class UserGroupUser(SQLModel, table=True):
    __table_args__ = (
        Index("ix_usergroupuser_group_user", "usergroup_id", "user_id"),
        Index("ix_usergroupuser_user", "user_id"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    usergroup_id: int = Field(
        sa_column=Column(Integer, ForeignKey("usergroup.id", ondelete="CASCADE"), index=True)
    )
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), index=True)
    )
    org_id: int = Field(
        sa_column=Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), index=True)
    )
    creation_date: str = ""
    update_date: str = ""
