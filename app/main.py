from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.core.database import SessionLocal, create_tables
from app.api.v1.webhook import router as webhook_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.send_message import router as send_router
from app.models.tenant import Tenant 
from app.api.v1.human_send import router as human_send_router


# ← Novo

app = FastAPI(
    title="OdontoIA SaaS",
    description="Agente IA WhatsApp para Clínicas Odontológicas",
    version="1.0"
)

# ==================== CORS (essencial para Lovable) ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== ROTAS ====================
app.include_router(webhook_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/dashboard")
app.include_router(send_router, prefix="/api")   # ← Rota para a atendente enviar mensagem
app.include_router(human_send_router, prefix="/api")

# ==================== WEBSOCKET (real-time para Lovable) ====================
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"✅ Recebido: {data}")
    except WebSocketDisconnect:
        print("WebSocket desconectado")

# ==================== STARTUP ====================
@app.on_event("startup")
async def startup_event():
    create_tables()
    
    # Reset automático do modo humano ao iniciar o servidor
    db = SessionLocal()
    tenants = db.query(Tenant).all()
    for tenant in tenants:
        tenant.human_mode_active = False
        tenant.human_mode_until = None
    db.commit()
    db.close()
    
    print("✅ Sistema iniciado - Modo humano resetado para todos os tenants")
    print("✅ OdontoIA SaaS rodando normalmente!")

# ==================== ROOT ====================
@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "OdontoIA SaaS rodando 🚀",
        "webhook": "/api/v1/twilio/webhook",
        "dashboard": "/dashboard",
        "websocket": "/ws/chat"
    }
    