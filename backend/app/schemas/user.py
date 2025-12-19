"""用户相关 schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel

from app.models.user import Role


class UserCreate(SQLModel):
    name: str
    password: str
    role: Optional[Role] = None


class UserPublic(SQLModel):
    id: int
    name: str
    balance: float
    role: str


class UserContactPublic(SQLModel):
    id: int
    name: str
    role: str


class UserContactStatusPublic(UserContactPublic):
    is_online: bool


class BalanceUpdate(SQLModel):
    amount: float


class UserUpdate(SQLModel):
    name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[Role] = None


class RoleUpdate(SQLModel):
    user_id: int
    role: Role


class ModelConfigCreate(SQLModel):
    name: str
    base_url: str
    api_key: str
    model_name: str
    max_tokens: int = 4096
    temperature: float = 1.0
    owner_id: Optional[int] = None


class ModelConfigUpdate(SQLModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    owner_id: Optional[int] = None


class ModelConfigPublic(SQLModel):
    id: int
    name: str
    base_url: str
    api_key: str
    model_name: str
    max_tokens: int
    temperature: float
    owner_id: Optional[int]


class WebCategoryCreate(SQLModel):
    name: str
    description: str = ""


class WebCategoryPublic(SQLModel):
    id: int
    name: str
    description: str


class WebPageCreate(SQLModel):
    category_id: int
    url: str
    account: Optional[str] = None
    password: Optional[str] = None
    cookie: Optional[str] = None
    note: Optional[str] = None


class WebPagePublic(SQLModel):
    id: int
    category_id: int
    url: str
    account: Optional[str]
    password: Optional[str]
    cookie: Optional[str]
    note: Optional[str]


class RolePromptCreate(SQLModel):
    name: str
    prompt: str


class RolePromptUpdate(SQLModel):
    name: Optional[str] = None
    prompt: Optional[str] = None


class RolePromptPublic(SQLModel):
    id: int
    name: str
    prompt: str


class JobAutomationConfigPublic(SQLModel):
    id: int
    service_url: str
    service_token: Optional[str]
    resume_link: Optional[str]
    greeting: str
    keywords: str
    cities: str
    auto_apply: bool
    auto_greet: bool
    daily_limit: int


class JobAutomationConfigUpdate(SQLModel):
    service_url: Optional[str] = None
    service_token: Optional[str] = None
    resume_link: Optional[str] = None
    greeting: Optional[str] = None
    keywords: Optional[str] = None
    cities: Optional[str] = None
    auto_apply: Optional[bool] = None
    auto_greet: Optional[bool] = None
    daily_limit: Optional[int] = None


class JobRunPublic(SQLModel):
    id: int
    status: str
    message: str
    requested_at: datetime
    finished_at: Optional[datetime]
    requested_by: int
    keywords: Optional[str]
    cities: Optional[str]
    resume_link: Optional[str]
    greeting: Optional[str]
    auto_apply: Optional[bool]
    auto_greet: Optional[bool]
    daily_limit: Optional[int]


class JobRunRequest(SQLModel):
    keywords: Optional[str] = None
    cities: Optional[str] = None
    resume_link: Optional[str] = None
    greeting: Optional[str] = None
    auto_apply: Optional[bool] = None
    auto_greet: Optional[bool] = None
    daily_limit: Optional[int] = None
