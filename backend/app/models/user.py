"""用户与业务模型。"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

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
    name: str = Field(index=True, unique=True)
    description: str = Field(default="")


class WebPage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    category_id: int = Field(foreign_key="webcategory.id")
    url: str
    account: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    cookie: Optional[str] = Field(default=None)
    note: Optional[str] = Field(default=None)


class RolePrompt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    prompt: str


class JobAutomationConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=1, primary_key=True)
    service_url: str = Field(default="", description="get_jobs 服务接收任务的地址")
    service_token: Optional[str] = Field(default=None, description="get_jobs 服务鉴权 token，可选")
    resume_link: Optional[str] = Field(default=None, description="简历链接或存储地址")
    greeting: str = Field(default="您好，我对岗位很感兴趣，这是我的简历，期待沟通。", description="开场白模板")
    keywords: str = Field(default="", description="投递关键词，逗号分隔")
    cities: str = Field(default="", description="城市列表，逗号分隔")
    auto_apply: bool = Field(default=True, description="是否自动投递")
    auto_greet: bool = Field(default=True, description="是否自动打招呼")
    daily_limit: int = Field(default=30, description="每日最大投递数量")


class JobRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    status: str = Field(default="pending")
    message: str = Field(default="")
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    requested_by: int
    keywords: Optional[str] = None
    cities: Optional[str] = None
    resume_link: Optional[str] = None
    greeting: Optional[str] = None
    auto_apply: Optional[bool] = None
    auto_greet: Optional[bool] = None
    daily_limit: Optional[int] = None
