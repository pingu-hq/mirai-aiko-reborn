import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from app.core.local_config import settings

def setup_logger(name: str = "fast_api", log_level: str = "INFO") -> logging.Logger:

    logger = logging.getLogger(name=name)

    if logger.hasHandlers():
        return logger

    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    app_file_handler = RotatingFileHandler(
        log_dir / "app.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    app_file_handler.setFormatter(formatter)
    app_file_handler.setLevel(logging.INFO)
    logger.addHandler(app_file_handler)

    error_file_handler = RotatingFileHandler(
        log_dir / "error.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    error_file_handler.setFormatter(formatter)
    error_file_handler.setLevel(logging.ERROR)
    logger.addHandler(error_file_handler)

    return logger

def setup_logger_with_config():
    if settings.project_development_mode:
        log_level = "DEBUG"
    else:
        log_level = "INFO"
    return setup_logger(log_level=log_level)

app_logger = setup_logger_with_config()