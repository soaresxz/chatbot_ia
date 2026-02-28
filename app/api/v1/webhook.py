from fastapi import APIRouter, Request
from app.services.whatsapp.service import process_incoming_message
from app.services.whatsapp.human_handler import handle_attendant_message
from app.core.database import SessionLocal
from app.models.tenant import Tenant
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/twilio/webhook")
async def twilio_webhook(request: Request):
    form = await request.form()
    
    from_number = form.get("From", "")          # quem enviou
    to_number   = form.get("To", "")            # para quem foi enviado
    body        = form.get("Body", "").strip()

    print(f"\n📨 WEBHOOK → From: {from_number} | To: {to_number} | Msg: {body}")

    db = SessionLocal()
    tenant = db.query(Tenant).filter(
        Tenant.whatsapp_number == to_number.replace("whatsapp:", "").replace("+", "").strip()
    ).first()
    db.close()

    if not tenant:
        return {"status": "ignored"}

    # ==================== MENSAGEM DA ATENDENTE PARA O PACIENTE ====================
    # Se o "From" for o número da clínica → é a atendente enviando para o paciente
    if from_number.replace("whatsapp:", "").replace("+", "") == tenant.whatsapp_number.replace("+", ""):
        # O "To" é o número do paciente
        patient_phone = to_number
        print(f"👩‍💼 ATENDENTE ENVIANDO PARA PACIENTE {patient_phone} → Ativando modo humano")
        await handle_attendant_message(tenant, patient_phone)
        return {"status": "human_takeover"}

    # ==================== MENSAGEM NORMAL DO PACIENTE ====================
    else:
        await process_incoming_message(from_number, body, to_number)
        return {"status": "processed"}