import os
import sys
from typing import Literal

from loguru import logger

from app.core.config import settings


class LoguruHandler:
    loguru_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan> | "
        "<cyan>{function}</cyan> | "
        "<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    def setup_logger(self, setup_type: Literal["auto","dev","prod"] = "auto"):

        os.makedirs("logs", exist_ok=True)
        logger.remove()

        if setup_type == "auto":
            if settings.is_deployed_for_production:
                self.production()
            else:
                self.development()

        elif setup_type == "dev":
            self.development()
        elif setup_type == "prod":
            self.production()

    def production(self) -> None:
        logger.add(
            sys.stderr,
            format=self.loguru_format,
            level="INFO",
            colorize=True,
        )

        logger.add(
            "logs/app.log",
            format=self.loguru_format,
            level="INFO",
            rotation="200 MB",
            retention="10 days",
            compression="zip",
            encoding="utf-8",
            enqueue=True,
        )
        logger.add(
            "logs/error.log",
            format=self.loguru_format,
            level="ERROR",
            rotation="200 MB",
            retention="10 days",
            compression="zip",
            encoding="utf-8",
            enqueue=True,
        )
    def development(self) -> None:
        logger.add(
            sys.stderr,
            format=self.loguru_format,
            level="DEBUG",
            colorize=True,
        )
        logger.add(
            "logs/test.log",
            format=self.loguru_format,
            level="DEBUG",
            rotation="10 MB",
            retention="5 days",
            compression="zip",
            encoding="utf-8",
            enqueue=False,
        )
