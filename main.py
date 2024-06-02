from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import redis
import json

# Renomear o aplicativo FastAPI
chat_app = FastAPI()

redis_conn = redis.Redis(host='localhost', port=6379, db=0)

template_engine = Jinja2Templates(directory="templates")

class WebSocketConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

ws_manager = WebSocketConnectionManager()

@chat_app.get("/")
async def load_chat_page(request: Request):
    return template_engine.TemplateResponse("chat.html", {"request": request})

@chat_app.websocket("/ws/{user}")
async def handle_websocket(websocket: WebSocket, user: str):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = {"username": user, "message": data}
            redis_conn.rpush("chat", json.dumps(message_data))
            await ws_manager.broadcast(json.dumps(message_data))
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
