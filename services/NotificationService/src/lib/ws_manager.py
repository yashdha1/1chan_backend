import json
from collections import defaultdict

from fastapi import WebSocket


class NotificationConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, ws: WebSocket, user_id: str) -> None:
        await ws.accept()
        self._connections[user_id].append(ws)

    def disconnect(self, ws: WebSocket, user_id: str) -> None:
        conns = self._connections.get(user_id)
        if not conns:
            return
        if ws in conns:
            conns.remove(ws)
        if not conns:
            del self._connections[user_id]

    async def broadcast_to_user(self, user_id: str, payload: dict) -> None:
        conns = list(self._connections.get(user_id, []))
        if not conns:
            return

        dead: list[WebSocket] = []
        data = json.dumps(payload, default=str)
        for ws in conns:
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect(ws, user_id)


notification_ws_manager = NotificationConnectionManager()
