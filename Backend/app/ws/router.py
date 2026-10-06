import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["websocket"])

active_connections: set[WebSocket] = set()

@router.websocket("/ws/online")
async def websocket_online(websocket: WebSocket):
    """
    在线访客实时 WebSocket 广播端点，复刻旧系统 /ws/online 协议。
    前端期望接收纯数字文本作为在线人数，收到 ping 返回 pong。
    """
    await websocket.accept()
    active_connections.add(websocket)
    try:
        # 立即推送当前在线连接数
        await websocket.send_text(str(max(1, len(active_connections))))
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            else:
                await websocket.send_text(str(max(1, len(active_connections))))
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        active_connections.discard(websocket)
