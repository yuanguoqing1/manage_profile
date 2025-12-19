"""WebSocket 连接管理。"""

from __future__ import annotations

import logging
from typing import Dict, List, Set

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, user_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(user_id, set()).add(ws)
        logging.info("WS connect user_id=%s connections=%s", user_id, len(self._connections[user_id]))

    def disconnect(self, user_id: int, ws: WebSocket) -> None:
        conns = self._connections.get(user_id)
        if not conns:
            return
        conns.discard(ws)
        if not conns:
            self._connections.pop(user_id, None)
        logging.info("WS disconnect user_id=%s remain=%s", user_id, len(self._connections.get(user_id, [])))

    async def send_to(self, user_id: int, payload: dict) -> None:
        conns = list(self._connections.get(user_id, set()))
        if not conns:
            return
        dead: List[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_json(payload)
            except Exception:  # noqa: BLE001
                dead.append(ws)
        for ws in dead:
            self.disconnect(user_id, ws)

    def is_ws_online(self, user_id: int) -> bool:
        return user_id in self._connections and len(self._connections[user_id]) > 0


ws_manager = ConnectionManager()
