from typing import Optional
from sqlalchemy import Column, ForeignKey, Integer, Text, Boolean, String, Index
from sqlmodel import Field, SQLModel
from src.db.users import UserRead


# Available discussion labels
DISCUSSION_LABELS = [
    {"id": "general", "name": "General", "color": "#6B7280", "icon": "MessageSquare"},
    {"id": "question", "name": "Q&A", "color": "#EAB308", "icon": "HelpCircle"},
    {"id": "idea", "name": "Ideas", "color": "#8B5CF6", "icon": "Lightbulb"},
    {"id": "announcement", "name": "Announcements", "color": "#3B82F6", "icon": "Megaphone"},
    {"id": "showcase", "name": "Show and Tell", "color": "#10B981", "icon": "Star"},
]


class DiscussionBase(SQLModel):
    title: str
    content: Optional[str] = Field(default=None, sa_column=Column(Text))
    label: Optional[str] = Field(default="general", sa_column=Column(String(50)))
    emoji: Optional[str] = Field(default=None, sa_column=Column(String(50)))


class Discussion(DiscussionBase, table=True):
    __table_args__ = (
        Index("ix_discussion_community_pinned_date", "community_id", "is_pinned", "creation_date"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    community_id: int = Field(
        sa_column=Column(Integer, ForeignKey("community.id", ondelete="CASCADE"), index=True)
    )
    space_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("space.id", ondelete="SET NULL"), nullable=True, index=True)
    )
    org_id: int = Field(
        sa_column=Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), index=True)
    )
    author_id: int = Field(
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), index=True)
    )
    discussion_uuid: str = Field(default="", index=True)
    upvote_count: int = 0
    edit_count: int = 0
    is_pinned: bool = Field(default=False, sa_column=Column(Boolean, default=False))
    is_locked: bool = Field(default=False, sa_column=Column(Boolean, default=False))
    creation_date: str = ""
    update_date: str = ""


class DiscussionCreate(SQLModel):
    title: str
    content: Optional[str] = None
    label: Optional[str] = "general"
    emoji: Optional[str] = None
    community_id: int = Field(default=None, foreign_key="community.id")
    space_id: Optional[int] = Field(default=None, foreign_key="space.id")
    org_id: int = Field(default=None, foreign_key="organization.id")
    author_id: int = Field(default=None, foreign_key="user.id")


class DiscussionUpdate(SQLModel):
    title: Optional[str] = None
    content: Optional[str] = None
    label: Optional[str] = None
    emoji: Optional[str] = None


class DiscussionPinUpdate(SQLModel):
    is_pinned: bool


class DiscussionLockUpdate(SQLModel):
    is_locked: bool


class DiscussionRead(SQLModel):
    id: int
    title: str
    content: Optional[str] = None
    label: Optional[str] = "general"
    emoji: Optional[str] = None
    community_id: int = Field(default=None, foreign_key="community.id")
    space_id: Optional[int] = Field(default=None, foreign_key="space.id")
    org_id: int = Field(default=None, foreign_key="organization.id")
    author_id: int = Field(default=None, foreign_key="user.id")
    discussion_uuid: str
    upvote_count: int
    edit_count: int = 0
    is_pinned: bool = False
    is_locked: bool = False
    creation_date: str
    update_date: str


class DiscussionReadWithAuthor(DiscussionRead):
    author: Optional[UserRead] = None


class DiscussionReadWithVoteStatus(DiscussionReadWithAuthor):
    has_voted: bool = False


class DiscussionLabelInfo(SQLModel):
    id: str
    name: str
    color: str
    icon: str
