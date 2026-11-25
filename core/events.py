"""
WebSocket Real-Time Event Broadcasting Manager.
Distributes emergency events to authorized departments, incident rooms, and drone pilots.
"""
import json
import logging
from typing import Any, Dict, List, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # Room identifier -> Set of WebSockets
        self.rooms: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str) -> None:
        await websocket.accept()
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(websocket)
        logger.debug("WebSocket client joined room: %s", room)

    def disconnect(self, websocket: WebSocket, room: str) -> None:
        if room in self.rooms and websocket in self.rooms[room]:
            self.rooms[room].remove(websocket)
            if not self.rooms[room]:
                del self.rooms[room]
        logger.debug("WebSocket client disconnected from room: %s", room)

    async def broadcast_to_room(self, room: str, event_type: str, payload: Dict[str, Any]) -> None:
        if room not in self.rooms:
            return
        message = json.dumps({"event": event_type, "data": payload}, default=str)
        dead_sockets: List[WebSocket] = []
        for socket in list(self.rooms[room]):
            try:
                await socket.send_text(message)
            except Exception as e:
                logger.warning("Error broadcasting WebSocket to room %s: %s", room, str(e))
                dead_sockets.append(socket)
        for dead in dead_sockets:
            self.disconnect(dead, room)

    async def broadcast_global(self, event_type: str, payload: Dict[str, Any]) -> None:
        await self.broadcast_to_room("global_dashboard", event_type, payload)

    async def broadcast_department(self, department_id: str, event_type: str, payload: Dict[str, Any]) -> None:
        await self.broadcast_to_room(f"department_{department_id}", event_type, payload)
        await self.broadcast_global(event_type, payload)

    async def broadcast_incident(self, incident_id: str, event_type: str, payload: Dict[str, Any]) -> None:
        await self.broadcast_to_room(f"incident_{incident_id}", event_type, payload)
        await self.broadcast_global(event_type, payload)

    async def broadcast_pilot(self, pilot_id: str, event_type: str, payload: Dict[str, Any]) -> None:
        await self.broadcast_to_room(f"pilot_{pilot_id}", event_type, payload)


event_manager = ConnectionManager()
