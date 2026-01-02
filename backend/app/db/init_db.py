"""初始化数据库结构。"""

from __future__ import annotations

from sqlmodel import SQLModel

from app.db.session import engine
from app.models import album as album_models  # noqa: F401
from app.models import diary as diary_models  # noqa: F401
from app.models import message as message_models  # noqa: F401
from app.models import token as token_models  # noqa: F401
from app.models import user as user_models  # noqa: F401


def create_db_and_tables() -> None:
    """初始化数据库并创建表结构。"""
    SQLModel.metadata.create_all(engine)
