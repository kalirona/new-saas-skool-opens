"""Schema-version verification using Alembic at startup.

Replaces the old ``create_all``-on-every-startup pattern.  On production
deployments Alembic is the single source of truth; this module checks
that the database is at the expected migration head before the app serves
traffic.
"""

import logging
import os

from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory
from sqlalchemy import inspect as sa_inspect, text as sa_text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)

_ALEMBIC_INI_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "alembic.ini"
)


def _get_alembic_head() -> str | None:
    """Return the Alembic head revision string, or ``None`` on error."""
    try:
        alembic_cfg = AlembicConfig(_ALEMBIC_INI_PATH)
        script = ScriptDirectory.from_config(alembic_cfg)
        head = script.get_current_head()
        return head
    except Exception:
        logger.error("Failed to read Alembic head revision", exc_info=True)
        return None


async def verify_schema_version(engine: AsyncEngine) -> None:
    """Check that the database schema matches the Alembic head revision.

    Raises ``RuntimeError`` (fail-fast) in production when:
      - The ``alembic_version`` table is missing but other tables exist.
      - The current revision does not match the configured head.
    Logs a warning on a completely empty (fresh) database so that the
    auto-installer can create the schema later in the startup sequence.
    """
    if os.getenv("TESTING", "").lower() in ("true", "1", "yes"):
        logger.info("Testing mode: skipping schema version check")
        return

    head = _get_alembic_head()
    if head is None:
        raise RuntimeError(
            "Could not determine Alembic head revision. "
            "Ensure alembic.ini and migrations/ are intact."
        )

    async with engine.connect() as conn:
        inspector = sa_inspect(conn.sync_engine)
        all_tables = inspector.get_table_names()
        has_alembic_table = "alembic_version" in all_tables

        if not has_alembic_table:
            if not all_tables:
                logger.info(
                    "Fresh database detected (no tables). "
                    "Skipping schema check — auto-install or "
                    "'alembic upgrade head' must create the schema."
                )
                return

            raise RuntimeError(
                "Database has tables but no 'alembic_version' table. "
                "The schema was likely created with the old 'create_all' "
                "pattern. Run 'alembic stamp head' to mark the current "
                "state, then apply any pending migrations with "
                "'alembic upgrade head'."
            )

        row = (await conn.execute(sa_text("SELECT version_num FROM alembic_version"))).first()
        current_rev = str(row[0]) if row else None

        if current_rev != head:
            raise RuntimeError(
                f"Schema version mismatch: database is at {current_rev!r}, "
                f"but Alembic head is {head!r}. "
                "Run 'alembic upgrade head' to apply pending migrations."
            )

        logger.info("Schema version verified: %s (head: %s)", current_rev, head)
