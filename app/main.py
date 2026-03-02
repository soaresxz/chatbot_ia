from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import os

from app.core.database import create_tables
from app.api.v1.webhook import router as webhook_router
from app.api.v1.send_message import router as send_router
from app.api.v1.human_send import router as human_send_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.routers.dashboard import router as dashboard_router   # ← caminho correto
from app.api.v1.reports import router as reports_router
from app.core.websocket_manager import active_connections
from app.core.tenant import TenantMiddleware
from app.core.database import get_db
from pydantic import BaseModel

app = FastAPI(
    title="OdontoIA SaaS",
    description="Plataforma multi-clínica de chatbot WhatsApp para odontologia",
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

# Middleware simples de log (útil em produção)
class SimpleRequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        print(f"[REQUEST] {request.method} {request.url.path}")
        response = await call_next(request)
        print(f"[RESPONSE] {response.status_code} {request.url.path}")
        return response

app.add_middleware(SimpleRequestMiddleware)

# ================== CHAVE ADMIN (SaaS) ==================
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
if not ADMIN_API_KEY:
    raise RuntimeError("ADMIN_API_KEY não configurada no Railway!")

def verify_admin_key(api_key: str = Query(None, alias="api_key")):
    if not api_key or api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Chave de admin inválida")
    return True

# ================== ROTAS ANTIGAS DO ADMIN (mantidas funcionando) ==================
@app.get("/admin/create-tenant")
def create_tenant(
    name: str = Query(...),
    dentist_name: str = Query(...),
    whatsapp_number: str = Query(...),
    plan: str = Query("basic"),
    api_key: bool = Depends(verify_admin_key),
    db=Depends(get_db)
):
    from app.models.tenant import Tenant
    if db.query(Tenant).filter(Tenant.whatsapp_number == whatsapp_number).first():
        raise HTTPException(400, "Número de WhatsApp já cadastrado")

    new_tenant = Tenant(
        id=f"clinica_{name.lower().replace(' ', '_').replace('ã','a').replace('ç','c')}",
        name=name,
        dentist_name=dentist_name,
        whatsapp_number=whatsapp_number,
        plan=plan,
        is_active=True,
        human_mode_active=False
    )
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)
    return {"status": "success", "tenant_id": new_tenant.id}

@app.get("/admin/tenants")
def list_tenants(api_key: bool = Depends(verify_admin_key), db=Depends(get_db)):
    from app.models.tenant import Tenant
    tenants = db.query(Tenant).all()
    return {
        "total": len(tenants),
        "clinicas": [{
            "id": t.id,
            "nome": t.name,
            "dentista": t.dentist_name,
            "whatsapp": t.whatsapp_number,
            "plano": t.plan,
            "ativo": t.is_active
        } for t in tenants]
    }

# ================== ROTAS NOVAS (production-ready) ==================
app.include_router(webhook_router, prefix="/api/v1")
app.include_router(send_router, prefix="/api")
app.include_router(human_send_router, prefix="/api")
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(dashboard_router)           # ← sem prefixo extra (já vem com /dashboard no router)
app.include_router(reports_router)


# WebSocket
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
    
@app.get("/dashboard/clinica/{tenant_id}")
async def get_clinica_dashboard(tenant_id: str, db=Depends(get_db)):
    from app.services.dashboard_service import DashboardService
    try:
        metrics = await DashboardService.get_clinica_dashboard(db, tenant_id)
        return {"metrics": metrics, "tenant_id": tenant_id}
    except Exception as e:
        print(f"❌ ERRO DASHBOARD: {str(e)}")
        return {"error": str(e)}

