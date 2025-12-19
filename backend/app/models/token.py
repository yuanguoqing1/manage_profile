"""Token 模型。"""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class AuthToken(SQLModel, table=True):
    token: str = Field(primary_key=True, index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
