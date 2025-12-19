"""聊天路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.message import ChatCompletionRequest, ChatCompletionResponse
from app.services.chat_service import build_chat_request, fetch_chat_completion, stream_chat_completion

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/completions", response_model=ChatCompletionResponse)
def create_chat_completion(
    payload: ChatCompletionRequest,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    model, target_url, request_body = build_chat_request(session, payload, user)
    if payload.stream:
        return stream_chat_completion(model, target_url, request_body)
    return fetch_chat_completion(model, target_url, request_body)
