"""用户相关路由。"""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.api.deps import get_current_user, require_admin
from app.core.logging import read_logs
from app.crud.message import create_peer_message, get_peer_messages
from app.crud.token import get_online_count, get_register_count, purge_expired_tokens
from app.crud.user import list_contacts
from app.db.session import get_session
from app.models.token import AuthToken
from app.models.user import ModelConfig, User
from app.schemas.message import PeerMessageCreate, PeerMessagePublic
from app.schemas.user import UserContactStatusPublic
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

    payload_ws = {"type": "peer_message", "data": public_msg.model_dump()}
    await ws_manager.send_to(receiver.id, payload_ws)
    await ws_manager.send_to(user.id, payload_ws)

    return public_msg


@router.get("/stats/redis")
def redis_stats(session: Session = Depends(get_session)):
    return {
        "register_count": get_register_count(session),
        "online_count": get_online_count(session),
    }


@router.get("/dashboard")
def dashboard(request: Request, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    users = session.exec(select(User)).all()
    total_balance = sum(u.balance for u in users)
    models = session.exec(select(ModelConfig)).all()

    now = dt.datetime.now()
    client_ip = request.client.host if request.client else "unknown"
    weather = "晴朗"

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
