from __future__ import annotations

import logging
from typing import Any, AsyncGenerator, Optional, TypeAlias

from pydantic import BaseModel, Field
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from src.services.ai.prompt_sanitizer import sanitize_user_input
from src.services.ai.studio.conversation import ConversationManager
from src.services.ai.studio.generation_service import AIGenerationService

logger = logging.getLogger(__name__)


class ContextQuery(BaseModel):
    entity_type: str = Field(description="Type: course, resource, community, event, setting")
    query: str = Field(description="Search query")
    org_id: int
    limit: int = 5


class AssistantResponse(BaseModel):
    answer: str = Field(description="Answer to the user's question")
    sources: list[dict] = Field(default_factory=list, description="Source references used")
    requires_rag: bool = Field(default=False, description="Whether RAG indexing is needed for deeper answers")


SYSTEM_PROMPT = (
    "You are a helpful workspace assistant for an online learning platform called LearnHouse. "
    "You can answer questions about courses, resources, communities, events, and creator settings. "
    "Use the provided context to give accurate, helpful answers. "
    "If you don't know the answer based on the context, say so and suggest what the user can do. "
    "Keep answers concise and actionable."
)

RAG_PLACEHOLDER_NOTE = (
    "\n\n*Note: For deeper search across all content, the RAG (Retrieval-Augmented Generation) "
    "system can be enabled. Contact your administrator to activate full semantic search.*"
)


class WorkspaceAssistant:
    """Workspace AI assistant with RAG-ready architecture.

    Current implementation uses keyword/DB queries to fetch context.
    When RAG is enabled, ``_query_context`` can be replaced with vector search.
    """

    def __init__(self, ai_service: AIGenerationService):
        self._ai = ai_service
        self._conversation = ConversationManager(max_history=20)

    @property
    def conversation(self) -> ConversationManager:
        return self._conversation

    async def _query_context(
        self,
        query: str,
        entity_type: Optional[str],
        org_id: int,
        db_session: AsyncSession,
        rag_enabled: bool = False,
    ) -> tuple[list[dict], bool]:
        """Query database context based on entity type.

        RAG-ready: when ``rag_enabled`` is True, this should delegate to
        vector search instead of keyword matching.
        """
        if rag_enabled:
            return [], True

        results: list[dict] = []
        types_to_check = [entity_type] if entity_type else ["course", "resource", "community", "event"]

        for etype in types_to_check:
            if etype == "course":
                from src.db.courses.courses import Course
                stmt = select(Course).where(
                    Course.org_id == org_id,
                    Course.name.ilike(f"%{query}%"),
                ).limit(5)
                rows = (await db_session.execute(stmt)).scalars().all()
                for r in rows:
                    results.append({"type": "course", "title": r.name, "uuid": r.course_uuid, "description": r.description})

            elif etype == "resource":
                from src.db.resources.resources import Resource
                stmt = select(Resource).where(
                    Resource.org_id == org_id,
                    Resource.title.ilike(f"%{query}%"),
                ).limit(5)
                rows = (await db_session.execute(stmt)).scalars().all()
                for r in rows:
                    results.append({"type": "resource", "title": r.title, "uuid": r.resource_uuid, "description": r.description})

            elif etype == "community":
                from src.db.communities.communities import Community
                stmt = select(Community).where(
                    Community.org_id == org_id,
                    Community.name.ilike(f"%{query}%"),
                ).limit(5)
                rows = (await db_session.execute(stmt)).scalars().all()
                for r in rows:
                    results.append({"type": "community", "title": r.name, "uuid": r.community_uuid, "description": r.description})

            elif etype == "event":
                from src.db.events.events import Event
                stmt = select(Event).where(
                    Event.org_id == org_id,
                    Event.title.ilike(f"%{query}%"),
                ).limit(5)
                rows = (await db_session.execute(stmt)).scalars().all()
                for r in rows:
                    results.append({"type": "event", "title": r.title, "uuid": r.event_uuid, "description": r.description, "start_date": r.start_date})

        return results, False

    def _build_context_prompt(self, sources: list[dict]) -> str:
        if not sources:
            return "No matching content found in the workspace."
        lines = ["Here is the relevant workspace content:"]
        for s in sources:
            lines.append(f"- [{s['type']}] {s['title']}: {s.get('description', '')}")
        return "\n".join(lines)

    async def ask(
        self,
        query: str,
        org_id: int,
        user_id: int,
        db_session: AsyncSession,
        entity_type: Optional[str] = None,
        rag_enabled: bool = False,
        model_name: Optional[str] = None,
    ) -> AssistantResponse:
        sources, needs_rag = await self._query_context(query, entity_type, org_id, db_session, rag_enabled)

        context_text = self._build_context_prompt(sources)
        self._conversation.add_user_message(query)

        sanitized_query = sanitize_user_input(query)
        full_user_prompt = (
            f"User question: {sanitized_query}\n\n"
            f"Workspace context:\n{context_text}\n"
            f"{RAG_PLACEHOLDER_NOTE if not rag_enabled else ''}"
        )

        result = await self._ai.generate(
            user_prompt=full_user_prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=2048,
            model_name=model_name,
        )

        answer = result.content
        if isinstance(answer, dict) and "answer" in answer:
            answer = answer["answer"]

        self._conversation.add_assistant_message(str(answer))

        return AssistantResponse(
            answer=str(answer),
            sources=sources,
            requires_rag=needs_rag,
        )

    async def ask_stream(
        self,
        query: str,
        org_id: int,
        db_session: AsyncSession,
        entity_type: Optional[str] = None,
        rag_enabled: bool = False,
        model_name: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        sources, needs_rag = await self._query_context(query, entity_type, org_id, db_session, rag_enabled)
        context_text = self._build_context_prompt(sources)

        sanitized_query = sanitize_user_input(query)
        full_user_prompt = (
            f"User question: {sanitized_query}\n\n"
            f"Workspace context:\n{context_text}\n"
            f"{RAG_PLACEHOLDER_NOTE if not rag_enabled else ''}"
        )

        self._conversation.add_user_message(query)

        full_response: list[str] = []
        async for chunk in self._ai.generate_stream(
            user_prompt=full_user_prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=2048,
            model_name=model_name,
        ):
            full_response.append(chunk)
            yield chunk

        self._conversation.add_assistant_message("".join(full_response))
