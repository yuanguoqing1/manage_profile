"""WebSocket 路由。"""

from __future__ import annotations

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

        await ws_manager.connect(user.id, ws)
        try:
            while True:
                await ws.receive_text()
        except WebSocketDisconnect:
            ws_manager.disconnect(user.id, ws)
        except Exception:  # noqa: BLE001
            ws_manager.disconnect(user.id, ws)
            try:
                await ws.close(code=1011)
            except Exception:  # noqa: BLE001
                pass
