"""认证相关 schema。"""

from __future__ import annotations

from sqlmodel import SQLModel

from app.schemas.user import UserPublic


class LoginRequest(SQLModel):
    name: str
    password: str


class LoginResponse(SQLModel):
    token: str
    user: UserPublic
