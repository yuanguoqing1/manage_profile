"""Alembic 环境配置。"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

# 导入数据库 URL 和所有模型
from app.db.session import DATABASE_URL
from app.models import message, token, user  # noqa: F401

# Alembic Config 对象
config = context.config

# 解释 Python 日志配置文件
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 添加模型的 MetaData 对象以支持自动生成迁移
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """在 'offline' 模式下运行迁移。"""
    url = DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在 'online' 模式下运行迁移。"""
    # 创建配置字典
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = DATABASE_URL
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
