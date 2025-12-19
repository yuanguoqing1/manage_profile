"""日志配置与读取。"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

LOG_FILE = Path("app.log")


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(LOG_FILE, encoding="utf-8")],
    )


def read_logs(max_lines: int = 200) -> List[str]:
    if not LOG_FILE.exists():
        return []
    lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
    return lines[-max_lines:]
