"""数据库会话与初始化配置。"""

from __future__ import annotations

from sqlmodel import Session, SQLModel, create_engine

sqlite_url = "sqlite:///./data.db"
engine = create_engine(sqlite_url, echo=False, connect_args={"check_same_thread": False})


def ensure_columns() -> None:
    """确保旧表拥有新字段，缺失时自动补齐。"""

    required_columns = {
        "user": {
            "password_hash": "TEXT",
            "salt": "TEXT",
            "role": "TEXT DEFAULT 'user'",
        }
    }
    with engine.begin() as conn:
        for table, columns in required_columns.items():
            existing = {row[1] for row in conn.exec_driver_sql(f'PRAGMA table_info("{table}")').all()}
            for column, sql_type in columns.items():
                if column not in existing:
                    conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}")  # noqa: S608


def create_db_and_tables() -> None:
    """初始化数据库并创建表结构。"""

    SQLModel.metadata.create_all(engine)
    ensure_columns()


def get_session():
    """获取数据库会话。"""

    with Session(engine) as session:
        yield session
