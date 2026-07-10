from typing import Optional
from sqlalchemy import Column, ForeignKey, Integer, Text, Index
from sqlmodel import Field, SQLModel
from pgvector.sqlalchemy import Vector


class CourseEmbedding(SQLModel, table=True):
    __tablename__ = "course_embedding"
    __table_args__ = (
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(
        sa_column=Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), index=True)
    )
    course_id: int = Field(
        sa_column=Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), index=True)
    )
    activity_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("activity.id", ondelete="CASCADE"), nullable=True, index=True),
    )
    activity_uuid: str = Field(default="", index=True)
    block_uuid: Optional[str] = None
    source_type: str = ""  # dynamic_page, pdf_block, image_block, audio_block, quiz_block, custom_block, document_activity
    chunk_text: str = Field(default="", sa_column=Column(Text))
    chunk_index: int = 0
    activity_name: str = ""
    chapter_name: str = ""
    course_name: str = ""
    embedding: list = Field(sa_column=Column(Vector(768)))
    creation_date: str = ""
    update_date: str = ""
