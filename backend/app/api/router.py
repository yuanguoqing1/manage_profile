"""API 路由汇总。"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import auth, chat, models, users, ws

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(models.router)
api_router.include_router(users.router)
api_router.include_router(chat.router)
api_router.include_router(ws.router)
