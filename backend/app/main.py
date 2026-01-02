from __future__ import annotations

import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.init_db import create_db_and_tables

setup_logging()

from app.api.router import api_router  # noqa: E402
from app.services.ws_manager import ws_manager  # noqa: E402
from app.services.memory_service import init_memory  # noqa: E402

app = FastAPI(title=settings.app_title, version=settings.app_version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务（上传的图片）
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# 前端静态文件目录
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()
    init_memory()  # 初始化AI记忆服务


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """优雅关闭所有WebSocket连接。"""
    await ws_manager.disconnect_all()


app.include_router(api_router)

# 挂载前端静态文件（放在 API 路由之后）
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="frontend-assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(request: Request, full_path: str):
        """服务前端 SPA，所有非 API 路由返回 index.html"""
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
