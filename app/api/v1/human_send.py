from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.message_log import MessageLog
from app.models.tenant import Tenant
from app.core.websocket_manager import broadcast
from app.services.whatsapp.twilio_provider import TwilioProvider
from uuid import uuid4
from datetime import datetime
import logging
from app.core.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


def normalize_phone(phone: str) -> str:
    clean = phone.replace("whatsapp:", "").replace(" ", "").strip()
    if clean and not clean.startswith("+"):
        clean = "+" + clean
    return clean


@router.post("/human-send")
async def human_send(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON inválido")

    phone = (
        data.get("patient_phone") or
        data.get("patientPhone") or
        data.get("phone") or
        data.get("to")
    )
    message = data.get("message") or data.get("text") or data.get("body")
    tenant_id = data.get("tenant_id") or data.get("tenantId")

    if not phone or not message:
        raise HTTPException(status_code=422, detail="patient_phone e message são obrigatórios")
    if not tenant_id:
        raise HTTPException(status_code=422, detail="tenant_id é obrigatório")

    # ✅ Busca o tenant para obter o número da clínica como from_phone
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Clínica não encontrada")

    phone_clean = normalize_phone(phone)        # ✅ número do paciente normalizado
    clinic_phone = normalize_phone(tenant.whatsapp_number)  # ✅ número da clínica como remetente

    logger.info(f"[HUMANO SEND] tenant={tenant_id} phone={phone_clean} msg={message[:80]}")

    # Salva no banco com phones normalizados
    log = MessageLog(
        id=str(uuid4()),
        tenant_id=tenant_id,
        from_phone=clinic_phone,   # ✅ número real da clínica, não "humano"
        to_phone=phone_clean,      # ✅ normalizado
        message=message,
        direction="out",
        created_at=datetime.utcnow()
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    # Envia via Twilio
    try:
        provider = TwilioProvider()
        sid = await provider.send_message(f"whatsapp:{phone_clean}", message)
    except Exception as e:
        logger.error(f"[HUMANO SEND] Erro Twilio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # Broadcast em tempo real
    await broadcast({
        "type": "new_message",
        "tenant_id": tenant_id,
        "patient_phone": phone_clean,
        "message": {
            "id": log.id,
            "content": message,
            "direction": "out",
            "timestamp": log.created_at.isoformat(),
            "sender_name": "Atendente",
        }
    })

    logger.info(f"[HUMANO SEND] ✅ Enviado! SID: {sid}")
    return {"status": "success", "sid": sid}