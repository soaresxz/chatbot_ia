from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.message_log import MessageLog
from app.core.websocket_manager import broadcast
from app.services.whatsapp.twilio_provider import TwilioProvider
from uuid import uuid4
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/human-send")
async def human_send(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON inválido")

    # ✅ FIX 1: aceita patient_phone (snake_case que o frontend manda)
    phone = (
        data.get("patient_phone") or
        data.get("patientPhone") or
        data.get("phone") or
        data.get("to")
    )
    message = data.get("message") or data.get("text") or data.get("body")

    # ✅ FIX 2: tenant_id vem do request
    tenant_id = data.get("tenant_id") or data.get("tenantId")

    if not phone or not message:
        raise HTTPException(status_code=422, detail="patient_phone e message são obrigatórios")
    if not tenant_id:
        raise HTTPException(status_code=422, detail="tenant_id é obrigatório")

    logger.info(f"[HUMANO SEND] tenant={tenant_id} phone={phone} msg={message[:80]}")

    # Normaliza o número
    phone_clean = phone.replace("whatsapp:", "").replace(" ", "").strip()
    if not phone_clean.startswith("+"):
        phone_clean = "+" + phone_clean
    full_to = f"whatsapp:{phone_clean}"

    # Salva no banco
    log = MessageLog(
        id=str(uuid4()),
        tenant_id=tenant_id,
        from_phone="humano",
        to_phone=phone_clean,
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
        sid = await provider.send_message(full_to, message)
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