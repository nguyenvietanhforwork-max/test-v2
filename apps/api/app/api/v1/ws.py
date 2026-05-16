"""WebSocket /ws/stream — real-time pipeline + news event broadcast.

Auth: ?token=<jwt> on the upgrade request.
Server → client: typed JSON events (see docs/api.md §8).
"""

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.logging import log
from app.core.security import decode_token
from app.events.bus import event_bus

ws_router = APIRouter()


@ws_router.websocket("/ws/stream")
async def stream(ws: WebSocket, token: str = Query(default="")) -> None:
    try:
        payload = decode_token(token)
    except Exception as e:
        await ws.close(code=4401, reason=f"unauthorized: {e}")
        return

    user_id = payload.get("sub", "anon")
    await ws.accept()
    log.info("ws.connected", user_id=user_id)

    queue = await event_bus.subscribe(f"events:user:{user_id}", "events:global")
    try:
        while True:
            msg = await queue.get()
            await ws.send_json(msg)
    except WebSocketDisconnect:
        log.info("ws.disconnected", user_id=user_id)
    finally:
        await event_bus.unsubscribe(queue)
