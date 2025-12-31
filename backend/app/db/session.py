"""数据库会话与配置。"""

from __future__ import annotations

import os
from sqlmodel import Session, create_engine
from sqlalchemy.engine import Engine


def _mysql_url() -> str:

    user = os.getenv("MYSQL_USER", "manage_profile")
    password = os.getenv("MYSQL_PASSWORD", "123456")
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = os.getenv("MYSQL_PORT", "3306")
    db = os.getenv("MYSQL_DB", "manage_profile")
    # PyMySQL 驱动写法：mysql+pymysql://
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4"


DATABASE_URL = os.getenv("DATABASE_URL") or _mysql_url()

engine: Engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,   # 避免 MySQL 连接被踢后报错
    pool_recycle=3600,    # 防止长连接超时
)


def get_session():
    """获取数据库会话。"""
    with Session(engine) as session:
        yield session
