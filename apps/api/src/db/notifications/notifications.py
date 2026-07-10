from typing import Optional
from sqlalchemy import Column, ForeignKey, Integer, BigInteger, Text, String, Boolean, Index
from sqlmodel import Field, SQLModel


NOTIFICATION_TYPES = [
    "new_comment",
    "new_discussion",
    "mention",
    "event_reminder",
]


class NotificationBase(SQLModel):
    notification_type: str = Field(default="", sa_column=Column(String(30)))
    title: str
    message: Optional[str] = Field(default=None, sa_column=Column(Text))
    is_read: bool = False
    link: Optional[str] = None


class Notification(NotificationBase, table=True):
    __table_args__ = (
        Index("ix_notification_user_read", "user_id", "is_read"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("organization.id", ondelete="CASCADE"), index=True)
    )
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), index=True)
    )
    actor_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True),
    )
    resource_uuid: Optional[str] = None
    parent_resource_uuid: Optional[str] = None
    notification_uuid: str = Field(default="", index=True)
    creation_date: str = ""


class NotificationCreate(SQLModel):
    notification_type: str
    title: str
    message: Optional[str] = None
    user_id: int
    org_id: int
    actor_id: Optional[int] = None
    resource_uuid: Optional[str] = None
    parent_resource_uuid: Optional[str] = None
    link: Optional[str] = None


class NotificationRead(NotificationBase):
    id: int
    org_id: int
    user_id: int
    actor_id: Optional[int] = None
    resource_uuid: Optional[str] = None
    parent_resource_uuid: Optional[str] = None
    notification_uuid: str
    creation_date: str