# === ROTA DE RELATÓRIOS DIRETA (para produção real) ===
@app.get("/reports/clinica/{tenant_id}")
def get_clinica_report(tenant_id: str, db=Depends(get_db)):
    from sqlalchemy import select, func, and_
    from datetime import datetime
    from app.models.appointment import Appointment

    hoje = datetime.utcnow().date()
    inicio_mes = hoje.replace(day=1)

    total_mes = db.scalar(
        select(func.count()).where(
            and_(
                Appointment.tenant_id == tenant_id,
                Appointment.scheduled_date >= inicio_mes
            )
        )
    ) or 0

    confirmados_mes = db.scalar(
        select(func.count()).where(
            and_(
                Appointment.tenant_id == tenant_id,
                Appointment.scheduled_date >= inicio_mes,
                Appointment.status == "confirmed"
            )
        )
    ) or 0

    faturamento_mes = 0.0  # coluna value ainda não existe

    return {
        "periodo": inicio_mes.strftime("%B %Y"),
        "total_agendamentos": total_mes,
        "taxa_confirmacao": round((confirmados_mes / total_mes * 100), 1) if total_mes > 0 else 0.0,
        "faturamento_mes": round(float(faturamento_mes), 2)
    }

# ================== PACIENTES (para demo do vídeo) ==================
class CreatePatient(BaseModel):
    nome: str
    telefone: str

@app.get("/clinica/{tenant_id}/pacientes")
def list_patients(tenant_id: str, db=Depends(get_db)):
    from app.models.patient import Patient
    patients = db.query(Patient).filter(Patient.tenant_id == tenant_id).all()
    return {
        "total": len(patients),
        "pacientes": [{
            "id": p.id,
            "nome": p.name,
            "telefone": p.phone,
            "criado_em": p.created_at.strftime("%d/%m/%Y %H:%M")
        } for p in patients]
    }

@app.post("/clinica/{tenant_id}/pacientes")
def create_patient(tenant_id: str, data: CreatePatient, db=Depends(get_db)):
    from app.models.patient import Patient
    new_patient = Patient(
        tenant_id=tenant_id,
        name=data.nome,
        phone=data.telefone
    )
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return {
        "status": "success", 
        "paciente_id": new_patient.id, 
        "nome": new_patient.name,
        "telefone": new_patient.phone
    }

@app.get("/dashboard/conversations")
def get_dashboard_conversations(db=Depends(get_db)):
    tenant_id = "sandbox_twilio"   # ← sandbox que você está usando para teste
    
    from app.models.message_log import MessageLog   # ajuste se o nome do seu modelo for diferente
    from datetime import datetime
    
    messages = db.query(MessageLog)\
        .filter(MessageLog.tenant_id == tenant_id)\
        .order_by(MessageLog.created_at.desc())\
        .limit(30).all()
    
    return {
        "conversas": [{
            "id": str(m.id),
            "paciente": "Cliente WhatsApp",
            "telefone": m.from_phone or "+14155238886",
            "mensagem": m.message,
            "data": m.created_at.strftime("%d/%m %H:%M"),
            "direcao": "recebida" if m.from_user else "enviada",
            "nao_lidas": 0
        } for m in messages]
    }

@app.get("/api/v1/conversations")
def get_conversations(
    tenant_id: str = Query(None),
    api_key: str = Query(None, alias="api_key"),
    db=Depends(get_db)
):
    if api_key != "senhaadminteste":
        raise HTTPException(403, "Chave inválida")
    
    if not tenant_id:
        tenant_id = "clinica_odonto_sorriso"
    
    from app.models.message_log import MessageLog
    
    messages = db.query(MessageLog)\
        .filter(MessageLog.tenant_id == tenant_id)\
        .order_by(MessageLog.created_at.desc())\
        .limit(50).all()
    
    return {
        "conversas": [
            {
                "id": str(m.id),
                "mensagem": m.message,
                "de": "paciente" if getattr(m, 'from_user', True) else "bot",
                "data": m.created_at.strftime("%d/%m %H:%M"),
                "telefone": getattr(m, 'from_phone', '+14155238886'),
                "nao_lidas": 0
            } for m in messages
        ]
    }

# Root
@app.get("/")
async def root():
    return {"status": "online", "version": "1.0", "saas": "multi-clínica"}