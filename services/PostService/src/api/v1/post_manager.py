import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from uuid import UUID

ws_router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.post_connections: dict[str, list[WebSocket]] = {}
        self.thread_connections: dict[str, list[WebSocket]] = {}


    async def connect_post(self, ws: WebSocket, post_id: str):
        await ws.accept()
        self.post_connections.setdefault(post_id, []).append(ws)

    def disconnect_post(self, ws: WebSocket, post_id: str):
        conns = self.post_connections.get(post_id)
        if not conns:
            return
        conns.remove(ws)
        if not conns:
            del self.post_connections[post_id]

    async def broadcast_post(self, post_id: str, payload: dict):
        for ws in self.post_connections.get(post_id, []):
            await ws.send_text(json.dumps(payload))

    def _thread_key(self, post_id: str, comment_id: str) -> str:
        return f"{post_id}:{comment_id}"

    async def connect_thread(self, ws: WebSocket, post_id: str, comment_id: str):
        await ws.accept()
        key = self._thread_key(post_id, comment_id)
        self.thread_connections.setdefault(key, []).append(ws)

    def disconnect_thread(self, ws: WebSocket, post_id: str, comment_id: str):
        key = self._thread_key(post_id, comment_id)
        conns = self.thread_connections.get(key)
        if not conns:
            return
        conns.remove(ws)
        if not conns:
            del self.thread_connections[key]

    async def broadcast_thread(self, post_id: str, comment_id: str, payload: dict):
        key = self._thread_key(post_id, comment_id)
        for ws in self.thread_connections.get(key, []):
            await ws.send_text(json.dumps(payload))


manager = ConnectionManager()


# when the post is viewed, clients job is to join the room. 
@ws_router.websocket("/ws/post/{post_id}")
async def ws_post(websocket: WebSocket, post_id: UUID):
    pid = str(post_id)
    await manager.connect_post(websocket, pid)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_post(websocket, pid)

@ws_router.websocket("/ws/post/{post_id}/thread/{comment_id}")
async def ws_thread(websocket: WebSocket, post_id: UUID, comment_id: UUID):
    pid, cid = str(post_id), str(comment_id)
    await manager.connect_thread(websocket, pid, cid)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_thread(websocket, pid, cid)