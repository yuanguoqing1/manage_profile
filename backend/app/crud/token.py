"""Token 与在线统计。"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import redis
from sqlalchemy import func
from sqlmodel import Session, select

from app.core.config import settings
from app.models.token import AuthToken
from app.models.user import User


def init_redis() -> Optional["redis.Redis"]:
    try:
        client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            decode_responses=True,
        )
        client.ping()
        return client
    except Exception as exc:  # noqa: BLE001
        logging.warning("Redis 连接失败，将使用数据库统计：%s", exc)
        return None


redis_client = init_redis()
if redis_client:
    logging.info("Redis 连接成功")
else:
    logging.info("Redis 不可用，使用数据库统计在线与注册数量")


def create_token(session: Session, token: str, user_id: int, expires_at: datetime | None) -> AuthToken:
    record = AuthToken(token=token, user_id=user_id, expires_at=expires_at)
    session.add(record)
    session.commit()
    return record


def get_token(session: Session, token: str) -> AuthToken | None:
    return session.get(AuthToken, token)


def delete_token(session: Session, token: str) -> None:
    record = session.get(AuthToken, token)
    if record:
        session.delete(record)
        session.commit()


def purge_expired_tokens(session: Session) -> int:
    now = datetime.utcnow()
    expired = session.exec(select(AuthToken).where(AuthToken.expires_at.is_not(None), AuthToken.expires_at < now)).all()
    for record in expired:
        session.delete(record)
    if expired:
        session.commit()
    return len(expired)


def increment_register_count() -> None:
    if redis_client:
        redis_client.incr("register_count")


def register_user_online(token: str) -> None:
    if redis_client:
        redis_client.sadd("online_tokens", token)


def logout_user_online(token: str) -> None:
    if redis_client:
        redis_client.srem("online_tokens", token)


def get_online_count(session: Session) -> int:
    if redis_client:
        return int(redis_client.scard("online_tokens"))
    purge_expired_tokens(session)
    return session.exec(select(func.count()).select_from(AuthToken)).one()[0]


def get_register_count(session: Session) -> int:
    if redis_client:
        value = redis_client.get("register_count")
        return int(value) if value else 0
    return session.exec(select(func.count()).select_from(User)).one()[0]
