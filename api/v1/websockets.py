"""
WebSocket Real-Time Event Subscriptions.
Provides real-time event feeds for department monitoring, incident rooms, pilot telemetry, and global dashboard.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.events import event_manager

router = APIRouter(tags=["WebSockets"])


@router.websocket("/ws/department/{department_id}")
async def department_websocket(websocket: WebSocket, department_id: str):
    """Real-time event stream for authorized department personnel."""
    room = f"department_{department_id}"
    await event_manager.connect(websocket, room)
    try:
        while True:
            # Keep connection alive; can receive client heartbeats
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        event_manager.disconnect(websocket, room)


@router.websocket("/ws/incidents/{incident_id}")
async def incident_websocket(websocket: WebSocket, incident_id: str):
    """Real-time event stream for a specific emergency incident."""
    room = f"incident_{incident_id}"
    await event_manager.connect(websocket, room)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        event_manager.disconnect(websocket, room)


@router.websocket("/ws/pilot/{pilot_id}")
async def pilot_websocket(websocket: WebSocket, pilot_id: str):
    """Real-time telemetry and job card dispatch stream for drone pilots."""
    room = f"pilot_{pilot_id}"
    await event_manager.connect(websocket, room)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        event_manager.disconnect(websocket, room)


@router.websocket("/ws/dashboard")
async def global_dashboard_websocket(websocket: WebSocket):
    """Global emergency live feed stream for master incident overview."""
    room = "global_dashboard"
    await event_manager.connect(websocket, room)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        event_manager.disconnect(websocket, room)
