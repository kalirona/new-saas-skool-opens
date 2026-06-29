import re
from typing import List
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.users import User


MENTION_PATTERN = re.compile(r'@([\w.]+)')


def parse_mentions(content: str) -> List[str]:
    """
    Extract @username mentions from content.
    Returns list of unique usernames.
    """
    if not content:
        return []
    mentions = MENTION_PATTERN.findall(content)
    return list(set(mentions))


async def resolve_mention_user_ids(
    usernames: List[str],
    db_session: AsyncSession,
) -> List[int]:
    """
    Resolve @mentions to user IDs.
    """
    if not usernames:
        return []

    statement = select(User.id).where(User.username.in_(usernames))
    result = await db_session.execute(statement)
    return [row[0] for row in result.all()]
