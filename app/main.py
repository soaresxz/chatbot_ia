from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# ================== IMPORTS DO PROJETO ==================
from app.core.database import create_tables
from app.api.v1.webhook import router as webhook_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.send_message import router as send_router
from app.api.v1.human_send import router as human_send_router
from app.core.websocket_manager import active_connections
from app.services.ai.gemini_agent import get_ai_response
from sqlalchemy.orm import Session
from app.core.database import get_db

# ================== APP FASTAPI ==================
app = FastAPI(
    title="OdontoIA SaaS",
    description="Agente IA WhatsApp para Clínicas Odontológicas",
    version="1.0"
)

# ================== CORS (essencial para Lovable) ==================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================== MIDDLEWARE DE DEBUG (para você ver tudo no Railway) ==================
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

# ================== ROTAS ==================
app.include_router(webhook_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/dashboard")
app.include_router(send_router, prefix="/api")
app.include_router(human_send_router, prefix="/api")

# ================== WEBSOCKET PARA LOVABLE ==================
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

# ================== STARTUP (SÍNCRONO - compatível com database.py atual) ==================
@app.on_event("startup")
def startup_event():
    create_tables()                      # ← síncrono (sem await)
    print("🚀 Chatbot iniciado com PostgreSQL (síncrono)!")
    
@app.get("/setup-tenant")
def setup_tenant(db: Session = Depends(get_db)):
    from app.models.tenant import Tenant
    import traceback

    try:
        sandbox_number = "+14155238886"

        # Verifica se já existe
        existing = db.query(Tenant).filter(
            Tenant.whatsapp_number.ilike(f"%{sandbox_number}%")
        ).first()

        if existing:
            print(f"✅ Tenant já existe: ID={existing.id} | Nome={existing.name}")
            return {
                "status": "already_exists",
                "id": existing.id,
                "name": existing.name,
                "whatsapp_number": existing.whatsapp_number
            }

        # Cria tenant com TODOS os campos obrigatórios
        new_tenant = Tenant(
            id="sandbox_twilio",                    # ← obrigatório (primary key)
            name="Twilio Sandbox Test",             # ← obrigatório
            dentist_name="Dr. Teste Sandbox",       # ← obrigatório
            whatsapp_number=sandbox_number,         # ← obrigatório
            human_mode_active=False,
            plan="basic",
            is_active=True,
            attendant_phone="+557981171862"         # seu número (opcional)
        )

        db.add(new_tenant)
        db.commit()
        db.refresh(new_tenant)

        print(f"🎉 Tenant criado com sucesso! ID = {new_tenant.id}")
        return {
            "status": "created",
            "id": new_tenant.id,
            "name": new_tenant.name,
            "whatsapp_number": new_tenant.whatsapp_number
        }

    except Exception as e:
        print(f"❌ ERRO AO CRIAR TENANT: {e}")
        traceback.print_exc()   # ← mostra o erro completo no log do Railway
        return {"status": "error", "message": str(e)}
    
# ================== ROOT ==================
@app.get("/")
async def root():
    return {
        "status": "online",
        "websocket": "/ws",
        "dashboard": "/dashboard"
    }