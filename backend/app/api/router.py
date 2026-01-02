"""API 路由汇总。"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import admin, album, auth, chat, diary, memory, models, role_prompts, users, web, ws

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(models.router)
api_router.include_router(users.router)
api_router.include_router(role_prompts.router)
api_router.include_router(web.router)
api_router.include_router(chat.router)
api_router.include_router(memory.router)
api_router.include_router(diary.router, prefix="/diaries", tags=["diaries"])
api_router.include_router(album.router, tags=["album"])
api_router.include_router(ws.router)
