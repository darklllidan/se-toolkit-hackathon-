import asyncio
import json

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self._active: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._active.add(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._active.discard(ws)

    async def broadcast(self, payload: dict) -> None:
        message = json.dumps(payload, default=str)
        dead: set[WebSocket] = set()
        async with self._lock:
            targets = set(self._active)
        for ws in targets:
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        if dead:
            async with self._lock:
                self._active -= dead


manager = ConnectionManager()
