from typing import Optional
from sqlalchemy import Column, ForeignKey, Integer, Text, String, Boolean
from sqlmodel import Field, SQLModel


class PromptTemplateBase(SQLModel):
    name: str = Field(sa_column=Column(String(100)))
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    category: Optional[str] = Field(default=None, sa_column=Column(String(50)))
    is_active: bool = True
    is_system: bool = False


class PromptTemplate(PromptTemplateBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(
        sa_column=Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"))
    )
    author_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
    )
    current_version_id: Optional[int] = None
    prompt_uuid: str = Field(default="", index=True)
    creation_date: str = ""
    update_date: str = ""


class PromptTemplateVersion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    prompt_id: int = Field(
        sa_column=Column(Integer, ForeignKey("prompttemplate.id", ondelete="CASCADE"))
    )
    version_number: int = 0
    system_prompt: str = Field(sa_column=Column(Text))
    user_prompt_template: Optional[str] = Field(default=None, sa_column=Column(Text))
    parameters: Optional[str] = Field(default=None, sa_column=Column(Text))
    temperature: float = 0.7
    max_tokens: int = 4096
    author_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True),
    )
    change_note: Optional[str] = Field(default=None, sa_column=Column(String(200)))
    creation_date: str = ""


class PromptTemplateCreate(SQLModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    system_prompt: str
    user_prompt_template: Optional[str] = None
    parameters: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    is_system: bool = False


class PromptTemplateUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


class PromptTemplateVersionCreate(SQLModel):
    system_prompt: str
    user_prompt_template: Optional[str] = None
    parameters: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    change_note: Optional[str] = None


class PromptTemplateRead(PromptTemplateBase):
    id: int
    org_id: int
    author_id: Optional[int] = None
    current_version_id: Optional[int] = None
    prompt_uuid: str
    creation_date: str
    update_date: str
    current_version: Optional["PromptTemplateVersionRead"] = None


class PromptTemplateVersionRead(SQLModel):
    id: int
    prompt_id: int
    version_number: int
    system_prompt: str
    user_prompt_template: Optional[str] = None
    parameters: Optional[str] = None
    temperature: float
    max_tokens: int
    author_id: Optional[int] = None
    change_note: Optional[str] = None
    creation_date: str
