from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json

router = APIRouter()

# Store active connections per household
class ConnectionManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}

    async def connect(self, household_id: str, websocket: WebSocket):
        await websocket.accept()
        if household_id not in self.active:
            self.active[household_id] = []
        self.active[household_id].append(websocket)

    def disconnect(self, household_id: str, websocket: WebSocket):
        if household_id in self.active:
            self.active[household_id].remove(websocket)

    async def broadcast(self, household_id: str, data: dict):
        if household_id not in self.active:
            return
        dead = []
        for ws in self.active[household_id]:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active[household_id].remove(ws)


manager = ConnectionManager()


@router.websocket("/ws/readings/{household_id}")
async def websocket_readings(websocket: WebSocket, household_id: str):
    await manager.connect(household_id, websocket)
    try:
        while True:
            # Keep connection alive — ping every 20s
            await asyncio.sleep(20)
            await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        manager.disconnect(household_id, websocket)
