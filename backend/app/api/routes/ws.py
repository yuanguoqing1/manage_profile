"""WebSocket 路由。"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlmodel import Session

from app.api.deps import get_user_by_token
from app.db.session import engine
from app.services.ws_manager import ws_manager

router = APIRouter()


@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    token = ws.query_params.get("token")
    if not token:
        auth_header = ws.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split()[1]

    if not token:
        await ws.accept()
        await ws.close(code=status.WS_1008_POLICY_VIOLATION, reason="缺少 token")
        return

    with Session(engine) as session:
        try:
            user = get_user_by_token(token, session)
        except HTTPException as exc:
            await ws.accept()
            await ws.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(exc.detail))
            return

        user_id = user.id

    await ws_manager.connect(user_id, ws)
    try:
        while True:
            try:
                # 60秒超时，给前端足够时间发心跳
                data = await asyncio.wait_for(ws.receive_text(), timeout=60.0)
                # 处理心跳
                if data in ("ping", "pong"):
                    await ws.send_text("pong")
                else:
                    logging.debug(f"[WS] user_id={user_id} 收到: {data}")
            except asyncio.TimeoutError:
                # 超时后发送心跳检测
                try:
                    await ws.send_text("ping")
                except Exception:
                    logging.info(f"[WS] user_id={user_id} 心跳发送失败，断开")
                    break
    except WebSocketDisconnect:
        logging.info(f"[WS] user_id={user_id} 客户端断开")
    except Exception as e:
        logging.warning(f"[WS] user_id={user_id} 异常: {e}")
    finally:
        ws_manager.disconnect(user_id, ws)
        try:
            await ws.close()
        except Exception:
            pass
