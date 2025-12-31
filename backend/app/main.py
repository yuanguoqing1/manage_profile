from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.init_db import create_db_and_tables

setup_logging()

from app.api.router import api_router  # noqa: E402
from app.services.ws_manager import ws_manager  # noqa: E402

app = FastAPI(title=settings.app_title, version=settings.app_version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """优雅关闭所有WebSocket连接。"""
    await ws_manager.disconnect_all()


app.include_router(api_router)
