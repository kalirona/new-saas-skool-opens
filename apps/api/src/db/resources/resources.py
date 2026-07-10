from typing import Optional, List, Dict, Any
from sqlalchemy import Column, ForeignKey, Integer, Text, String, BigInteger, Boolean, JSON, Index
from sqlmodel import Field, SQLModel


RESOURCE_TYPES = [
    "pdf", "video", "audio", "link", "file", "zip",
    "markdown", "rich_text", "ai_prompt", "template", "external_embed",
]
VISIBILITY_OPTIONS = ["public", "private", "restricted"]


class ResourceBase(SQLModel):
    title: str
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    resource_type: str
    url: Optional[str] = None
    file_id: Optional[str] = None
    file_size: Optional[int] = None
    file_mime: Optional[str] = None
    file_format: Optional[str] = None
    thumbnail_image: Optional[str] = None
    visibility: str = Field(default="private", sa_column=Column(String(20)))
    locked: bool = False
    content: Optional[str] = Field(default=None, sa_column=Column(Text))
    metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    embed_url: Optional[str] = None
    category: Optional[str] = None
    featured: bool = False
    pinned: bool = False


class Resource(ResourceBase, table=True):
    __table_args__ = (
        Index("ix_resource_org_id", "org_id"),
        Index("ix_resource_author_id", "author_id"),
        Index("ix_resource_org_type_vis", "org_id", "resource_type", "visibility"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("organization.id", ondelete="CASCADE"), nullable=False)
    )
    author_id: int = Field(
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    )
    folder_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("folder.id", ondelete="SET NULL"), nullable=True, index=True)
    )
    community_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("community.id", ondelete="SET NULL"), nullable=True, index=True)
    )
    space_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("space.id", ondelete="SET NULL"), nullable=True, index=True)
    )
    resource_uuid: str = Field(default="", index=True)
    creation_date: str = ""
    update_date: str = ""


class ResourceCreate(ResourceBase):
    org_id: int
    author_id: int
    folder_id: Optional[int] = None
    community_id: Optional[int] = None
    space_id: Optional[int] = None


class ResourceUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    resource_type: Optional[str] = None
    url: Optional[str] = None
    file_id: Optional[str] = None
    file_size: Optional[int] = None
    file_mime: Optional[str] = None
    file_format: Optional[str] = None
    thumbnail_image: Optional[str] = None
    visibility: Optional[str] = None
    locked: Optional[bool] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    embed_url: Optional[str] = None
    category: Optional[str] = None
    featured: Optional[bool] = None
    pinned: Optional[bool] = None
    folder_id: Optional[int] = None
    community_id: Optional[int] = None
    space_id: Optional[int] = None


class ResourceRead(ResourceBase):
    id: int
    org_id: int
    author_id: int
    folder_id: Optional[int] = None
    community_id: Optional[int] = None
    space_id: Optional[int] = None
    resource_uuid: str
    creation_date: str
    update_date: str


class ResourceDetailRead(ResourceRead):
    """Extended resource detail with community, author, and access info."""
    community_name: Optional[str] = None
    community_uuid: Optional[str] = None
    community_thumbnail: Optional[str] = None
    author_username: Optional[str] = None
    author_avatar: Optional[str] = None
    author_first_name: Optional[str] = None
    author_last_name: Optional[str] = None
    org_uuid: Optional[str] = None
    user_has_access: bool = True
    required_plan_name: Optional[str] = None
    required_plan_uuid: Optional[str] = None
