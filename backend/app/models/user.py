"""用户与业务模型。"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from sqlalchemy import String
from sqlmodel import Field, SQLModel


class Role(str, Enum):
    admin = "admin"
    user = "user"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    balance: float = Field(default=0.0, ge=0.0)
    password_hash: str
    salt: str
    role: str = Field(default=Role.user.value, index=True)
    email: Optional[str] = Field(default=None, index=True, sa_type=String(255))
    phone: Optional[str] = Field(default=None, sa_type=String(20))
    LDC : Optional[int] = Field(default=0)
    last_check_in: Optional[date] = Field(default=None)

class ModelConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    base_url: str
    api_key: str
    model_name: str
    max_tokens: int = Field(default=4096, ge=1)
    temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")


class WebCategory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str = Field(default="")
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)


class WebPage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    category_id: int = Field(foreign_key="webcategory.id")
    url: str
    account: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    cookie: Optional[str] = Field(default=None)
    note: Optional[str] = Field(default=None)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)


class RolePrompt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    prompt: str


class Skill(SQLModel, table=True):
    """技能库：记录各种操作命令和知识"""
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    category: str = Field(default="其他", index=True)
    content: str  # Markdown 格式内容
    tags: Optional[str] = Field(default=None)  # 逗号分隔的标签
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    created_at: Optional[str] = Field(default=None)
    updated_at: Optional[str] = Field(default=None)


class SystemConfig(SQLModel, table=True):
    """系统配置：存储各种密钥和配置"""
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)
    value: str
    description: Optional[str] = Field(default=None)
    updated_at: Optional[str] = Field(default=None)

