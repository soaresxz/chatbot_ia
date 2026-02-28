from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import SessionLocal, create_tables
from app.api.v1.webhook import router as webhook_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.send_message import router as send_router
from app.api.v1.human_send import router as human_send_router
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.websocket_manager import active_connections, broadcast

# Import do Tenant para o startup
from app.models.tenant import Tenant

# Sistema de conexões WebSocket (para Lovable)

app = FastAPI(
    title="OdontoIA SaaS",
    description="Agente IA WhatsApp para Clínicas Odontológicas",
    version="1.0"
)

# CORS - essencial para Lovable funcionar
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================== LOGGER GLOBAL DE DEBUG (para Lovable) ==================


class DebugRequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        print(f"\n🔍 [REQUEST] {request.method} {request.url.path} | IP: {request.client.host if request.client else 'unknown'}")
        
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    print(f"   📦 BODY: {body.decode('utf-8')[:600]}...")
            except:
                pass
                
        response = await call_next(request)
        print(f"   📤 RESPONSE: {response.status_code} {request.url.path}")
        return response

app.add_middleware(DebugRequestMiddleware)
# =========================================================================
# Rotas
app.include_router(webhook_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/dashboard")
app.include_router(send_router, prefix="/api")
app.include_router(human_send_router, prefix="/api")

# ==================== WEBSOCKET PARA LOVABLE ====================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    print(f"✅ WebSocket conectado: {websocket.client}")

    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.discard(websocket)
        print(f"❌ WebSocket desconectado: {websocket.client}")
    except Exception as e:
        print(f"Erro no WebSocket: {e}")
        active_connections.discard(websocket)

# ==================== STARTUP ====================
@app.on_event("startup")
async def startup_event():
    create_tables()
    
    db = SessionLocal()
    tenants = db.query(Tenant).all()
    for tenant in tenants:
        tenant.human_mode_active = False
        tenant.human_mode_until = None
    db.commit()
    db.close()
    
    print("✅ Sistema iniciado - Modo humano resetado para todos os tenants")
    print("✅ OdontoIA SaaS rodando normalmente!")

# Root
@app.get("/")
async def root():
    return {
        "status": "online",
        "websocket": "/ws",
        "dashboard": "/dashboard"
    }