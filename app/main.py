from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.database import create_tables
from app.api.v1.webhook import router as webhook_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.send_message import router as send_router
from app.api.v1.human_send import router as human_send_router
from app.core.websocket_manager import active_connections
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.tenant import Tenant
from fastapi import Depends              # ← adicione esta linha



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
    
# ================== ATIVAR PREMIUM (temporário) ==================
@app.get("/set-premium")
def set_premium(db: Session = Depends(get_db)):
    from app.models.tenant import Tenant
    from sqlalchemy import update

    tenant = db.query(Tenant).filter(Tenant.id == "sandbox_twilio").first()
    if not tenant:
        return {"status": "error", "message": "Tenant não encontrado"}

    tenant.plan = "premium"
    db.commit()
    db.refresh(tenant)

    return {
        "status": "success",
        "message": "Plano PREMIUM ativado com sucesso!",
        "tenant_id": tenant.id,
        "plan": tenant.plan
    }
    
@app.post("/admin/create-tenant")
def create_tenant(
    name: str,
    dentist_name: str,
    whatsapp_number: str,   # ex: "+5511999999999"
    plan: str = "basic",
    db: Session = Depends(get_db)
):
    from app.models.tenant import Tenant

    # Verifica se número já existe
    existing = db.query(Tenant).filter(Tenant.whatsapp_number == whatsapp_number).first()
    if existing:
        return {"status": "error", "message": "Número WhatsApp já cadastrado"}

    new_tenant = Tenant(
        id=f"clinica_{name.lower().replace(' ', '_')}",   # ex: clinica_odonto_sorriso
        name=name,
        dentist_name=dentist_name,
        whatsapp_number=whatsapp_number,
        plan=plan,
        is_active=True,
        attendant_phone=""   # pode preencher depois
    )

    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)

    return {
        "status": "success",
        "message": f"Clínica '{name}' criada com sucesso!",
        "tenant_id": new_tenant.id,
        "whatsapp_number": new_tenant.whatsapp_number,
        "plan": new_tenant.plan
    }

# Root
@app.get("/")
async def root():
    return {
        "status": "online",
        "version": "1.0",
        "message": "Chatbot OdontoIA rodando"
    }