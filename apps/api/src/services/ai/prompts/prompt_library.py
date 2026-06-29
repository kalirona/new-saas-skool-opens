from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlmodel import select, delete
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.ai.prompt_library import (
    PromptTemplate,
    PromptTemplateVersion,
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateVersionCreate,
    PromptTemplateRead,
    PromptTemplateVersionRead,
)

logger = logging.getLogger(__name__)


def render_prompt_template(
    template: str,
    **kwargs: str,
) -> str:
    """Render a prompt template string with keyword arguments."""
    return template.format(**kwargs)


class PromptLibraryService:
    @staticmethod
    async def create(
        org_id: int,
        author_id: int,
        data: PromptTemplateCreate,
        db_session: AsyncSession,
    ) -> PromptTemplateRead:
        prompt = PromptTemplate(
            name=data.name,
            description=data.description,
            category=data.category,
            is_active=True,
            is_system=data.is_system,
            org_id=org_id,
            author_id=author_id,
            prompt_uuid=f"pt_{uuid4()}",
            creation_date=str(datetime.now()),
            update_date=str(datetime.now()),
        )
        db_session.add(prompt)
        await db_session.commit()
        await db_session.refresh(prompt)

        version = PromptTemplateVersion(
            prompt_id=prompt.id,
            version_number=1,
            system_prompt=data.system_prompt,
            user_prompt_template=data.user_prompt_template,
            parameters=data.parameters,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
            author_id=author_id,
            change_note="Initial version",
            creation_date=str(datetime.now()),
        )
        db_session.add(version)
        await db_session.commit()
        await db_session.refresh(version)

        prompt.current_version_id = version.id
        db_session.add(prompt)
        await db_session.commit()
        await db_session.refresh(prompt)

        read = PromptTemplateRead.model_validate(prompt.model_dump())
        read.current_version = PromptTemplateVersionRead.model_validate(version.model_dump())
        return read

    @staticmethod
    async def list_for_org(
        org_id: int,
        db_session: AsyncSession,
        category: Optional[str] = None,
        include_system: bool = True,
    ) -> list[PromptTemplateRead]:
        statement = select(PromptTemplate).where(PromptTemplate.org_id == org_id)
        if not include_system:
            statement = statement.where(PromptTemplate.is_system == False)
        if category:
            statement = statement.where(PromptTemplate.category == category)
        statement = statement.order_by(PromptTemplate.name.asc())

        prompts = (await db_session.execute(statement)).scalars().all()

        result = []
        for p in prompts:
            read = PromptTemplateRead.model_validate(p.model_dump())
            if p.current_version_id:
                version = (
                    await db_session.execute(
                        select(PromptTemplateVersion).where(
                            PromptTemplateVersion.id == p.current_version_id
                        )
                    )
                ).scalars().first()
                if version:
                    read.current_version = PromptTemplateVersionRead.model_validate(version.model_dump())
            result.append(read)
        return result

    @staticmethod
    async def get(
        prompt_uuid: str,
        db_session: AsyncSession,
    ) -> Optional[PromptTemplateRead]:
        prompt = (
            await db_session.execute(
                select(PromptTemplate).where(PromptTemplate.prompt_uuid == prompt_uuid)
            )
        ).scalars().first()
        if not prompt:
            return None

        read = PromptTemplateRead.model_validate(prompt.model_dump())
        if prompt.current_version_id:
            version = (
                await db_session.execute(
                    select(PromptTemplateVersion).where(
                        PromptTemplateVersion.id == prompt.current_version_id
                    )
                )
            ).scalars().first()
            if version:
                read.current_version = PromptTemplateVersionRead.model_validate(version.model_dump())
        return read

    @staticmethod
    async def update(
        prompt_uuid: str,
        data: PromptTemplateUpdate,
        db_session: AsyncSession,
    ) -> Optional[PromptTemplateRead]:
        prompt = (
            await db_session.execute(
                select(PromptTemplate).where(PromptTemplate.prompt_uuid == prompt_uuid)
            )
        ).scalars().first()
        if not prompt:
            return None

        for field, value in data.model_dump(exclude_none=True).items():
            setattr(prompt, field, value)

        prompt.update_date = str(datetime.now())
        db_session.add(prompt)
        await db_session.commit()
        await db_session.refresh(prompt)

        read = PromptTemplateRead.model_validate(prompt.model_dump())
        if prompt.current_version_id:
            version = (
                await db_session.execute(
                    select(PromptTemplateVersion).where(
                        PromptTemplateVersion.id == prompt.current_version_id
                    )
                )
            ).scalars().first()
            if version:
                read.current_version = PromptTemplateVersionRead.model_validate(version.model_dump())
        return read

    @staticmethod
    async def delete(
        prompt_uuid: str,
        db_session: AsyncSession,
    ) -> bool:
        prompt = (
            await db_session.execute(
                select(PromptTemplate).where(PromptTemplate.prompt_uuid == prompt_uuid)
            )
        ).scalars().first()
        if not prompt:
            return False

        await db_session.execute(
            delete(PromptTemplateVersion).where(
                PromptTemplateVersion.prompt_id == prompt.id
            )
        )
        await db_session.delete(prompt)
        await db_session.commit()
        return True

    @staticmethod
    async def create_version(
        prompt_uuid: str,
        author_id: int,
        data: PromptTemplateVersionCreate,
        db_session: AsyncSession,
    ) -> Optional[PromptTemplateRead]:
        prompt = (
            await db_session.execute(
                select(PromptTemplate).where(PromptTemplate.prompt_uuid == prompt_uuid)
            )
        ).scalars().first()
        if not prompt:
            return None

        versions = (
            await db_session.execute(
                select(PromptTemplateVersion).where(
                    PromptTemplateVersion.prompt_id == prompt.id
                ).order_by(PromptTemplateVersion.version_number.desc())
            )
        ).scalars().all()

        next_version = (versions[0].version_number + 1) if versions else 1

        version = PromptTemplateVersion(
            prompt_id=prompt.id,
            version_number=next_version,
            system_prompt=data.system_prompt,
            user_prompt_template=data.user_prompt_template,
            parameters=data.parameters,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
            author_id=author_id,
            change_note=data.change_note,
            creation_date=str(datetime.now()),
        )
        db_session.add(version)
        await db_session.commit()
        await db_session.refresh(version)

        prompt.current_version_id = version.id
        prompt.update_date = str(datetime.now())
        db_session.add(prompt)
        await db_session.commit()
        await db_session.refresh(prompt)

        read = PromptTemplateRead.model_validate(prompt.model_dump())
        read.current_version = PromptTemplateVersionRead.model_validate(version.model_dump())
        return read

    @staticmethod
    async def list_versions(
        prompt_uuid: str,
        db_session: AsyncSession,
    ) -> list[PromptTemplateVersionRead]:
        prompt = (
            await db_session.execute(
                select(PromptTemplate).where(PromptTemplate.prompt_uuid == prompt_uuid)
            )
        ).scalars().first()
        if not prompt:
            return []

        versions = (
            await db_session.execute(
                select(PromptTemplateVersion)
                .where(PromptTemplateVersion.prompt_id == prompt.id)
                .order_by(PromptTemplateVersion.version_number.desc())
            )
        ).scalars().all()

        return [PromptTemplateVersionRead.model_validate(v.model_dump()) for v in versions]
