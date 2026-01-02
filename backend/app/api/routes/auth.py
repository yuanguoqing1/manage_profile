"""认证路由。"""

from __future__ import annotations

import datetime as dt
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlmodel import Session

from app.core.config import settings
from app.core.security import generate_salt, hash_password
from app.crud.token import create_token, increment_register_count, register_user_online, logout_user_online, delete_token
from app.crud.user import admin_exists, create_user, get_user_by_name
from app.db.session import get_session
from app.models.user import Role, User
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.user import UserCreate, UserPublic
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, session: Session = Depends(get_session)):
    if not payload.password.strip():
        raise HTTPException(status_code=400, detail="密码不能为空")

    existing = get_user_by_name(session, payload.name)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    chosen_role = Role.user.value
    if payload.role:
        if payload.role == Role.admin and not admin_exists(session):
            chosen_role = payload.role.value
        elif payload.role == Role.user:
            chosen_role = payload.role.value

    salt = generate_salt()
    password_hash = hash_password(payload.password, salt)
    user = create_user(session, payload, chosen_role, password_hash, salt)

    increment_register_count()
    return UserPublic(
        id=user.id,
        name=user.name,
        balance=user.balance,
        role=user.role,
        email=user.email,
        phone=user.phone,
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    user = get_user_by_name(session, payload.name)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    hashed = hash_password(payload.password, user.salt)
    if hashed != user.password_hash:
        raise HTTPException(status_code=401, detail="密码错误")

    token = secrets.token_urlsafe(24)
    expires_at = dt.datetime.utcnow() + dt.timedelta(days=settings.token_expires_days)
    create_token(session, token, user.id, expires_at)

    register_user_online(token)

    public_user = UserPublic(
        id=user.id,
        name=user.name,
        balance=user.balance,
        role=user.role,
        email=user.email,
        phone=user.phone,
        LDC=user.LDC or 0,
        last_check_in=user.last_check_in,
    )
    return LoginResponse(token=token, user=public_user)


@router.post("/logout")
def logout(
    authorization: str = Header(default=None),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    token = authorization.split()[1]
    delete_token(session, token)
    logout_user_online(token)
    return {"message": f"{user.name} 已退出"}


@router.get("/me", response_model=UserPublic)
def get_me(user: User = Depends(get_current_user)):
    return UserPublic(
        id=user.id,
        name=user.name,
        balance=user.balance,
        role=user.role,
        email=user.email,
        phone=user.phone,
        LDC=user.LDC or 0,
        last_check_in=user.last_check_in,
    )
