"""WebSocket route — clients subscribe to channels."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws.manager import ws_manager

router = APIRouter()


@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket, channels: str = "news,reports"):
    """`channels` is a comma-separated list — currently informational only,
    fan-out broadcasts to all subscribers and the client filters."""
    await ws_manager.connect(ws)
    try:
        # send hello
        await ws.send_json({"type": "hello", "data": {"channels": channels.split(",")}})
        while True:
            # we only push; ignore client messages but keep the socket alive
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
