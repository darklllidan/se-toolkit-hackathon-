from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.dependencies import get_current_user
from app.services.ws_manager import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/dashboard")
async def dashboard_ws(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    WebSocket endpoint for real-time dashboard updates.
    JWT token is passed as a query parameter because browsers cannot set
    Authorization headers in WebSocket handshakes.
    """
    # Validate token before accepting the connection
    from app.database import AsyncSessionLocal
    from app.dependencies import _resolve_token

    async with AsyncSessionLocal() as db:
        try:
            await _resolve_token(token, db)
        except Exception:
            await websocket.accept()
            await websocket.close(code=4001)
            return

    await manager.connect(websocket)
    try:
        while True:
            # Keep-alive: discard any client messages (pings)
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
