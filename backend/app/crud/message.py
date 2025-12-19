"""消息相关数据库操作。"""

from __future__ import annotations

from sqlmodel import Session, select
from sqlalchemy import and_, or_

from app.models.message import PeerMessage


def get_peer_messages(session: Session, user_id: int, peer_id: int) -> list[PeerMessage]:
    query = (
        select(PeerMessage)
        .where(
            or_(
                and_(PeerMessage.sender_id == user_id, PeerMessage.receiver_id == peer_id),
                and_(PeerMessage.sender_id == peer_id, PeerMessage.receiver_id == user_id),
            )
        )
        .order_by(PeerMessage.created_at)
    )
    return session.exec(query).all()


def create_peer_message(session: Session, sender_id: int, receiver_id: int, content: str) -> PeerMessage:
    message = PeerMessage(sender_id=sender_id, receiver_id=receiver_id, content=content)
    session.add(message)
    session.commit()
    session.refresh(message)
    return message
