"""依赖注入。"""

from __future__ import annotations

from datetime import datetime

from fastapi import Depends, Header, HTTPException, status
from sqlmodel import Session

from app.crud.token import get_token
from app.db.session import get_session
from app.models.token import AuthToken
from app.models.user import User


def _validate_token_record(record: AuthToken) -> None:
    if record.expires_at is not None and record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期")


def get_current_user(
    authorization: str = Header(default=None),
    session: Session = Depends(get_session),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少凭证")
    token = authorization.split()[1]

    record = get_token(session, token)
    if not record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效")
    _validate_token_record(record)

    user = session.get(User, record.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user


def get_user_by_token(token: str, session: Session) -> User:
    record = get_token(session, token)
    if not record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效")
    _validate_token_record(record)

    user = session.get(User, record.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user
