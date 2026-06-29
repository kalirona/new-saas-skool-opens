import logging
import os

_LOG_CONFIGURED = False


async def create_logs_dir():
    if not os.path.exists("logs"):
        os.mkdir("logs")


async def init_logging():
    global _LOG_CONFIGURED
    if _LOG_CONFIGURED:
        return
    _LOG_CONFIGURED = True

    await create_logs_dir()

    log_level = os.environ.get("LEARNHOUSE_LOG_LEVEL", "INFO").upper()

    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
        handlers=[
            logging.FileHandler("logs/learnhouse.log"),
            logging.StreamHandler(),
        ],
    )

    logging.info("Logging initiated (level=%s)", log_level)
