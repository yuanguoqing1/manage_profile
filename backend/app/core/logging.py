"""日志配置与读取。"""

from __future__ import annotations

import logging
import logging.config
from pathlib import Path
from typing import List

LOG_FILE = Path("app.log")


def setup_logging() -> None:
    formatter = {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"}
    handlers = {
        "console": {"class": "logging.StreamHandler", "formatter": "default"},
        "file": {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": str(LOG_FILE),
            "encoding": "utf-8",
        },
    }
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"default": formatter},
            "handlers": handlers,
            "root": {"level": "INFO", "handlers": ["console", "file"]},
            "loggers": {
                "uvicorn": {"level": "ERROR", "handlers": ["console", "file"], "propagate": False},
                "uvicorn.error": {"level": "ERROR", "handlers": ["console", "file"], "propagate": False},
                "uvicorn.access": {"level": "ERROR", "handlers": ["console", "file"], "propagate": False},
                "fastapi": {"level": "INFO", "handlers": ["console", "file"], "propagate": False},
            },
        }
    )


def read_logs(max_lines: int = 200) -> List[str]:
    if not LOG_FILE.exists():
        return []
    lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
    return lines[-max_lines:]
