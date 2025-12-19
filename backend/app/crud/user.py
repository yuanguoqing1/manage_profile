"""用户相关数据库操作。"""

from __future__ import annotations

from sqlmodel import Session, select

from app.models.user import Role, User
from app.schemas.user import UserCreate


def admin_exists(session: Session) -> bool:
    return session.exec(select(User).where(User.role == Role.admin.value)).first() is not None


def get_user_by_name(session: Session, name: str) -> User | None:
    return session.exec(select(User).where(User.name == name)).first()


def create_user(session: Session, payload: UserCreate, role_value: str, password_hash: str, salt: str) -> User:
    user = User(name=payload.name, balance=0.0, password_hash=password_hash, salt=salt, role=role_value)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def list_contacts(session: Session, user_id: int) -> list[User]:
    return session.exec(select(User).where(User.id != user_id)).all()
