"""用户相关路由。"""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session, select

from app.api.deps import get_current_user, require_admin
from app.core.logging import read_logs
from app.core.security import generate_salt, hash_password
from app.crud.message import create_peer_message, get_peer_messages
from app.crud.token import get_online_count, get_register_count, purge_expired_tokens
from app.crud.user import get_user_by_name, list_contacts
from app.db.session import get_session
from app.models.token import AuthToken
from app.models.user import ModelConfig, User
from app.schemas.message import PeerMessageCreate, PeerMessagePublic
from app.schemas.user import UserContactStatusPublic, UserPublic, UserUpdate
from app.services.weather_service import get_weather_by_city
from app.services.ws_manager import ws_manager

router = APIRouter(tags=["users"])


@router.get("/health")
def healthcheck():
    return {"status": "ok"}


@router.get("/contacts", response_model=list[UserContactStatusPublic])
def list_contacts_route(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    purge_expired_tokens(session)
    online_user_ids = {record.user_id for record in session.exec(select(AuthToken)).all()}

    contacts = list_contacts(session, user.id)
    return [
        UserContactStatusPublic(
            id=item.id,
            name=item.name,
            role=item.role,
            is_online=(item.id in online_user_ids) or ws_manager.is_ws_online(item.id),
        )
        for item in contacts
    ]


@router.get("/contacts/messages/{peer_id}", response_model=list[PeerMessagePublic])
def get_peer_messages_route(peer_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    peer = session.get(User, peer_id)
    if not peer:
        raise HTTPException(status_code=404, detail="联系人不存在")

    messages = get_peer_messages(session, user.id, peer_id)
    return [
        PeerMessagePublic(
            id=msg.id,
            sender_id=msg.sender_id,
            receiver_id=msg.receiver_id,
            sender_name=peer.name if msg.sender_id == peer.id else user.name,
            receiver_name=peer.name if msg.receiver_id == peer.id else user.name,
            content=msg.content,
            created_at=msg.created_at,
        )
        for msg in messages
    ]


@router.post("/contacts/messages", response_model=PeerMessagePublic, status_code=201)
async def create_peer_message_route(
    payload: PeerMessageCreate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    import logging
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="内容不能为空")
    if payload.receiver_id == user.id:
        raise HTTPException(status_code=400, detail="不能给自己发送消息")

    receiver = session.get(User, payload.receiver_id)
    if not receiver:
        raise HTTPException(status_code=404, detail="联系人不存在")

    message = create_peer_message(session, user.id, payload.receiver_id, content)

    public_msg = PeerMessagePublic(
        id=message.id,
        sender_id=message.sender_id,
        receiver_id=message.receiver_id,
        sender_name=user.name,
        receiver_name=receiver.name,
        content=message.content,
        created_at=message.created_at,
    )

    payload_ws = {"type": "peer_message", "data": public_msg.model_dump(mode="json")}
    logging.info(f"[WS] 推送消息给 receiver_id={receiver.id}, sender_id={user.id}")
    await ws_manager.send_to(receiver.id, payload_ws)
    await ws_manager.send_to(user.id, payload_ws)
    logging.info("[WS] 推送完成")

    return public_msg


@router.get("/stats/redis")
def redis_stats(session: Session = Depends(get_session)):
    return {
        "register_count": get_register_count(session),
        "online_count": get_online_count(session),
    }


@router.get("/dashboard")
def dashboard(
    request: Request,
    city: str = Query(default="", description="城市名称"),
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    users = session.exec(select(User)).all()
    total_balance = sum(u.balance for u in users)
    models = session.exec(select(ModelConfig)).all()

    now = dt.datetime.now()
    client_ip = request.client.host if request.client else "unknown"
    weather = get_weather_by_city(city)

    return {
        "summary": {"user_count": len(users), "total_balance": total_balance, "model_count": len(models)},
        "redis": redis_stats(session),
        "date": now.strftime("%Y-%m-%d %H:%M"),
        "ip": client_ip,
        "weather": weather,
        "me": {"id": user.id, "name": user.name, "role": user.role},
    }


@router.get("/logs")
def get_logs(limit: int = 200, _: User = Depends(require_admin)):
    return {"lines": read_logs(max_lines=max(10, min(limit, 1000)))}


@router.put("/users/{user_id}", response_model=UserPublic)
def update_user_profile(
    user_id: int,
    payload: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """更新用户信息（用户只能修改自己的信息，管理员可以修改任何人）。"""
    # 检查权限：只能修改自己的信息，除非是管理员
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权修改其他用户信息")
    
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    update_data = payload.model_dump(exclude_unset=True)
    
    # 普通用户不能修改自己的角色
    if "role" in update_data and current_user.role != "admin":
        del update_data["role"]
    
    # 如果修改用户名，检查是否重复
    if "name" in update_data and update_data["name"] != user.name:
        existing = get_user_by_name(session, update_data["name"])
        if existing:
            raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 如果更新密码，需要重新哈希
    if "password" in update_data and update_data["password"]:
        salt = generate_salt()
        update_data["password_hash"] = hash_password(update_data["password"], salt)
        update_data["salt"] = salt
        del update_data["password"]

    for key, value in update_data.items():
        setattr(user, key, value)
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
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
#签到功能    
@router.post("/user/check_in")
def check_in(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    from datetime import date, timedelta
    
    today = date.today()
    
    # 检查今天是否已签到
    if current_user.last_check_in == today:
        raise HTTPException(status_code=400, detail="今天已经签到过了")
    
    # 判断是否连续签到
    if current_user.last_check_in == today - timedelta(days=1):
        # 昨天签到了，连续天数+1
        current_user.LDC = (current_user.LDC or 0) + 1
    else:
        # 断签了，重置为1
        current_user.LDC = 1
    
    # 更新签到日期
    current_user.last_check_in = today
    
    # 奖励：根据连续天数给不同奖励，最多7倍
    reward = min(current_user.LDC, 7)
    current_user.balance += reward
    
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return {
        "message": "签到成功",
        "LDC": current_user.LDC,
        "reward": reward,
        "balance": current_user.balance
    }
    
