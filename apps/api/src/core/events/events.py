import asyncio
import logging
from typing import Callable
from fastapi import FastAPI
from config.config import LearnHouseConfig, get_learnhouse_config
from src.core.events.autoinstall import auto_install
from src.core.events.content import check_content_directory
from src.core.events.database import close_database, connect_to_db
from src.core.events.logs import create_logs_dir, init_logging
from src.core.ee_hooks import run_ee_startup

logger = logging.getLogger(__name__)

_cleanup_task = None


async def _periodic_migration_cleanup():
    from src.services.courses.migration.migration_service import cleanup_old_temp_migrations
    while True:
        await asyncio.sleep(600)
        try:
            cleanup_old_temp_migrations()
        except Exception as e:
            logger.warning("Periodic migration cleanup failed: %s", e)


async def _reconcile_packs():
    try:
        from src.core.events.database import _async_session_factory
        from src.services.packs.packs import reconcile_pack_credits
        async with _async_session_factory() as db_session:
            result = await reconcile_pack_credits(db_session)
            logger.info("Pack reconciliation on startup: %s", result)
    except Exception as e:
        logger.warning("Pack reconciliation skipped: %s", e)


def startup_app(app: FastAPI) -> Callable:
    async def start_app() -> None:
        learnhouse_config: LearnHouseConfig = get_learnhouse_config()
        app.learnhouse_config = learnhouse_config

        await connect_to_db(app)
        await init_logging()
        await check_content_directory()
        await auto_install()
        await _reconcile_packs()

        from src.services.courses.migration.migration_service import cleanup_old_temp_migrations
        cleanup_old_temp_migrations()
        global _cleanup_task
        _cleanup_task = asyncio.create_task(_periodic_migration_cleanup())

        run_ee_startup(app)

    return start_app


def shutdown_app(app: FastAPI) -> Callable:
    async def close_app() -> None:
        if _cleanup_task:
            _cleanup_task.cancel()
            try:
                await _cleanup_task
            except asyncio.CancelledError:
                pass

        from src.core.tasks.executor import get_executor
        await get_executor().shutdown()

        from src.services.webhooks.dispatch import close_webhook_client
        await close_webhook_client()
        await close_database(app)

    return close_app
