from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.database import create_tables
from app.api.v1.webhook import router as webhook_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.send_message import router as send_router
from app.api.v1.human_send import router as human_send_router
from app.core.websocket_manager import active_connections

app = FastAPI(
    title="OdontoIA SaaS",
    description="Agente IA WhatsApp para Clínicas Odontológicas",
    version="1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de debug leve (pode remover depois se quiser)
class DebugRequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        print(f"[REQUEST] {request.method} {request.url.path}")
        response = await call_next(request)
        print(f"[RESPONSE] {response.status_code} {request.url.path}")
        return response

app.add_middleware(DebugRequestMiddleware)

# Rotas
app.include_router(webhook_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/dashboard")
app.include_router(send_router, prefix="/api")
app.include_router(human_send_router, prefix="/api")

# WebSocket para Lovable
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.discard(websocket)

# Startup
@app.on_event("startup")
def startup_event():
    create_tables()
    print("🚀 OdontoIA SaaS iniciado com sucesso!")

# Root
@app.get("/")
async def root():
    return {
        "status": "online",
        "version": "1.0",
        "message": "Chatbot OdontoIA rodando"
    }