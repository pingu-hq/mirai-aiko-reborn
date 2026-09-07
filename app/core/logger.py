import os
import sys

from loguru import logger

from app.core.config import settings

LOGURU_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan> | "
    "<cyan>{function}</cyan> | "
    "<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

def initialize_setup_logger() -> None:
    if settings.is_deployed_for_production:
        enqueue = True
    else:
        enqueue = False
        
    os.makedirs("logs", exist_ok=True)
    logger.remove()
    logger.add(
        sys.stderr,
        format=LOGURU_FORMAT,
        level="INFO",
        colorize=True,
    )

    logger.add(
        "logs/app.log",
        format=LOGURU_FORMAT,
        level="INFO",
        rotation="10 MB",
        retention="10 days",
        compression="zip",
        encoding="utf-8",
        enqueue=enqueue,
    )
    logger.add(
        "logs/error.log",
        format=LOGURU_FORMAT,
        level="ERROR",
        rotation="10 MB",
        retention="10 days",
        compression="zip",
        encoding="utf-8",
        enqueue=enqueue,
    )
