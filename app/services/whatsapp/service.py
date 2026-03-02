import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.tenant import Tenant
from app.models.message_log import MessageLog
from app.models.conversation_status import ConversationStatus
from app.services.whatsapp.twilio_provider import TwilioProvider
from app.services.intent_matcher import get_quick_response
from app.services.basic_bot import handle_basic_plan
from app.services.ai.gemini_agent import get_ai_response
from app.core.websocket_manager import broadcast

FALLBACK_MESSAGE = "Aguarde um momento. Uma atendente vai te responder em breve. 😊"

async def process_incoming_message(from_number: str, body: str, to_number: str):
    db: Session = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(
            Tenant.whatsapp_number.ilike(f"%{to_number.replace('whatsapp:', '').replace('+', '').strip()}%")
        ).first()

        if not tenant:
            print(f"⚠️ Nenhum tenant encontrado para o número: {to_number}")
            return

        # ✅ FIX 2: para o bot se human_mode_active=True, independente de human_mode_until
        status = db.query(ConversationStatus).filter(
            ConversationStatus.tenant_id == tenant.id,
            ConversationStatus.patient_phone == from_number,
            ConversationStatus.human_mode_active == True
        ).first()

        if status:
            # Se tem prazo, verifica se ainda está dentro do prazo
            if status.human_mode_until is None or datetime.utcnow() < status.human_mode_until:
                print(f"🙋 Modo humano ativo para {from_number}, bot pausado.")
                return

        # ✅ FIX 1: salva o timestamp antes do commit para evitar KeyError após expiração
        now_in = datetime.utcnow()
        log_in = MessageLog(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            from_phone=from_number,
            to_phone=to_number,
            message=body,
            direction="in",
            created_at=now_in
        )
        db.add(log_in)
        db.commit()

        await broadcast({
            "type": "new_message",
            "tenant_id": tenant.id,
            "patient_phone": from_number,
            "message": {
                "id": log_in.id,
                "content": body,
                "direction": "in",
                "timestamp": now_in.isoformat(),
                "sender_name": None,
            }
        })

        # Gera resposta conforme plano
        if tenant.plan == "basic":
            response_text = await handle_basic_plan(body, from_number, tenant)
        else:
            quick = get_quick_response(body, tenant.name or "clínica")
            response_text = quick or await get_ai_response(body, tenant, from_number) or FALLBACK_MESSAGE

        # Envia resposta
        provider = TwilioProvider()
        await provider.send_message(from_number, response_text)

        # ✅ FIX 1: mesmo padrão para log de saída
        now_out = datetime.utcnow()
        log_out = MessageLog(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            from_phone=to_number,
            to_phone=from_number,
            message=response_text,
            direction="out",
            created_at=now_out
        )
        db.add(log_out)
        db.commit()

        await broadcast({
            "type": "new_message",
            "tenant_id": tenant.id,
            "patient_phone": from_number,
            "message": {
                "id": log_out.id,
                "content": response_text,
                "direction": "out",
                "timestamp": now_out.isoformat(),
                "sender_name": "Bot",
            }
        })

        print(f"✅ Resposta enviada para {from_number}")

    finally:
        db.close()