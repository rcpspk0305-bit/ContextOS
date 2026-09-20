import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from contextos.runtime.event_bus import event_bus
from contextos.models.event import EventEnvelope

router = APIRouter()

class WebSocketConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_event(self, event: EventEnvelope):
        data = event.model_dump_json()
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception:
                disconnected.append(connection)

        for dead in disconnected:
            self.disconnect(dead)

manager = WebSocketConnectionManager()

# Hook manager into event_bus so every emitted event is sent over WebSocket
event_bus.subscribe(lambda event: asyncio.create_task(manager.broadcast_event(event)))

@router.websocket("/api/events/ws")
async def websocket_events_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep socket alive and accept ping/pong or client commands
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
