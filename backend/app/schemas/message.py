"""消息相关 schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Union

from sqlmodel import SQLModel


class ChatMessage(SQLModel):
    role: str
    content: str


class PeerMessageCreate(SQLModel):
    receiver_id: int
    content: str


class PeerMessagePublic(SQLModel):
    id: int
    sender_id: int
    receiver_id: int
    sender_name: str
    receiver_name: str
    content: str
    created_at: datetime


class ChatCompletionRequest(SQLModel):
    model_id: Optional[int] = None
    messages: List[ChatMessage]
    stream: bool = False
    role_prompt: Optional[str] = None
    role_id: Optional[int] = None


UsageValue = Union[int, Dict[str, int]]


class ChatCompletionResponse(SQLModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, object]]
    usage: Dict[str, UsageValue]
