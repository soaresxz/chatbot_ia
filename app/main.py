from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import os

from app.core.database import create_tables
from app.api.v1.webhook import router as webhook_router
from app.api.v1.send_message import router as send_router
from app.api.v1.human_send import router as human_send_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.routers.dashboard import router as dashboard_router
from app.api.v1.reports import router as reports_router
from app.core.websocket_manager import active_connections
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

class SimpleRequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        print(f"[REQUEST] {request.method} {request.url.path}")
        response = await call_next(request)
        print(f"[RESPONSE] {response.status_code} {request.url.path}")
        return response

app.add_middleware(SimpleRequestMiddleware)

# ================== CHAVE ADMIN ==================
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
if not ADMIN_API_KEY:
    raise RuntimeError("ADMIN_API_KEY não configurada no Railway!")

def verify_admin_key(api_key: str = Query(None, alias="api_key")):
    if not api_key or api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Chave de admin inválida")
    return True

# ================== ADMIN ==================

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


# FIX 1: campos renomeados para bater com o frontend (name, dentist_name, whatsapp_number, plan, is_active)
@app.get("/admin/tenants")
def list_tenants(api_key: bool = Depends(verify_admin_key), db=Depends(get_db)):
    from app.models.tenant import Tenant
    tenants = db.query(Tenant).all()
    return {
        "total": len(tenants),
        "tenants": [{
            "id": t.id,
            "name": t.name,
            "dentist_name": t.dentist_name,
            "whatsapp_number": t.whatsapp_number,
            "plan": t.plan,
            "is_active": t.is_active
        } for t in tenants]
    }

# ================== ROUTERS ==================
app.include_router(webhook_router, prefix="/api/v1")
app.include_router(send_router, prefix="/api")
app.include_router(human_send_router, prefix="/api")
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(dashboard_router)
app.include_router(reports_router)

# ================== WEBSOCKET ==================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.discard(websocket)

# ================== STARTUP ==================
@app.on_event("startup")
def startup_event():
    create_tables()
    print("🚀 OdontoIA SaaS iniciado com sucesso!")

# ================== DASHBOARD ==================
@app.get("/dashboard/clinica/{tenant_id}")
async def get_clinica_dashboard(tenant_id: str, db=Depends(get_db)):
    from app.services.dashboard_service import DashboardService
    try:
        metrics = await DashboardService.get_clinica_dashboard(db, tenant_id)
        return {"metrics": metrics, "tenant_id": tenant_id}
    except Exception as e:
        print(f"❌ ERRO DASHBOARD: {str(e)}")
        return {"error": str(e)}

@app.get("/dashboard/conversations")
def get_dashboard_conversations(db=Depends(get_db)):
    from app.models.message_log import MessageLog
    from datetime import datetime

    tenant_id = "sandbox_twilio"
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

# ================== RELATÓRIOS ==================
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

    return {
        "periodo": inicio_mes.strftime("%B %Y"),
        "total_agendamentos": total_mes,
        "taxa_confirmacao": round((confirmados_mes / total_mes * 100), 1) if total_mes > 0 else 0.0,
        "faturamento_mes": 0.0
    }

# ================== PACIENTES ==================
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

# ================== CONVERSAS ==================

# FIX 2: retorna campos corretos para o frontend e respeita o tenant_id real
@app.get("/api/v1/conversations")
def get_conversations(
    tenant_id: str = Query(None),
    api_key: str = Query(None, alias="api_key"),
    db=Depends(get_db)
):
    if api_key != ADMIN_API_KEY:
        raise HTTPException(403, "Chave inválida")

    # Usa sandbox_twilio como fallback se não tiver tenant_id
    effective_tenant = tenant_id or "sandbox_twilio"

    from app.models.message_log import MessageLog
    from sqlalchemy import func

    # Busca todos os telefones únicos que conversaram com esse tenant
    phones = db.query(MessageLog.from_phone)\
        .filter(MessageLog.tenant_id == effective_tenant)\
        .distinct().all()

    conversations = []
    for (phone,) in phones:
        if not phone:
            continue

        # Última mensagem desta conversa
        last_msg = db.query(MessageLog)\
            .filter(
                MessageLog.tenant_id == effective_tenant,
                MessageLog.from_phone == phone
            )\
            .order_by(MessageLog.created_at.desc())\
            .first()

        if not last_msg:
            continue

        # Verifica se está em modo humano
        from app.models.tenant import Tenant
        tenant = db.query(Tenant).filter(Tenant.id == effective_tenant).first()
        is_human = getattr(tenant, 'human_mode_active', False)

        conversations.append({
            "id": phone,
            "patient_name": f"Paciente {phone[-4:]}",
            "patient_phone": phone,
            "last_message": last_msg.message or "",
            "last_message_time": last_msg.created_at.isoformat(),
            "updated_at": last_msg.created_at.isoformat(),
            "status": "human_mode" if is_human else "ai_mode",
            "unread_count": 0
        })

    return {"conversations": conversations, "total": len(conversations)}


@app.get("/api/v1/conversations/{patient_phone}")
def get_conversation_messages(
    patient_phone: str,
    tenant_id: str = Query(None),
    api_key: str = Query(None, alias="api_key"),
    db=Depends(get_db)
):
    if api_key != ADMIN_API_KEY:
        raise HTTPException(403, "Chave inválida")

    effective_tenant = tenant_id or "sandbox_twilio"

    from app.models.message_log import MessageLog

    messages = db.query(MessageLog)\
        .filter(
            MessageLog.tenant_id == effective_tenant,
            MessageLog.from_phone == patient_phone
        )\
        .order_by(MessageLog.created_at.asc())\
        .all()

    return {
        "messages": [{
            "id": str(m.id),
            "content": m.message or "",
            "direction": "in" if getattr(m, 'from_user', True) else "out",
            "timestamp": m.created_at.isoformat(),
            "sender_name": None
        } for m in messages]
    }


@app.post("/api/v1/conversations/assume")
def assume_conversation(
    tenant_id: str = Query(...),
    api_key: str = Query(None, alias="api_key"),
    body: dict = None,
    db=Depends(get_db)
):
    if api_key != ADMIN_API_KEY:
        raise HTTPException(403, "Chave inválida")

    from app.models.tenant import Tenant
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(404, "Clínica não encontrada")

    tenant.human_mode_active = True
    db.commit()
    return {"status": "success", "mode": "human_mode"}


# FIX 3: endpoint /release criado
@app.post("/api/v1/conversations/release")
def release_conversation(
    tenant_id: str = Query(...),
    api_key: str = Query(None, alias="api_key"),
    body: dict = None,
    db=Depends(get_db)
):
    if api_key != ADMIN_API_KEY:
        raise HTTPException(403, "Chave inválida")

    from app.models.tenant import Tenant
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(404, "Clínica não encontrada")

    tenant.human_mode_active = False
    db.commit()
    return {"status": "success", "mode": "ai_mode"}


# ================== ROOT ==================
@app.get("/")
async def root():
    return {"status": "online", "version": "1.0", "saas": "multi-clínica"}