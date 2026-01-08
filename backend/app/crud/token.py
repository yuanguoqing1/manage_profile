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
    """获取在线人数（10分钟内有活跃请求的用户数）"""
    if redis_client:
        try:
            # 使用 Redis ZSET 存储用户活跃时间，获取10分钟内活跃的用户数
            import time
            cutoff_time = time.time() - 600  # 10分钟前
            # 清理过期的活跃记录
            redis_client.zremrangebyscore("user_activity", 0, cutoff_time)
            # 获取活跃用户数
            return redis_client.zcard("user_activity")
        except Exception:
            pass
    
    # 降级：返回有效 token 数量
    purge_expired_tokens(session)
    return session.exec(select(func.count()).select_from(AuthToken)).one()


def update_user_activity(user_id: int) -> None:
    """更新用户活跃时间"""
    if redis_client:
        try:
            import time
            redis_client.zadd("user_activity", {str(user_id): time.time()})
        except Exception:
            pass


def get_register_count(session: Session) -> int:
    # 始终从数据库获取真实的用户总数
    count = session.exec(select(func.count()).select_from(User)).one()
    
    # 如果Redis可用，同步更新Redis中的值
    if redis_client:
        redis_client.set("register_count", count)
    
    return count
