"""应用配置。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_title: str = "个人管理系统"
    app_version: str = "0.2.0"
    token_expires_days: int = int(os.getenv("TOKEN_EXPIRES_DAYS", "7"))
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: str | None = os.getenv("REDIS_PASSWORD")


settings = Settings()
